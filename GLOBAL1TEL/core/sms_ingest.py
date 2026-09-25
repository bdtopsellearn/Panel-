"""
The one place an incoming SMS turns into money.

Every inbound path funnels through ingest_sms():
  * the SMPP engine (carrier binds to us, or we bind to the carrier),
  * the HTTP webhook /api/smpp.php?action=receive,
  * the legacy Jasmin webhook /api/cdr.php?action=receive.

Keeping a single pipeline means an OTP is recorded, priced and credited
identically no matter how it arrived — which is exactly what went wrong
when each transport had its own copy of the logic.

Steps:
  1. raw log        -> smpp_cdr (always, even for unknown numbers)
  2. number lookup  -> sms_numbers + sms_ranges
  3. hierarchy      -> client / agent / manager
  4. pricing        -> the number's pay_term picks the range payout column
  5. billing CDR    -> sms_cdr
  6. balances       -> user_balances for each level
  7. notify         -> notifications + user_activity
"""
from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime

from core.db import Database
from core.helpers import (
    create_notification, log_activity, resolve_manager_id_for_user, sanitize,
    to_float, to_int,
)

logger = logging.getLogger("g1t.ingest")

PAYOUT_COLUMN = {
    "1/1": "payout_1_1",
    "7/1": "payout_7_1",
    "7/7": "payout_7_7",
    "30/45": "payout_30_45",
}

# Share of the number's payout kept by each upstream level. These match the
# percentages the PHP build used, so existing statements stay consistent.
AGENT_SHARE = 0.10
MANAGER_SHARE = 0.05

# Keywords that appear next to a numeric code in a real OTP SMS. "code" and
# "pin" were missing from the keyword side, so the single most common wording of
# all - "Your Google code is 483920" - was never flagged as an OTP.
_OTP_WORDS = (r"otp|code|pin|passcode|password|one[- ]?time|verification|verify|"
              r"confirmation|confirm|security|log\s*in|activation|auth(?:entication)?|"
              r"token|2fa")

OTP_PATTERN = re.compile(
    # keyword ... digits   e.g. "Your code is 483920", "OTP: 1234"
    rf"\b({_OTP_WORDS})\b[^\r\n]{{0,60}}?\b\d{{4,8}}\b"
    # digits ... keyword   e.g. "483920 is your verification code"
    rf"|\b\d{{4,8}}\b[^\r\n]{{0,60}}?\b({_OTP_WORDS})\b",
    re.IGNORECASE,
)


def detect_otp(message: str) -> int:
    """Classify the text without storing the code itself — only the flag is kept."""
    return 1 if message and OTP_PATTERN.search(message) else 0


def _normalise(number: str) -> str:
    """Carriers are inconsistent about the leading + and 00 prefix, so match on
    digits only. Without this, a real OTP arrives for '+959692514720' while the
    number is stored as '959692514720' and the message is silently dropped."""
    return re.sub(r"\D", "", str(number or ""))


def find_number(db: Database, destination: str):
    """Locate the destination number, tolerant of formatting differences."""
    digits = _normalise(destination)
    if not digits:
        return None

    sql = (
        "SELECT n.*, r.id as range_id, r.range_name, r.currency, r.test_number, "
        "r.payout_1_1, r.payout_7_1, r.payout_7_7, r.payout_30_45, "
        "n.pay_term, n.payout_rate "
        "FROM sms_numbers n JOIN sms_ranges r ON n.range_id = r.id "
    )

    row = db.query(sql + "WHERE n.number = ? LIMIT 1", [destination]).fetch()
    if row:
        return row
    row = db.query(sql + "WHERE n.number = ? LIMIT 1", [digits]).fetch()
    if row:
        return row
    # Last resort: compare only the trailing digits, which handles a country
    # code the carrier adds or drops.
    return db.query(
        sql + "WHERE REPLACE(REPLACE(n.number,'+',''),' ','') LIKE ? LIMIT 1",
        [f"%{digits[-9:]}"],
    ).fetch() if len(digits) >= 9 else None


def ingest_sms(source_addr: str, destination_addr: str, message: str,
               message_id: str = "", connector_id: str = "",
               submit_date=None) -> dict:
    """Record one inbound SMS. Returns a summary dict; never raises for an
    unknown number (the raw message is still logged so nothing is lost)."""
    db = Database.get_instance()

    message_id = sanitize(message_id) or f"sms_{uuid.uuid4().hex[:16]}"
    source_addr = sanitize(source_addr or "")
    destination_addr = sanitize(destination_addr or "")
    message = str(message or "")
    connector_id = sanitize(connector_id or "")
    submit_date = submit_date or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    if not source_addr or not destination_addr:
        return {"success": False, "error": "Missing source or destination"}

    # 0. Idempotency guard. A spool replay, a carrier that repeats a deliver_sm
    #    after a missed resp, or a webhook retry must not create a second CDR or
    #    credit a balance twice. Same message_id = same message.
    existing = db.query(
        "SELECT id, cdr_id FROM smpp_cdr WHERE message_id = ? LIMIT 1",
        [message_id]).fetch()
    if existing:
        logger.info("Duplicate inbound message_id %s ignored (already stored as "
                    "smpp_cdr %s)", message_id, existing["id"])
        return {"success": True, "duplicate": True,
                "assigned": bool(existing.get("cdr_id")),
                "smpp_cdr_id": existing["id"], "cdr_id": existing.get("cdr_id"),
                "message": "Already processed"}

    # 1. Always log the raw message first, so an unknown number is still visible
    #    in the SMPP CDR instead of vanishing.
    raw = db.query(
        "INSERT INTO smpp_cdr (message_id, source_addr, destination_addr, short_message, "
        "message_status, submit_date, connector_id) VALUES (?, ?, ?, ?, 'delivered', ?, ?)",
        [message_id, source_addr, destination_addr, message, submit_date, connector_id],
    )
    smpp_cdr_id = raw.lastrowid

    # 2. Which of our numbers was this sent to?
    number = find_number(db, destination_addr)
    if not number:
        log_activity(None, "sms_unknown_number",
                     f"SMS received for unknown number: {destination_addr}")
        return {"success": True, "assigned": False,
                "message": "SMS logged but number is not in any range",
                "smpp_cdr_id": smpp_cdr_id}

    assigned_user_id = to_int(number.get("assigned_to"))
    otp_detected = detect_otp(message)
    is_test = (number.get("test_number") == number.get("number")
               or to_int(number.get("is_test")) == 1)
    sms_type = "test" if is_test else "general"

    if not assigned_user_id:
        # Unassigned pool number: log it in the CDR with no payout so it still
        # appears in reports and the Test Panel.
        cdr = db.query(
            "INSERT INTO sms_cdr (date_time, range_id, number, cli, user_id, sms_count, sms_type, "
            "message, otp_detected, currency, my_payout, user_payout, agent_payout, profit, "
            "smpp_message_id, smpp_status, connector_id, processed_at) "
            "VALUES (?, ?, ?, ?, NULL, 1, ?, ?, ?, ?, 0, 0, 0, 0, ?, 'delivered', ?, NOW())",
            [submit_date, number["range_id"], number["number"], source_addr, sms_type,
             message, otp_detected, number.get("currency"), message_id, connector_id],
        )
        db.query("UPDATE smpp_cdr SET cdr_id = ? WHERE id = ?", [cdr.lastrowid, smpp_cdr_id])
        _bump_smpp_counters(db, connector_id)
        return {"success": True, "assigned": False, "cdr_id": cdr.lastrowid,
                "smpp_cdr_id": smpp_cdr_id, "number": number["number"],
                "range": number.get("range_name"), "otp_detected": bool(otp_detected)}

    # 3. Resolve the hierarchy above the assigned account.
    assigned_user = db.query(
        "SELECT id, username, parent_id, role FROM users WHERE id = ?", [assigned_user_id]
    ).fetch()
    if not assigned_user:
        return {"success": False, "error": "Assigned user not found",
                "smpp_cdr_id": smpp_cdr_id}

    agent_id = None
    if assigned_user["role"] == "client" and assigned_user.get("parent_id"):
        agent = db.query("SELECT id FROM users WHERE id = ? AND role='agent'",
                         [to_int(assigned_user["parent_id"])]).fetch()
        agent_id = to_int(agent["id"]) if agent else None
    manager_id = resolve_manager_id_for_user(assigned_user_id)

    # 4. Price it from the number's own payment term.
    pay_term = number.get("pay_term") or "1/1"
    payout_column = PAYOUT_COLUMN.get(pay_term, "payout_1_1")
    assigned_payout = to_float(
        number.get("payout_rate")
        or number.get(payout_column)
        or number.get("payout_1_1")
    )
    agent_payout = assigned_payout * AGENT_SHARE if agent_id else 0.0
    manager_payout = assigned_payout * MANAGER_SHARE if manager_id else 0.0
    currency = number.get("currency") or "USD"

    # 5. Billing CDR.
    cdr = db.query(
        "INSERT INTO sms_cdr (date_time, range_id, number, cli, user_id, sms_count, sms_type, "
        "message, otp_detected, currency, my_payout, user_payout, agent_payout, profit, "
        "smpp_message_id, smpp_status, connector_id, processed_at) "
        "VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?, 0, ?, 'delivered', ?, NOW())",
        [submit_date, number["range_id"], number["number"], source_addr, assigned_user_id,
         sms_type, message, otp_detected, currency, manager_payout, assigned_payout, agent_payout,
         message_id, connector_id],
    )
    cdr_id = cdr.lastrowid
    db.query("UPDATE smpp_cdr SET cdr_id = ? WHERE id = ?", [cdr_id, smpp_cdr_id])

    # 6. Credit every level in one transaction.
    try:
        with db.transaction() as tx:
            tx.query(
                "INSERT INTO user_balances (user_id, currency, balance) VALUES (?, ?, ?) "
                "ON DUPLICATE KEY UPDATE balance = balance + ?",
                [assigned_user_id, currency, assigned_payout, assigned_payout])
            if agent_id and agent_payout > 0:
                tx.query(
                    "INSERT INTO user_balances (user_id, currency, balance) VALUES (?, ?, ?) "
                    "ON DUPLICATE KEY UPDATE balance = balance + ?",
                    [agent_id, currency, agent_payout, agent_payout])
            if manager_id and manager_payout > 0:
                tx.query(
                    "INSERT INTO user_balances (user_id, currency, balance) VALUES (?, ?, ?) "
                    "ON DUPLICATE KEY UPDATE balance = balance + ?",
                    [manager_id, currency, manager_payout, manager_payout])
            tx.query("UPDATE smpp_config SET total_received = total_received + 1, "
                     "last_received_at = NOW() WHERE status = 'active'")
    except Exception as exc:
        log_activity(None, "smpp_balance_error",
                     f"Failed to update balances for SMS {message_id}: {exc}")
        return {"success": False, "error": "Failed to update balances",
                "cdr_id": cdr_id, "smpp_cdr_id": smpp_cdr_id}

    _bump_carrier_counter(db, connector_id)

    # 7. Tell the humans (notification bell), but skip the Activity Log entry —
    # incoming SMS floods that log, so it's intentionally left out here.
    create_notification(assigned_user_id, "SMS Received",
                        f"New SMS on {number['number']} from {source_addr}", "info")
    if agent_id:
        create_notification(agent_id, "Client SMS",
                            f"Client received SMS on {number['number']}", "info")

    return {
        "success": True,
        "assigned": True,
        "cdr_id": cdr_id,
        "smpp_cdr_id": smpp_cdr_id,
        "number": number["number"],
        "range": number.get("range_name"),
        "client_id": assigned_user_id,
        "agent_id": agent_id,
        "manager_id": manager_id,
        "otp_detected": bool(otp_detected),
        "payouts": {
            "client": assigned_payout,
            "agent": agent_payout,
            "manager": manager_payout,
            "currency": currency,
        },
    }


def _bump_smpp_counters(db: Database, connector_id: str = "") -> None:
    try:
        db.query("UPDATE smpp_config SET total_received = total_received + 1, "
                 "last_received_at = NOW() WHERE status = 'active'")
    except Exception:
        pass
    _bump_carrier_counter(db, connector_id)


def _bump_carrier_counter(db: Database, connector_id: str = "") -> None:
    """Per-carrier counter, so Admin > Live Sessions shows real traffic per
    supplier instead of a column that is always zero. connector_id carries the
    supplier name the SMPP engine bound as."""
    if not connector_id:
        return
    try:
        db.query("UPDATE smpp_users SET total_messages = total_messages + 1 "
                 "WHERE supplier_name = ? OR username = ? OR system_id = ?",
                 [connector_id, connector_id, connector_id])
    except Exception:
        pass
