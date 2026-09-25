"""
SMS CDR API — port of public/api/cdr.php.

Records, statistics, CSV export, plus the legacy Jasmin "receive" webhook.
Accepts either a logged-in session or an API token, exactly like the PHP.
"""
from __future__ import annotations

import csv
import io
import re
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from core.context import Ctx, get_ctx
from core.helpers import (
    ApiError, create_notification, json_response, log_activity, manager_owner_sql,
    resolve_manager_id_for_user, sanitize, to_float, to_int, update_balance,
    validate_api_token,
)

router = APIRouter()

# Privacy-preserving OTP classification. The inbound text is inspected only
# long enough to classify it; only the boolean flag is stored.
OTP_PATTERN = re.compile(
    r"\b(otp|one[- ]?time|verification|verify|security|login|passcode|auth(?:entication)?)"
    r"[^\r\n]{0,60}\b\d{4,8}\b"
    r"|\b\d{4,8}\b[^\r\n]{0,60}\b(otp|code|verification|verify|passcode)\b",
    re.IGNORECASE,
)


def _today_start() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d 00:00:00")


def _today_end() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d 23:59:59")


def _resolve_identity(ctx: Ctx):
    """Session first, API token second — the PHP preamble of cdr.php."""
    if ctx.session.logged_in and ctx.session.get("user_id"):
        return to_int(ctx.session.get("user_id")), str(ctx.session.get("role") or "")
    auth = ctx.request.headers.get("authorization") or ""
    token = auth[7:].strip() if auth.lower().startswith("bearer ") else (
        ctx.request.headers.get("x-api-token") or ctx.q("token") or ""
    )
    api_user = validate_api_token(token) if token else None
    if not api_user:
        raise ApiError("Unauthorized", 401)
    return to_int(api_user["id"]), str(api_user["role"])


def _scope_where(role: str, user_id: int, params: list, alias: str = "") -> str:
    """Role-based visibility, shared by datatable/stats/export."""
    col = f"{alias}user_id" if alias else "user_id"
    if role == "manager":
        params.append(user_id)
        return f" AND {manager_owner_sql(col)} = ?"
    if role == "agent":
        params.extend([user_id, user_id])
        return f" AND ({col} = ? OR {col} IN (SELECT id FROM users WHERE parent_id = ?))"
    params.append(user_id)
    return f" AND {col} = ?"


def cdr_datatable(ctx: Ctx, user_id: int, role: str):
    params_get = ctx.all_params()
    draw = to_int(params_get.get("draw"), 1)
    start = max(0, to_int(params_get.get("start"), 0))
    length = to_int(params_get.get("length"), 25)
    length = 25 if length < 1 or length > 5000 else length
    search = params_get.get("search[value]") or params_get.get("search") or ""

    date_from = sanitize(params_get.get("fdate1") or _today_start())
    date_to = sanitize(params_get.get("fdate2") or _today_end())
    range_id = to_int(params_get.get("frange"))
    agent_id = to_int(params_get.get("fagent"))
    client_id = to_int(params_get.get("fclient"))
    number = sanitize(params_get.get("fnum") or "")
    cli = sanitize(params_get.get("fcli") or "")

    # Group-by is a fixed whitelist — nothing user-supplied reaches the SQL.
    group_by = []
    if params_get.get("fgdate"):
        group_by.append("DATE(c.date_time)")
    if params_get.get("fgmonth"):
        group_by.append("DATE_FORMAT(c.date_time, '%Y-%m')")
    if params_get.get("fgrange"):
        group_by.append("c.range_id")
    if params_get.get("fgagent"):
        group_by.append("c.user_id")
    if params_get.get("fgnumber"):
        group_by.append("c.number")
    if params_get.get("fgcli"):
        group_by.append("c.cli")

    where = "c.date_time BETWEEN ? AND ?"
    params: list = [date_from, date_to]
    where += _scope_where(role, user_id, params, "c.")

    if role == "manager" and agent_id:
        where += " AND c.user_id = ?"
        params.append(agent_id)
    elif role == "agent" and client_id:
        where += " AND c.user_id = ?"
        params.append(client_id)

    if range_id:
        where += " AND c.range_id = ?"
        params.append(range_id)
    if number:
        where += " AND c.number LIKE ?"
        params.append(f"%{number}%")
    if cli:
        where += " AND c.cli LIKE ?"
        params.append(f"%{cli}%")
    if search:
        where += " AND (c.number LIKE ? OR c.cli LIKE ?)"
        params += [f"%{search}%"] * 2

    records_total = to_int(ctx.db.query(
        f"SELECT COUNT(*) as count FROM sms_cdr c WHERE {where}", params).scalar())

    if group_by:
        group_clause = "GROUP BY " + ", ".join(group_by)
        select_fields = (
            "DATE(c.date_time) as date, "
            "COALESCE(r.range_name, 'Unknown') as range_name, "
            "COALESCE(c.number, '-') as number, "
            "COALESCE(c.cli, '-') as cli, "
            "COALESCE(u.username, '-') as username, "
            "SUM(c.sms_count) as sms_count, "
            "c.sms_type, c.currency, "
            "SUM(c.my_payout) as my_payout, "
            "SUM(c.user_payout) as user_payout, "
            "SUM(c.profit) as profit"
        )
    else:
        group_clause = ""
        select_fields = "c.*, r.range_name, u.username"

    rows = ctx.db.query(
        f"SELECT {select_fields} FROM sms_cdr c "
        f"LEFT JOIN sms_ranges r ON c.range_id = r.id "
        f"LEFT JOIN users u ON c.user_id = u.id "
        f"WHERE {where} {group_clause} ORDER BY c.date_time DESC LIMIT {start}, {length}",
        params,
    ).fetchall()

    data = []
    for row in rows:
        type_badge = ('<span class="label label-warning">Test</span>'
                      if row.get("sms_type") == "test"
                      else '<span class="label label-success">General</span>')
        # "SMS" column shows the actual message text when available (single-record
        # view); grouped/aggregated rows have no single message, so fall back to
        # the summed count in that case.
        sms_cell = row.get("message") if not group_by else None
        if not sms_cell:
            sms_cell = row.get("sms_count")
        data.append([
            row.get("date_time") or row.get("date"),
            row.get("range_name") or "-",
            row.get("number"),
            row.get("cli") or "-",
            row.get("username") or "-",
            sms_cell,
            type_badge,
            row.get("currency"),
            f"{to_float(row.get('my_payout')):,.4f}",
            f"{to_float(row.get('user_payout')):,.4f}",
        ])

    totals_rows = ctx.db.query(
        f"SELECT SUM(c.sms_count) as total_sms, c.currency, "
        f"SUM(c.my_payout) as total_my_payout, SUM(c.user_payout) as total_user_payout, "
        f"SUM(c.profit) as total_profit "
        f"FROM sms_cdr c WHERE {where} GROUP BY c.currency WITH ROLLUP",
        params,
    ).fetchall()

    totals = {
        "usd_in": 0, "eur_in": 0, "gbp_in": 0,
        "usd_out": 0, "eur_out": 0, "gbp_out": 0,
        "usd_profit": 0, "eur_profit": 0, "gbp_profit": 0,
        "total_sms": 0,
    }
    for row in totals_rows:
        key = {"USD": "usd", "EUR": "eur", "GBP": "gbp"}.get(row.get("currency"))
        if key:
            totals[f"{key}_in"] = row.get("total_my_payout")
            totals[f"{key}_out"] = row.get("total_user_payout")
            totals[f"{key}_profit"] = row.get("total_profit")
        totals["total_sms"] = row.get("total_sms")

    # Totals stay separate from the record list — appending them as a fake CDR
    # made the "Recent Incoming SMS" table render a bogus extra SMS row.
    return json_response({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_total,
        "data": data,
        "totals": totals,
    })


def cdr_stats(ctx: Ctx, user_id: int, role: str):
    period = sanitize(ctx.q("period") or "today")
    group = sanitize(ctx.q("group") or "day")
    now = datetime.utcnow()

    if period == "today":
        date_from, date_to = _today_start(), _today_end()
    elif period == "yesterday":
        day = now - timedelta(days=1)
        date_from = day.strftime("%Y-%m-%d 00:00:00")
        date_to = day.strftime("%Y-%m-%d 23:59:59")
    elif period == "week":
        date_from = (now - timedelta(days=7)).strftime("%Y-%m-%d 00:00:00")
        date_to = _today_end()
    elif period == "month":
        date_from = now.strftime("%Y-%m-01 00:00:00")
        date_to = _today_end()
    elif period == "last_month":
        first = now.replace(day=1)
        last_month_end = first - timedelta(days=1)
        date_from = last_month_end.strftime("%Y-%m-01 00:00:00")
        date_to = last_month_end.strftime("%Y-%m-%d 23:59:59")
    else:
        date_from = sanitize(ctx.q("from") or _today_start())
        date_to = sanitize(ctx.q("to") or _today_end())

    where = "date_time BETWEEN ? AND ?"
    params: list = [date_from, date_to]
    if role == "agent":
        # stats scoped clients only, matching the PHP query
        where += " AND (user_id = ? OR user_id IN (SELECT id FROM users WHERE parent_id = ? AND role='client'))"
        params += [user_id, user_id]
    else:
        where += _scope_where(role, user_id, params)

    group_map = {
        "hour": ("DATE(date_time), HOUR(date_time)", "DATE(date_time) as date, HOUR(date_time) as hour"),
        "day": ("DATE(date_time)", "DATE(date_time) as date"),
        "range": ("range_id", "range_id"),
        "user": ("user_id", "user_id"),
        "type": ("sms_type", "sms_type"),
    }
    group_clause, select_group = group_map.get(group, group_map["day"])

    stats = ctx.db.query(
        f"SELECT {select_group}, COUNT(*) as total_sms, SUM(sms_count) as sms_count, currency, "
        f"SUM(my_payout) as my_payout, SUM(user_payout) as user_payout, SUM(profit) as profit "
        f"FROM sms_cdr WHERE {where} GROUP BY {group_clause}, currency ORDER BY MAX(date_time) DESC",
        params,
    ).fetchall()

    return json_response({"success": True, "stats": stats,
                          "period": {"from": date_from, "to": date_to}})


def cdr_export(ctx: Ctx, user_id: int, role: str):
    fmt = sanitize(ctx.q("format") or "csv")
    date_from = sanitize(ctx.q("fdate1") or _today_start())
    date_to = sanitize(ctx.q("fdate2") or _today_end())

    where = "c.date_time BETWEEN ? AND ?"
    params: list = [date_from, date_to]
    if role == "agent":
        where += (" AND (c.user_id = ? OR c.user_id IN "
                  "(SELECT id FROM users WHERE parent_id = ? AND role='client'))")
        params += [user_id, user_id]
    else:
        where += _scope_where(role, user_id, params, "c.")

    rows = ctx.db.query(
        f"SELECT c.*, r.range_name, u.username FROM sms_cdr c "
        f"LEFT JOIN sms_ranges r ON c.range_id = r.id "
        f"LEFT JOIN users u ON c.user_id = u.id "
        f"WHERE {where} ORDER BY c.date_time DESC",
        params,
    ).fetchall()

    if fmt != "csv":
        return json_response({"success": True, "data": rows})

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Date", "Range", "Number", "CLI", "User", "SMS Count", "Type",
                     "Currency", "My Payout", "User Payout", "Profit"])
    for row in rows:
        writer.writerow([
            row.get("date_time"), row.get("range_name"), row.get("number"), row.get("cli"),
            row.get("username"), row.get("sms_count"), row.get("sms_type"), row.get("currency"),
            row.get("my_payout"), row.get("user_payout"), row.get("profit"),
        ])
    buffer.seek(0)
    filename = f"sms_cdr_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def receive_sms(ctx: Ctx):
    """Legacy Jasmin webhook. The full ingest path used by the SMPP engine
    lives in core.sms_ingest; this endpoint is kept for compatibility."""
    body = await ctx.body()
    number = sanitize(body.get("to") or body.get("number") or "")
    cli = sanitize(body.get("from") or body.get("cli") or "")
    message = str(body.get("message") or "")
    timestamp = body.get("timestamp") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    otp_detected = 1 if OTP_PATTERN.search(message) else 0

    if not number:
        return json_response({"error": "Number is required"}, 400)

    number_data = ctx.db.query(
        "SELECT n.*, r.*, r.id as range_id, n.assigned_to as user_id "
        "FROM sms_numbers n JOIN sms_ranges r ON n.range_id = r.id WHERE n.number = ?",
        [number],
    ).fetch()
    if not number_data:
        return json_response({"success": False, "message": "Number not found"}, 404)

    sms_type = "test" if (number_data.get("test_number") == number
                          or to_int(number_data.get("is_test"))) else "general"

    my_payout = to_float(number_data.get("payout_1_1"))
    user_payout = my_payout * 0.9 if number_data.get("assigned_to") else 0.0
    profit = my_payout - user_payout

    result = ctx.db.query(
        "INSERT INTO sms_cdr (date_time, range_id, number, cli, user_id, sms_count, sms_type, "
        "message, otp_detected, currency, my_payout, user_payout, profit) "
        "VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)",
        [timestamp, number_data["range_id"], number, cli, number_data.get("assigned_to"),
         sms_type, message, otp_detected, number_data.get("currency"), my_payout, user_payout, profit],
    )

    if my_payout > 0:
        manager_id = resolve_manager_id_for_user(to_int(number_data.get("assigned_to")))
        if manager_id:
            update_balance(manager_id, number_data.get("currency"), my_payout, "credit")
    if user_payout > 0 and number_data.get("assigned_to"):
        update_balance(number_data["assigned_to"], number_data.get("currency"), user_payout, "credit")

    if number_data.get("assigned_to"):
        create_notification(number_data["assigned_to"], "SMS Received",
                            f"SMS received on {number} from {cli}", "info")
    # Intentionally no log_activity() call here — incoming SMS shouldn't flood the Activity Log.

    return json_response({
        "success": True,
        "message": "SMS processed successfully",
        "cdr_id": result.lastrowid,
        "payout": {"my_payout": my_payout, "user_payout": user_payout,
                   "currency": number_data.get("currency")},
    })


@router.api_route("/api/cdr.php", methods=["GET", "POST"])
@router.api_route("/api/cdr", methods=["GET", "POST"])
async def cdr_endpoint(request: Request, ctx: Ctx = Depends(get_ctx)):
    user_id, role = _resolve_identity(ctx)
    action = ctx.q("action") or "list"

    if ctx.method == "GET":
        if action == "stats":
            return cdr_stats(ctx, user_id, role)
        if action == "export":
            return cdr_export(ctx, user_id, role)
        return cdr_datatable(ctx, user_id, role)

    if ctx.method == "POST":
        if action == "receive":
            return await receive_sms(ctx)
        return json_response({"error": "Invalid action"}, 400)

    return json_response({"error": "Method not allowed"}, 405)
