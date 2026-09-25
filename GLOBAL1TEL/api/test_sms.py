"""
Test SMS API — port of public/api/test.php.

Test mode records a simulated result only; no real SMS is transmitted here.
"""
from __future__ import annotations

import math
import re
import secrets

from fastapi import APIRouter, Depends, Request

from core.context import Ctx, get_auth_ctx
from core.helpers import json_response, log_activity, sanitize, to_float, to_int

router = APIRouter()

DEST_RE = re.compile(r"^\+?[0-9]{10,15}$")

GSM7_CHARS = set(
    "@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ^{}\\[~]|€!\"#¤%&'()*+,-./"
    "0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ§"
    "¿abcdefghijklmnopqrstuvwxyzäöñüà "
)


def calculate_sms_count(message: str) -> int:
    """GSM-7 fits 160 chars (153 when concatenated); UCS-2 fits 70 (67)."""
    if not message:
        return 1
    is_gsm7 = all(ch in GSM7_CHARS for ch in message)
    length = len(message)
    if is_gsm7:
        return 1 if length <= 160 else math.ceil(length / 153)
    return 1 if length <= 70 else math.ceil(length / 67)


def get_test_numbers(ctx: Ctx):
    if ctx.role in ("manager", "admin"):
        # Admin-created test inventory is global for all Managers.
        rows = ctx.db.query(
            "SELECT n.id, n.number, n.range_id, r.range_name, r.prefix, r.currency "
            "FROM sms_numbers n JOIN sms_ranges r ON n.range_id = r.id "
            "WHERE r.status='active' AND n.is_test=1 ORDER BY r.range_name, n.number"
        ).fetchall()
    elif ctx.role == "agent":
        rows = ctx.db.query(
            "SELECT n.id, n.number, n.range_id, r.range_name, r.prefix, r.currency "
            "FROM sms_numbers n JOIN sms_ranges r ON n.range_id = r.id "
            "WHERE (n.assigned_to = ? OR n.assigned_to IN "
            "(SELECT id FROM users WHERE parent_id = ?)) "
            "AND n.status = 'assigned' AND n.is_test = 1 ORDER BY r.range_name, n.number",
            [ctx.user_id, ctx.user_id]).fetchall()
    else:
        rows = ctx.db.query(
            "SELECT n.id, n.number, n.range_id, r.range_name, r.prefix, r.currency "
            "FROM sms_numbers n JOIN sms_ranges r ON n.range_id = r.id "
            "WHERE n.assigned_to = ? AND n.status = 'assigned' AND n.is_test = 1 "
            "ORDER BY r.range_name, n.number", [ctx.user_id]).fetchall()

    return json_response({"success": True, "data": rows})


async def send_test_sms(ctx: Ctx):
    body = await ctx.body()
    number_id = to_int(body.get("number_id"))
    destination = sanitize(body.get("destination") or "")
    message = body.get("message") or ""

    if not number_id:
        return json_response({"error": "Number ID required"}, 400)
    if not destination or not DEST_RE.match(destination):
        return json_response(
            {"error": "Valid destination number required "
                      "(10-15 digits, optional + prefix)"}, 400)
    if not message:
        return json_response({"error": "Message required"}, 400)
    if len(message) > 1600:
        return json_response({"error": "Message too long (max 1600 characters)"}, 400)

    if ctx.role in ("manager", "admin"):
        number = ctx.db.query(
            "SELECT n.*, r.range_name, r.prefix, r.currency FROM sms_numbers n "
            "JOIN sms_ranges r ON n.range_id = r.id WHERE n.id = ? AND n.is_test = 1",
            [number_id]).fetch()
    elif ctx.role == "agent":
        number = ctx.db.query(
            "SELECT n.*, r.range_name, r.prefix, r.currency FROM sms_numbers n "
            "JOIN sms_ranges r ON n.range_id = r.id WHERE n.id = ? AND n.is_test = 1 "
            "AND (n.assigned_to = ? OR n.assigned_to IN "
            "(SELECT id FROM users WHERE parent_id = ? AND role='client'))",
            [number_id, ctx.user_id, ctx.user_id]).fetch()
    else:
        number = ctx.db.query(
            "SELECT n.*, r.range_name, r.prefix, r.currency FROM sms_numbers n "
            "JOIN sms_ranges r ON n.range_id = r.id "
            "WHERE n.id = ? AND n.is_test = 1 AND n.assigned_to = ?",
            [number_id, ctx.user_id]).fetch()

    if not number:
        return json_response({"error": "Number not found or access denied"}, 404)

    sms_count = calculate_sms_count(message)

    rng = ctx.db.query(
        "SELECT payout_1_1, payout_7_1, payout_7_7, payout_30_45 FROM sms_ranges WHERE id = ?",
        [number["range_id"]]).fetch()
    if not rng:
        return json_response({"error": "Range not found"}, 404)

    rate = to_float(rng["payout_1_1"])          # test SMS always uses the 1/1 rate
    currency = number.get("currency")
    cost = rate * sms_count
    message_id = "TEST-" + secrets.token_hex(8).upper()

    result = ctx.db.query(
        "INSERT INTO sms_cdr (date_time, range_id, number, cli, user_id, sms_count, sms_type, "
        "message, currency, my_payout, user_payout, agent_payout, profit, smpp_message_id, smpp_status, "
        "processed_at) VALUES (UTC_TIMESTAMP(), ?, ?, ?, ?, ?, 'test', ?, ?, 0, ?, 0, 0, ?, "
        "'pending', UTC_TIMESTAMP())",
        [number["range_id"], number["number"], destination, ctx.user_id, sms_count,
         message, currency, cost, message_id])
    cdr_id = result.lastrowid

    ctx.db.query(
        "UPDATE sms_cdr SET smpp_status = 'delivered', processed_at = UTC_TIMESTAMP() WHERE id = ?",
        [cdr_id])

    log_activity(ctx.user_id, "test_sms",
                 f"Sent test SMS from {number['number']} to {destination}")

    return json_response({
        "success": True,
        "message": "Test SMS submitted successfully",
        "data": {
            "message_id": message_id,
            "from": number["number"],
            "to": destination,
            "sms_count": sms_count,
            "cost": cost,
            "currency": currency,
            "status": "delivered",
        },
    })


def get_test_history(ctx: Ctx):
    limit = max(1, min(500, ctx.q_int("limit", 50)))
    offset = max(0, ctx.q_int("start", 0))

    history = ctx.db.query(
        f"SELECT c.*, r.range_name FROM sms_cdr c JOIN sms_ranges r ON c.range_id = r.id "
        f"WHERE c.user_id = ? AND c.sms_type = 'test' ORDER BY c.date_time DESC "
        f"LIMIT {limit} OFFSET {offset}", [ctx.user_id]).fetchall()
    total = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM sms_cdr WHERE user_id = ? AND sms_type = 'test'",
        [ctx.user_id]).scalar())

    return json_response({"success": True, "data": history, "total": total})


@router.api_route("/api/test.php", methods=["GET", "POST"])
@router.api_route("/api/test", methods=["GET", "POST"])
async def test_endpoint(request: Request, ctx: Ctx = Depends(get_auth_ctx)):
    action = ctx.q("action") or ("send" if ctx.method == "POST" else "numbers")

    if ctx.method == "GET":
        if action == "numbers":
            return get_test_numbers(ctx)
        if action == "history":
            return get_test_history(ctx)
        return json_response({"error": "Invalid action"}, 400)

    if ctx.method == "POST":
        if action == "send":
            return await send_test_sms(ctx)
        return json_response({"error": "Invalid action"}, 400)

    return json_response({"error": "Method not allowed"}, 405)
