"""
SMPP API — port of public/api/smpp.php.

    /api/smpp.php?action=receive   inbound webhook (POST + X-API-KEY)
    /api/smpp.php?action=status    admin-only connection status
    /api/smpp.php?action=stats     per-role counters

Two fixes carried over from the PHP version:

  * `pgrep -f jasmind` matched its own shell command line, so the panel
    reported "Jasmin running" even when nothing was running. Status now comes
    from the built-in SMPP engine, which actually knows whether it is bound,
    with an exact-name process check as a secondary signal.
  * The webhook returned 503 whenever SMPP_WEBHOOK_KEY was blank. That is still
    the safe default (an open webhook would let anyone forge OTP records), but
    the error now says exactly which setting to fill in.
"""
from __future__ import annotations

import logging

import hmac
import shutil
import subprocess
from datetime import datetime

from fastapi import APIRouter, Depends, Request

from core import config
from core import sms_spool
from core.context import Ctx, get_ctx
from core.helpers import ApiError, json_response, sanitize, to_int, validate_api_token
from core.sms_ingest import ingest_sms
from core.smpp_service import service as smpp_service

logger = logging.getLogger("g1t.webhook")

router = APIRouter()


def _require_auth(ctx: Ctx):
    if ctx.session.logged_in and ctx.session.get("user_id"):
        return to_int(ctx.session.get("user_id")), str(ctx.session.get("role") or "client")
    auth = ctx.request.headers.get("authorization") or ""
    token = auth[7:].strip() if auth.lower().startswith("bearer ") else (
        ctx.request.headers.get("x-api-token") or ctx.q("token") or ""
    )
    user = validate_api_token(token) if token else None
    if not user:
        raise ApiError("Unauthorized", 401)
    return to_int(user["id"]), str(user["role"])


def _jasmin_running() -> bool:
    """Exact-name match only. `pgrep -f jasmind` also matches the shell that
    runs the check itself, which is why the old status was always true."""
    if not shutil.which("pgrep"):
        return False
    try:
        result = subprocess.run(["pgrep", "-x", "jasmind"],
                                capture_output=True, timeout=3)
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        return False


async def receive_sms(ctx: Ctx):
    data = await ctx.body()
    if not data:
        data = dict(ctx.request.query_params)

    source = data.get("source_addr") or data.get("from") or ""
    destination = data.get("destination_addr") or data.get("to") or ""
    text = data.get("short_message") or data.get("message") or ""
    msg_id = data.get("message_id") or ""
    connector = data.get("connector_id") or ""
    when = (data.get("submit_date") or data.get("timestamp")
            or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        result = ingest_sms(
            source_addr=source,
            destination_addr=destination,
            message=text,
            message_id=msg_id,
            connector_id=connector,
            submit_date=when,
        )
    except Exception as exc:
        # The database is unreachable. Persist to disk and acknowledge, so the
        # sender does not discard the OTP - the replay task will store it.
        logger.exception("Webhook ingest failed for %s: %s", destination, exc)
        queued = sms_spool.spool(source, destination, text, msg_id, connector,
                                 when, f"{type(exc).__name__}: {exc}")
        if queued:
            return json_response({
                "success": True, "queued": True,
                "message": "SMS accepted and queued; database is temporarily "
                           "unavailable and it will be stored automatically.",
            }, 202)
        return json_response({"error": "SMS could not be stored"}, 503)

    if not result.get("success"):
        return json_response({"error": result.get("error", "Failed to process SMS")}, 400)
    if result.get("duplicate"):
        # Re-sent by the carrier or replayed from the spool. Acknowledge without
        # creating a second CDR, so the sender stops retrying.
        return json_response({
            "success": True, "duplicate": True,
            "message": "Already processed",
            "cdr_id": result.get("cdr_id"),
            "smpp_cdr_id": result.get("smpp_cdr_id"),
        })
    if not result.get("assigned"):
        return json_response({
            "success": True,
            "message": result.get("message", "SMS logged but number not assigned"),
            "smpp_cdr_id": result.get("smpp_cdr_id"),
        })

    return json_response({
        "success": True,
        "message": "SMS processed successfully",
        "data": {
            "cdr_id": result["cdr_id"],
            "smpp_cdr_id": result["smpp_cdr_id"],
            "number": result["number"],
            "range": result["range"],
            "client_id": result["client_id"],
            "agent_id": result["agent_id"],
            "manager_id": result["manager_id"],
            "otp_detected": result["otp_detected"],
            "payouts": result["payouts"],
        },
    })


def smpp_status(ctx: Ctx):
    config_row = None
    hourly = daily = 0
    try:
        config_row = ctx.db.query(
            "SELECT * FROM smpp_config WHERE status = 'active' LIMIT 1").fetch()
        hourly = to_int(ctx.db.query(
            "SELECT COUNT(*) as count FROM smpp_cdr "
            "WHERE submit_date >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 1 HOUR)").scalar())
        daily = to_int(ctx.db.query(
            "SELECT COUNT(*) as count FROM smpp_cdr "
            "WHERE submit_date >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 24 HOUR)").scalar())
    except Exception:
        pass  # optional SMPP migration not installed yet

    engine = smpp_service.status()
    return json_response({
        "success": True,
        "status": {
            # The built-in engine is the real source of truth now.
            "smpp_engine_running": engine["server_running"],
            "bound_accounts": engine["bound_accounts"],
            "outbound_connections": engine["outbound_connections"],
            "jasmin_running": _jasmin_running(),
            "smpp_port": engine["listen_port"],
            "webhook_configured": bool(config.SMPP_WEBHOOK_KEY),
            "config": {
                "name": config_row["config_name"],
                "host": config_row["inbound_host"],
                "port": config_row["inbound_port"],
                "system_id": config_row["inbound_system_id"],
                "total_received": to_int(config_row.get("total_received")),
                "last_received": config_row.get("last_received_at"),
            } if config_row else None,
            "stats": {"hourly": hourly, "daily": daily},
        },
    })


def smpp_stats(ctx: Ctx, user_id: int, role: str):
    today = datetime.utcnow().strftime("%Y-%m-%d")
    this_month = datetime.utcnow().strftime("%Y-%m")
    stats: dict = {}

    try:
        if role in ("manager", "admin"):
            stats["today"] = to_int(ctx.db.query(
                "SELECT COUNT(*) as count FROM smpp_cdr WHERE DATE(submit_date) = ?",
                [today]).scalar())
            stats["month"] = to_int(ctx.db.query(
                "SELECT COUNT(*) as count FROM smpp_cdr "
                "WHERE DATE_FORMAT(submit_date, '%Y-%m') = ?", [this_month]).scalar())
            stats["by_range"] = ctx.db.query(
                "SELECT r.range_name, COUNT(*) as count FROM smpp_cdr s "
                "JOIN sms_cdr c ON s.cdr_id = c.id "
                "JOIN sms_ranges r ON c.range_id = r.id "
                "WHERE DATE_FORMAT(s.submit_date, '%Y-%m') = ? "
                "GROUP BY r.id ORDER BY count DESC LIMIT 5", [this_month]).fetchall()
        elif role == "agent":
            stats["today"] = to_int(ctx.db.query(
                "SELECT COUNT(*) as count FROM smpp_cdr s JOIN sms_cdr c ON s.cdr_id = c.id "
                "WHERE DATE(s.submit_date) = ? AND (c.user_id = ? OR c.user_id IN "
                "(SELECT id FROM users WHERE parent_id = ?))",
                [today, user_id, user_id]).scalar())
        else:
            stats["today"] = to_int(ctx.db.query(
                "SELECT COUNT(*) as count FROM smpp_cdr s JOIN sms_cdr c ON s.cdr_id = c.id "
                "WHERE DATE(s.submit_date) = ? AND c.user_id = ?",
                [today, user_id]).scalar())
    except Exception:
        stats = {"today": 0, "month": 0, "by_range": []}

    return json_response({"success": True, "stats": stats})


@router.api_route("/api/smpp.php", methods=["GET", "POST"])
@router.api_route("/api/smpp", methods=["GET", "POST"])
async def smpp_endpoint(request: Request, ctx: Ctx = Depends(get_ctx)):
    action = ctx.q("action") or (await ctx.value("action")) or "receive"

    if action == "receive":
        if ctx.method != "POST":
            return json_response(
                {"error": "Method not allowed. Use POST for receive action"}, 405)

        api_key = ctx.request.headers.get("x-api-key") or ctx.q("api_key") or ""
        valid_key = str(config.SMPP_WEBHOOK_KEY or "")
        if valid_key == "":
            return json_response({
                "error": "SMPP webhook is not configured",
                "hint": "Set SMPP_WEBHOOK_KEY in config/.env to a long random "
                        "value, then send it as the X-API-KEY header.",
            }, 503)
        if not hmac.compare_digest(valid_key, str(api_key)):
            return json_response({"error": "Invalid API key"}, 401)

        return await receive_sms(ctx)

    if action == "status":
        user_id, role = _require_auth(ctx)
        if role != "admin":
            return json_response({"error": "Admin access required"}, 403)
        return smpp_status(ctx)

    if action == "stats":
        user_id, role = _require_auth(ctx)
        return smpp_stats(ctx, user_id, role)

    return json_response({"error": "Invalid action"}, 400)
