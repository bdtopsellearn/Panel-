"""
Dashboard API — port of public/api/dashboard.php.

    /api/dashboard.php?action=stats   per-role tiles, trends, top lists
    /api/dashboard.php?action=chart   time series for the dashboard graphs

BUG FIXED IN THIS PORT: getChartData() referenced $managerScope, but that
variable was a local of getDashboardStats() and was never in scope there. For
a Manager the SQL came out as "... AND  = ?", so every chart request returned
a 500. The scope expression is now built where it is used.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Request

from core.context import Ctx, get_auth_ctx
from core.helpers import json_response, manager_owner_sql, to_float, to_int

router = APIRouter()


def _date(offset_days: int = 0) -> str:
    return (datetime.utcnow() - timedelta(days=offset_days)).strftime("%Y-%m-%d")


def _month(offset_months: int = 0) -> str:
    now = datetime.utcnow()
    year, month = now.year, now.month - offset_months
    while month <= 0:
        month += 12
        year -= 1
    return f"{year:04d}-{month:02d}"


def _pair(result) -> dict:
    """Turn a two-column result into {key: value}, normalising dates to text."""
    out = {}
    for row in result:
        values = list(row.values())
        if len(values) >= 2:
            key = values[0]
            if hasattr(key, "strftime"):
                key = key.strftime("%Y-%m-%d")
            out[str(key)] = values[1]
    return out


def _fill_date_series(rows, start_date: str, end_date: str) -> list:
    """Zero-fill every day in [start_date, end_date] that has no row.

    BUG FIXED HERE: the chart query only returns days that actually had at
    least one SMS (GROUP BY DATE(...)). The very first time an account gets
    even a single message, that made this come back as a ONE-point series
    (min date == max date). jqplot's DateAxisRenderer divides by the axis
    span when it auto-scales ticks, and a zero-width span sends it into an
    infinite tick-generation loop that freezes the whole tab's JS thread -
    no exception is thrown, so nothing shows up in any log. Always
    returning the full, evenly-spaced date range (real counts where they
    exist, 0 elsewhere) removes the zero-width-axis case entirely.
    """
    by_date = {}
    for row in rows:
        d = row.get("date")
        if hasattr(d, "strftime"):
            d = d.strftime("%Y-%m-%d")
        by_date[str(d)] = row

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    out = []
    day = start
    while day <= end:
        key = day.strftime("%Y-%m-%d")
        if key in by_date:
            out.append(by_date[key])
        else:
            out.append({"date": key, "count": 0, "payout": 0})
        day += timedelta(days=1)
    return out


def manager_stats(ctx: Ctx, stats: dict, today: str, this_month: str):
    uid = ctx.user_id
    scope = manager_owner_sql("sms_cdr.user_id")
    scope_c = manager_owner_sql("c.user_id")
    number_scope = manager_owner_sql("n.assigned_to")

    stats["total_agents"] = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM users WHERE role = 'agent' AND parent_id = ?",
        [uid]).scalar())
    stats["total_clients"] = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM users WHERE role = 'client' AND parent_id IN "
        "(SELECT id FROM users WHERE role = 'agent' AND parent_id = ?)", [uid]).scalar())
    stats["total_ranges"] = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM sms_ranges").scalar())
    stats["total_numbers"] = to_int(ctx.db.query(
        f"SELECT COUNT(*) as count FROM sms_numbers n JOIN sms_ranges r ON r.id=n.range_id "
        f"WHERE (n.assigned_to IS NULL AND n.status='available' AND r.status='active') "
        f"OR {number_scope} = ?", [uid]).scalar())
    stats["available_numbers"] = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM sms_numbers n JOIN sms_ranges r ON r.id=n.range_id "
        "WHERE n.status='available' AND n.assigned_to IS NULL AND r.status='active'").scalar())

    row = ctx.db.query(
        f"SELECT COUNT(*) as count, COALESCE(SUM(my_payout), 0) as payout FROM sms_cdr "
        f"WHERE DATE(date_time) = ? AND {scope} = ?", [today, uid]).fetch()
    stats["today_sms"] = to_int(row["count"])
    stats["today_payout"] = to_float(row["payout"])

    row = ctx.db.query(
        f"SELECT COUNT(*) as count, COALESCE(SUM(my_payout), 0) as payout FROM sms_cdr "
        f"WHERE DATE_FORMAT(date_time, '%Y-%m') = ? AND {scope} = ?", [this_month, uid]).fetch()
    stats["month_sms"] = to_int(row["count"])
    stats["month_payout"] = to_float(row["payout"])

    stats["balances"] = ctx.db.query(
        "SELECT currency, balance FROM user_balances WHERE user_id = ?", [uid]).fetch_key_pair()
    stats["pending_requests"] = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM number_requests nr JOIN users a ON a.id=nr.user_id "
        "WHERE nr.status='pending' AND a.role='agent' AND a.parent_id=?", [uid]).scalar())

    row = ctx.db.query(
        f"SELECT COUNT(*) as count, COALESCE(SUM(my_payout), 0) as payout FROM sms_cdr "
        f"WHERE date_time >= DATE_SUB(?, INTERVAL 7 DAY) AND {scope} = ?", [today, uid]).fetch()
    stats["last_7_days_sms"] = to_int(row["count"])
    stats["last_7_days_payout"] = to_float(row["payout"])

    daily = _pair(ctx.db.query(
        f"SELECT DATE(date_time) as date, COUNT(*) as count FROM sms_cdr "
        f"WHERE date_time >= DATE_SUB(?, INTERVAL 7 DAY) AND {scope} = ? "
        f"GROUP BY DATE(date_time) ORDER BY date", [today, uid]).fetchall())
    stats["daily_trend"] = [to_int(daily.get(_date(i), 0)) for i in range(6, -1, -1)]

    stats["top_agents"] = ctx.db.query(
        "SELECT a.username, COUNT(*) as sms_count, "
        "COALESCE(SUM(CASE WHEN u.role='client' THEN c.agent_payout ELSE c.user_payout END), 0) "
        "as payout FROM sms_cdr c JOIN users u ON c.user_id = u.id "
        "JOIN users a ON a.id = CASE WHEN u.role='client' THEN u.parent_id ELSE u.id END "
        "WHERE DATE_FORMAT(c.date_time, '%Y-%m') = ? AND a.role = 'agent' AND a.parent_id = ? "
        "GROUP BY a.id, a.username ORDER BY sms_count DESC LIMIT 5",
        [this_month, uid]).fetchall()

    stats["top_ranges"] = ctx.db.query(
        f"SELECT r.range_name, COUNT(*) as sms_count, SUM(c.my_payout) as payout FROM sms_cdr c "
        f"JOIN sms_ranges r ON c.range_id = r.id "
        f"WHERE DATE_FORMAT(c.date_time, '%Y-%m') = ? AND {scope_c} = ? "
        f"GROUP BY c.range_id, r.range_name ORDER BY sms_count DESC LIMIT 5",
        [this_month, uid]).fetchall()

    stats["recent_activity"] = ctx.db.query(
        "SELECT al.*, u.username FROM user_activity al JOIN users u ON al.user_id = u.id "
        "WHERE al.user_id = ? OR u.parent_id = ? ORDER BY al.created_at DESC LIMIT 10",
        [uid, uid]).fetchall()

    row = ctx.db.query(
        f"SELECT COUNT(*) as count, COALESCE(SUM(my_payout), 0) as payout FROM sms_cdr "
        f"WHERE DATE(date_time) = ? AND {scope} = ?", [_date(1), uid]).fetch()
    stats["yesterday_sms"] = to_int(row["count"])
    stats["yesterday_payout"] = to_float(row["payout"])

    stats["new_accounts"] = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM users WHERE DATE_FORMAT(created_at, '%Y-%m') = ? "
        "AND ((role = 'agent' AND parent_id = ?) OR parent_id IN "
        "(SELECT id FROM users WHERE parent_id = ?))", [this_month, uid, uid]).scalar())
    stats["new_numbers"] = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM sms_numbers WHERE DATE_FORMAT(created_at, '%Y-%m') = ?",
        [this_month]).scalar())

    stats["recent_agents"] = ctx.db.query(
        "SELECT u.id, u.username, u.email, u.status, u.created_at, up.phone FROM users u "
        "LEFT JOIN user_profiles up ON u.id = up.user_id "
        "WHERE u.role = 'agent' AND u.parent_id = ? ORDER BY u.created_at DESC LIMIT 5",
        [uid]).fetchall()
    # Backward-compatible key for older dashboard JavaScript
    stats["recent_clients"] = stats["recent_agents"]

    agent_expr = ("COALESCE(SUM(CASE WHEN u.role='agent' THEN c.user_payout "
                  "WHEN u.role='client' THEN c.agent_payout ELSE 0 END), 0)")
    client_expr = "COALESCE(SUM(CASE WHEN u.role='client' THEN c.user_payout ELSE 0 END), 0)"

    stats["agent_payouts"] = {
        "today": to_float(ctx.db.query(
            f"SELECT {agent_expr} as v FROM sms_cdr c LEFT JOIN users u ON u.id=c.user_id "
            f"WHERE DATE(c.date_time) = ? AND {scope_c} = ?", [today, uid]).scalar()),
        "month": to_float(ctx.db.query(
            f"SELECT {agent_expr} as v FROM sms_cdr c LEFT JOIN users u ON u.id=c.user_id "
            f"WHERE DATE_FORMAT(c.date_time, '%Y-%m') = ? AND {scope_c} = ?",
            [this_month, uid]).scalar()),
    }
    stats["client_payouts"] = {
        "today": to_float(ctx.db.query(
            f"SELECT {client_expr} as v FROM sms_cdr c LEFT JOIN users u ON u.id=c.user_id "
            f"WHERE DATE(c.date_time) = ? AND {scope_c} = ?", [today, uid]).scalar()),
        "month": to_float(ctx.db.query(
            f"SELECT {client_expr} as v FROM sms_cdr c LEFT JOIN users u ON u.id=c.user_id "
            f"WHERE DATE_FORMAT(c.date_time, '%Y-%m') = ? AND {scope_c} = ?",
            [this_month, uid]).scalar()),
    }

    totals = ctx.db.query(
        f"SELECT COALESCE(SUM(c.my_payout), 0) as manager_total, "
        f"{agent_expr} as agents_total, {client_expr} as clients_total "
        f"FROM sms_cdr c LEFT JOIN users u ON u.id=c.user_id WHERE {scope_c} = ?",
        [uid]).fetch() or {}
    manager_total = to_float(totals.get("manager_total"))
    agents_total = to_float(totals.get("agents_total"))
    clients_total = to_float(totals.get("clients_total"))
    stats["hierarchy_totals"] = {
        "manager": manager_total, "agents": agents_total, "clients": clients_total,
        "total": manager_total + agents_total + clients_total,
    }


def agent_stats(ctx: Ctx, stats: dict, today: str, this_month: str):
    uid = ctx.user_id
    mine_or_clients = "(user_id = ? OR user_id IN (SELECT id FROM users WHERE parent_id = ?))"
    payout_expr = "COALESCE(SUM(CASE WHEN user_id = ? THEN user_payout ELSE agent_payout END), 0)"

    stats["total_clients"] = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM users WHERE role = 'client' AND parent_id = ?",
        [uid]).scalar())
    stats["active_clients"] = to_int(ctx.db.query(
        "SELECT COUNT(DISTINCT user_id) as count FROM sms_cdr "
        "WHERE date_time >= DATE_SUB(?, INTERVAL 7 DAY) "
        "AND user_id IN (SELECT id FROM users WHERE parent_id = ?)", [today, uid]).scalar())
    stats["assigned_numbers"] = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM sms_numbers WHERE assigned_to = ? "
        "OR assigned_to IN (SELECT id FROM users WHERE parent_id = ?)", [uid, uid]).scalar())

    row = ctx.db.query(
        "SELECT COUNT(*) as count, COALESCE(SUM(user_payout), 0) as payout FROM sms_cdr "
        "WHERE DATE(date_time) = ? AND user_id = ?", [today, uid]).fetch()
    stats["today_sms"] = to_int(row["count"])
    stats["today_payout"] = to_float(row["payout"])

    row = ctx.db.query(
        f"SELECT COUNT(*) as count, {payout_expr} as payout FROM sms_cdr "
        f"WHERE DATE(date_time) = ? AND {mine_or_clients}", [uid, today, uid, uid]).fetch()
    stats["today_sms_total"] = to_int(row["count"])
    stats["today_payout_total"] = to_float(row["payout"])

    row = ctx.db.query(
        f"SELECT COUNT(*) as count, {payout_expr} as payout FROM sms_cdr "
        f"WHERE date_time >= DATE_SUB(?, INTERVAL 7 DAY) AND {mine_or_clients}",
        [uid, today, uid, uid]).fetch()
    stats["last_7_days_sms"] = to_int(row["count"])
    stats["last_7_days_payout"] = to_float(row["payout"])

    row = ctx.db.query(
        "SELECT COUNT(*) as count, COALESCE(SUM(user_payout), 0) as payout FROM sms_cdr "
        "WHERE DATE_FORMAT(date_time, '%Y-%m') = ? AND user_id = ?", [this_month, uid]).fetch()
    stats["month_sms"] = to_int(row["count"])
    stats["month_payout"] = to_float(row["payout"])

    row = ctx.db.query(
        f"SELECT COUNT(*) as count, {payout_expr} as payout FROM sms_cdr "
        f"WHERE DATE_FORMAT(date_time, '%Y-%m') = ? AND {mine_or_clients}",
        [uid, this_month, uid, uid]).fetch()
    stats["month_sms_total"] = to_int(row["count"])
    stats["month_payout_total"] = to_float(row["payout"])

    stats["balances"] = ctx.db.query(
        "SELECT currency, balance FROM user_balances WHERE user_id = ?", [uid]).fetch_key_pair()
    stats["available_ranges"] = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM sms_ranges WHERE status='active' "
        "AND available_numbers>0").scalar())
    stats["pending_requests"] = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM number_requests WHERE user_id = ? AND status = 'pending'",
        [uid]).scalar())

    daily = _pair(ctx.db.query(
        f"SELECT DATE(date_time) as date, COUNT(*) as count FROM sms_cdr "
        f"WHERE date_time >= DATE_SUB(?, INTERVAL 7 DAY) AND {mine_or_clients} "
        f"GROUP BY DATE(date_time) ORDER BY date", [today, uid, uid]).fetchall())
    stats["daily_trend"] = [to_int(daily.get(_date(i), 0)) for i in range(6, -1, -1)]

    stats["top_clients"] = ctx.db.query(
        "SELECT u.username, COUNT(*) as sms_count, SUM(c.user_payout) as payout FROM sms_cdr c "
        "JOIN users u ON c.user_id = u.id WHERE DATE_FORMAT(c.date_time, '%Y-%m') = ? "
        "AND u.parent_id = ? GROUP BY c.user_id, u.username ORDER BY sms_count DESC LIMIT 5",
        [this_month, uid]).fetchall()

    row = ctx.db.query(
        f"SELECT COUNT(*) as count, {payout_expr} as payout FROM sms_cdr "
        f"WHERE DATE(date_time) = ? AND {mine_or_clients}", [uid, _date(1), uid, uid]).fetch()
    stats["yesterday_sms"] = to_int(row["count"])
    stats["yesterday_payout"] = to_float(row["payout"])

    stats["recent_clients"] = ctx.db.query(
        "SELECT u.id, u.username, u.email, u.status, u.created_at, up.phone FROM users u "
        "LEFT JOIN user_profiles up ON u.id = up.user_id "
        "WHERE u.role = 'client' AND u.parent_id = ? ORDER BY u.created_at DESC LIMIT 5",
        [uid]).fetchall()


def client_stats(ctx: Ctx, stats: dict, today: str, this_month: str):
    uid = ctx.user_id

    stats["assigned_numbers"] = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM sms_numbers WHERE assigned_to = ?", [uid]).scalar())

    for key, sql, params in (
        ("today", "DATE(date_time) = ?", [today, uid]),
        ("last_7_days", "DATE(date_time) >= DATE_SUB(?, INTERVAL 7 DAY)", [today, uid]),
        ("last_30_days", "DATE(date_time) >= DATE_SUB(?, INTERVAL 30 DAY)", [today, uid]),
        ("yesterday", "DATE(date_time) = ?", [_date(1), uid]),
        ("month", "DATE_FORMAT(date_time, '%Y-%m') = ?", [this_month, uid]),
    ):
        row = ctx.db.query(
            f"SELECT COUNT(*) as count, COALESCE(SUM(user_payout), 0) as payout FROM sms_cdr "
            f"WHERE {sql} AND user_id = ?", params).fetch()
        stats[f"{key}_sms"] = to_int(row["count"])
        stats[f"{key}_payout"] = to_float(row["payout"])

    stats["balances"] = ctx.db.query(
        "SELECT currency, balance FROM user_balances WHERE user_id = ?", [uid]).fetch_key_pair()
    stats["available_ranges"] = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM sms_ranges WHERE status = 'active' "
        "AND available_numbers > 0").scalar())

    hourly = _pair(ctx.db.query(
        "SELECT HOUR(date_time) as hour, COUNT(*) as count FROM sms_cdr "
        "WHERE date_time >= DATE_SUB(NOW(), INTERVAL 6 HOUR) AND user_id = ? "
        "GROUP BY HOUR(date_time) ORDER BY hour", [uid]).fetchall())
    stats["hourly_trend"] = [
        to_int(hourly.get(str((datetime.utcnow() - timedelta(hours=i)).hour), 0))
        for i in range(5, -1, -1)
    ]

    daily = _pair(ctx.db.query(
        "SELECT DATE(date_time) as date, COUNT(*) as count FROM sms_cdr "
        "WHERE date_time >= DATE_SUB(?, INTERVAL 7 DAY) AND user_id = ? "
        "GROUP BY DATE(date_time) ORDER BY date", [today, uid]).fetchall())
    stats["daily_trend"] = [to_int(daily.get(_date(i), 0)) for i in range(6, -1, -1)]

    monthly = _pair(ctx.db.query(
        "SELECT DATE_FORMAT(date_time, '%Y-%m') as month, COUNT(*) as count FROM sms_cdr "
        "WHERE date_time >= DATE_SUB(?, INTERVAL 6 MONTH) AND user_id = ? "
        "GROUP BY DATE_FORMAT(date_time, '%Y-%m') ORDER BY month", [today, uid]).fetchall())
    stats["monthly_trend"] = [to_int(monthly.get(_month(i), 0)) for i in range(5, -1, -1)]

    stats["recent_ranges"] = ctx.db.query(
        "SELECT DISTINCT r.id, r.range_name, r.prefix, r.test_number, r.currency, r.payout_1_1 "
        "FROM sms_numbers n JOIN sms_ranges r ON r.id = n.range_id "
        "WHERE n.assigned_to = ? ORDER BY r.id DESC LIMIT 20", [uid]).fetchall()


def dashboard_stats(ctx: Ctx):
    stats: dict = {}
    today = _date()
    this_month = _month()

    if ctx.role == "manager":
        manager_stats(ctx, stats, today, this_month)
    elif ctx.role == "agent":
        agent_stats(ctx, stats, today, this_month)
    elif ctx.role == "client":
        client_stats(ctx, stats, today, this_month)

    stats["notifications"] = ctx.db.query(
        "SELECT id, title, message, type, is_read, created_at FROM notifications "
        "WHERE user_id = ? ORDER BY created_at DESC LIMIT 5", [ctx.user_id]).fetchall()
    stats["unread_notifications"] = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0",
        [ctx.user_id]).scalar())
    stats["news"] = ctx.db.query(
        "SELECT id, title, content, created_at FROM news "
        "WHERE status = 'published' AND (target_role = 'all' OR target_role = ?) "
        "ORDER BY created_at DESC LIMIT 5", [ctx.role]).fetchall()

    return json_response({"success": True, "stats": stats})


def chart_data(ctx: Ctx):
    period = ctx.q("period") or "7days"
    chart_type = ctx.q("type") or "sms"
    days = {"7days": 7, "30days": 30, "90days": 90}.get(period, 7)
    start_date = _date(days)
    end_date = _date()
    uid = ctx.user_id

    # Built here, not inherited from another function — this is the bug fix.
    scope = manager_owner_sql("user_id")
    agent_scope = ("(user_id = ? OR user_id IN "
                   "(SELECT id FROM users WHERE role='client' AND parent_id = ?))")
    agent_payout = "COALESCE(SUM(CASE WHEN user_id = ? THEN user_payout ELSE agent_payout END), 0)"

    if chart_type == "revenue":
        select, group = "currency, %s as revenue", "currency"
    elif chart_type == "types":
        select, group = "sms_type, COUNT(*) as count", "sms_type"
    else:
        select, group = "DATE(date_time) as date, COUNT(*) as count, %s as payout", "DATE(date_time)"

    if chart_type == "types":
        if ctx.role == "manager":
            rows = ctx.db.query(
                f"SELECT sms_type, COUNT(*) as count FROM sms_cdr "
                f"WHERE DATE(date_time) >= ? AND DATE(date_time) <= ? AND {scope} = ? "
                f"GROUP BY sms_type", [start_date, end_date, uid]).fetchall()
        elif ctx.role == "agent":
            rows = ctx.db.query(
                f"SELECT sms_type, COUNT(*) as count FROM sms_cdr "
                f"WHERE DATE(date_time) >= ? AND DATE(date_time) <= ? AND {agent_scope} "
                f"GROUP BY sms_type", [start_date, end_date, uid, uid]).fetchall()
        else:
            rows = ctx.db.query(
                "SELECT sms_type, COUNT(*) as count FROM sms_cdr "
                "WHERE DATE(date_time) >= ? AND DATE(date_time) <= ? AND user_id = ? "
                "GROUP BY sms_type", [start_date, end_date, uid]).fetchall()

    elif chart_type == "revenue":
        if ctx.role == "manager":
            rows = ctx.db.query(
                f"SELECT currency, SUM(my_payout) as revenue FROM sms_cdr "
                f"WHERE DATE(date_time) >= ? AND DATE(date_time) <= ? AND {scope} = ? "
                f"GROUP BY currency", [start_date, end_date, uid]).fetchall()
        elif ctx.role == "agent":
            rows = ctx.db.query(
                f"SELECT currency, {agent_payout} as revenue FROM sms_cdr "
                f"WHERE DATE(date_time) >= ? AND DATE(date_time) <= ? AND {agent_scope} "
                f"GROUP BY currency", [uid, start_date, end_date, uid, uid]).fetchall()
        else:
            rows = ctx.db.query(
                "SELECT currency, SUM(user_payout) as revenue FROM sms_cdr "
                "WHERE DATE(date_time) >= ? AND DATE(date_time) <= ? AND user_id = ? "
                "GROUP BY currency", [start_date, end_date, uid]).fetchall()

    else:
        if ctx.role == "manager":
            rows = ctx.db.query(
                f"SELECT DATE(date_time) as date, COUNT(*) as count, SUM(my_payout) as payout "
                f"FROM sms_cdr WHERE DATE(date_time) >= ? AND DATE(date_time) <= ? "
                f"AND {scope} = ? GROUP BY DATE(date_time) ORDER BY date",
                [start_date, end_date, uid]).fetchall()
        elif ctx.role == "agent":
            rows = ctx.db.query(
                f"SELECT DATE(date_time) as date, COUNT(*) as count, {agent_payout} as payout "
                f"FROM sms_cdr WHERE DATE(date_time) >= ? AND DATE(date_time) <= ? "
                f"AND {agent_scope} GROUP BY DATE(date_time) ORDER BY date",
                [uid, start_date, end_date, uid, uid]).fetchall()
        else:
            rows = ctx.db.query(
                "SELECT DATE(date_time) as date, COUNT(*) as count, SUM(user_payout) as payout "
                "FROM sms_cdr WHERE DATE(date_time) >= ? AND DATE(date_time) <= ? "
                "AND user_id = ? GROUP BY DATE(date_time) ORDER BY date",
                [start_date, end_date, uid]).fetchall()
        rows = _fill_date_series(rows, start_date, end_date)

    return json_response({"success": True, "data": rows,
                          "period": period, "type": chart_type})


@router.api_route("/api/dashboard.php", methods=["GET", "POST"])
@router.api_route("/api/dashboard", methods=["GET", "POST"])
async def dashboard_endpoint(request: Request, ctx: Ctx = Depends(get_auth_ctx)):
    action = ctx.q("action") or "stats"
    if action == "stats":
        return dashboard_stats(ctx)
    if action == "chart":
        return chart_data(ctx)
    return json_response({"error": "Invalid action"}, 400)
