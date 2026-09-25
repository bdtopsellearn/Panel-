"""
Legacy panel endpoints — port of public/ints/res_legacy.php.

Every /ints/<role>/res/<name>.php file in the PHP build was a one-line stub
that included res_legacy.php, which then switched on the filename. The same
shape is kept here: one route captures /ints/{role}/res/{name}.php and
dispatches on {name}, so none of the frontend JavaScript needs changing.

Responses use the old DataTables 1.9 envelope (sEcho/aaData) *and* the 1.10
one (draw/data) at the same time, exactly as the PHP did.
"""
from __future__ import annotations

import base64
import json
import logging
import re

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from core.context import Ctx, get_ctx
from core.helpers import (
    create_notification, esc, json_response, log_activity, manager_owner_sql,
    sanitize, to_float, to_int,
)
from api.numbers import PAY_COL, PAY_ENABLED_COL, PAY_TERMS

logger = logging.getLogger("g1t.legacy")
router = APIRouter()


def dt_out(rows=None, total=None):
    """DataTables envelope covering both the 1.9 and 1.10 key names."""
    rows = rows or []
    total = len(rows) if total is None else total
    return {"sEcho": 1, "iTotalRecords": total, "iTotalDisplayRecords": total,
            "aaData": rows, "draw": 1, "recordsTotal": total,
            "recordsFiltered": total, "data": rows}


def page_args(ctx: Ctx):
    params = ctx.all_params()
    start = max(0, to_int(params.get("iDisplayStart") or params.get("start"), 0))
    length = to_int(params.get("iDisplayLength") or params.get("length"), 25)
    if length < 1 or length > 2000:
        length = 25
    search = str(params.get("sSearch") or params.get("search[value]")
                 or params.get("search") or "").strip()
    return start, length, search


def cdr_scope(role: str, uid: int, params: list, alias: str = "c") -> str:
    if role == "manager":
        params.append(uid)
        return f"{manager_owner_sql(f'{alias}.user_id')}=?"
    if role == "agent":
        params += [uid, uid]
        return (f"({alias}.user_id=? OR {alias}.user_id IN "
                f"(SELECT id FROM users WHERE parent_id=?))")
    params.append(uid)
    return f"{alias}.user_id=?"


def strip_tags(value) -> str:
    return re.sub(r"<[^>]*>", "", str(value or ""))


def num(value, places: int = 4) -> str:
    return f"{to_float(value):,.{places}f}"


def plain(value, places: int = 4) -> str:
    """number_format(..., '.', '') — no thousands separator."""
    return f"{to_float(value):.{places}f}"


# ── select2 dropdown sources ────────────────────────────────────────────────
def aj_agents_clients(ctx: Ctx, name: str):
    uid, role = ctx.user_id, ctx.role
    want = "agent" if name == "aj_agents" else "client"
    q = str(ctx.q("q") or "").strip()
    page = max(1, ctx.q_int("page", 1))
    per_page = max(1, min(100, ctx.q_int("max", 25)))
    offset = (page - 1) * per_page

    if want == "agent":
        where, params = "u.role='agent' AND u.parent_id=? AND u.status='active'", [uid]
    elif role == "agent":
        where, params = "u.role='client' AND u.parent_id=? AND u.status='active'", [uid]
    else:
        where = ("u.role='client' AND u.parent_id IN "
                 "(SELECT id FROM users WHERE role='agent' AND parent_id=?) "
                 "AND u.status='active'")
        params = [uid]

    if q:
        where += " AND (u.username LIKE ? OR p.full_name LIKE ?)"
        params += [f"%{q}%"] * 2

    rows = ctx.db.query(
        f"SELECT u.id,u.username AS title FROM users u "
        f"LEFT JOIN user_profiles p ON p.user_id=u.id WHERE {where} "
        f"ORDER BY u.username LIMIT {offset},{per_page}", params).fetchall()
    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c FROM users u LEFT JOIN user_profiles p ON p.user_id=u.id "
        f"WHERE {where}", params).scalar())

    return {"results": rows, "pagination": {"more": (offset + per_page) < total}}


def aj_ranges(ctx: Ctx, name: str):
    uid, role = ctx.user_id, ctx.role
    q = str(ctx.q("q") or "").strip()
    page = max(1, ctx.q_int("page", 1))
    per_page = max(1, min(100, ctx.q_int("max", 25)))
    offset = (page - 1) * per_page
    params: list = []

    if role == "manager":
        where = "r.status='active'"
    else:
        where = ("r.status='active' AND r.id IN "
                 "(SELECT DISTINCT range_id FROM sms_numbers WHERE assigned_to=?)")
        params.append(uid)

    if name == "aj_smstestranges":
        where += " AND r.test_number IS NOT NULL AND r.test_number<>''"
    if q:
        where += " AND (r.range_name LIKE ? OR r.prefix LIKE ?)"
        params += [f"%{q}%"] * 2

    rows = ctx.db.query(
        f"SELECT r.id,r.range_name title FROM sms_ranges r WHERE {where} "
        f"ORDER BY r.range_name LIMIT {offset},{per_page}", params).fetchall()
    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c FROM sms_ranges r WHERE {where}", params).scalar())

    return {"results": rows, "pagination": {"more": (offset + per_page) < total}}


# ── data tables ─────────────────────────────────────────────────────────────
def data_clients(ctx: Ctx):
    uid, role = ctx.user_id, ctx.role
    start, length, search = page_args(ctx)

    if role == "manager":
        where, params = "u.role='agent' AND u.parent_id=?", [uid]
    elif role == "agent":
        where, params = "u.role='client' AND u.parent_id=?", [uid]
    else:
        return dt_out([], 0)

    if search:
        where += (" AND (u.username LIKE ? OR p.full_name LIKE ? OR u.email LIKE ? "
                  "OR p.phone LIKE ?)")
        params += [f"%{search}%"] * 4

    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c FROM users u LEFT JOIN user_profiles p ON p.user_id=u.id "
        f"WHERE {where}", params).scalar())

    rows = []
    href = "Agents.html#" if role == "manager" else "Clients.html#"
    for x in ctx.db.query(
        f"SELECT u.id,u.username,u.email,u.status,p.full_name,p.phone,p.address,p.company,"
        f"p.skype_id,p.country FROM users u LEFT JOIN user_profiles p ON p.user_id=u.id "
        f"WHERE {where} ORDER BY u.username LIMIT {start},{length}", params).fetchall():
        uid_row = to_int(x["id"])
        active = ("<span class='label label-success'>Yes</span>" if x["status"] == "active"
                  else "<span class='label label-important'>No</span>")
        # Keep the real DB id and the complete profile on the row, so the edit
        # modal can open even if the legacy edit AJAX endpoint is unavailable.
        payload = base64.b64encode(json.dumps({
            "id": uid_row, "username": x.get("username") or "", "email": x.get("email") or "",
            "status": x.get("status") or "active", "full_name": x.get("full_name") or "",
            "phone": x.get("phone") or "", "address": x.get("address") or "",
            "company": x.get("company") or "", "skype": x.get("skype_id") or "",
            "country": x.get("country") or "",
        }, ensure_ascii=False).encode()).decode()
        action = (f"<a href='{href}' id='view' info='{uid_row}' class='btn btn-mini btn-info'>"
                  f"<i class='icon-eye-open'></i></a> "
                  f"<a href='{href}' id='edit' info='{uid_row}' data-client='{payload}' "
                  f"class='btn btn-mini btn-warning'><i class='icon-edit'></i></a>")
        rows.append([f"<input type='checkbox' class='checkbox' value='{uid_row}'>",
                     esc(x["username"]), esc(x.get("full_name") or "-"),
                     esc(x.get("email") or "-"), esc(x.get("phone") or "-"),
                     esc(x.get("skype_id") or "-"), active, action])

    return dt_out(rows, total)


def data_smsnumbers(ctx: Ctx):
    uid, role = ctx.user_id, ctx.role
    start, length, search = page_args(ctx)
    params: list = []

    if role == "manager":
        where = (f"((n.assigned_to IS NULL AND n.status='available' AND r.status='active') "
                 f"OR {manager_owner_sql('n.assigned_to')}=?)")
        params.append(uid)
    elif role == "agent":
        where = ("(n.assigned_to=? OR n.assigned_to IN "
                 "(SELECT id FROM users WHERE parent_id=? AND role='client'))")
        params += [uid, uid]
    else:
        where = "n.assigned_to=?"
        params.append(uid)

    frange = ctx.q_int("frange")
    fclient = ctx.q_int("fclient")
    if frange:
        where += " AND n.range_id=?"
        params.append(frange)
    if fclient:
        where += " AND n.assigned_to=?"
        params.append(fclient)
    if search:
        where += " AND (n.number LIKE ? OR r.range_name LIKE ? OR u.username LIKE ?)"
        params += [f"%{search}%"] * 3

    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c FROM sms_numbers n JOIN sms_ranges r ON r.id=n.range_id "
        f"LEFT JOIN users u ON u.id=n.assigned_to WHERE {where}", params).scalar())

    # My SMS Numbers supports 10 / 25 / 50 / All.
    requested = to_int(ctx.all_params().get("iDisplayLength")
                       or ctx.all_params().get("length"), 25)
    if requested == -1:
        limit_sql = ""
    else:
        sms_len = requested if requested in (10, 25, 50) else 25
        limit_sql = f" LIMIT {start},{sms_len}"

    # Resolve the Agent's own client IDs directly, so the Client column reliably
    # shows the client's username for every number actually assigned to one.
    agent_client_ids = set()
    if role == "agent":
        agent_client_ids = {to_int(r["id"]) for r in ctx.db.query(
            "SELECT id FROM users WHERE parent_id=? AND role='client'", [uid]).fetchall()}

    rows = []
    for x in ctx.db.query(
        f"SELECT n.id,n.number,n.is_test,n.assigned_to,r.range_name,r.prefix,r.payout_1_1,"
        f"u.username FROM sms_numbers n JOIN sms_ranges r ON r.id=n.range_id "
        f"LEFT JOIN users u ON u.id=n.assigned_to WHERE {where} "
        f"ORDER BY r.range_name,n.number{limit_sql}", params).fetchall():
        pay = num(x.get("payout_1_1"))
        test = ' <span class="label label-important">Test</span>' if x.get("is_test") else ""
        if role == "client":
            rows.append([esc(x["range_name"]), esc(x["prefix"]), esc(x["number"]) + test,
                         "1/1", pay, "-"])
        else:
            # On an Agent page the Client column stays blank until the number is
            # actually assigned to one of that Agent's clients.
            if role == "agent" and to_int(x.get("assigned_to")) not in agent_client_ids:
                assigned_name = "-"
            else:
                assigned_name = x.get("username") or "-"
            rows.append([f"<input type='checkbox' class='checkbox' value='{to_int(x['id'])}'>",
                         esc(x["range_name"]), esc(x["prefix"]), esc(x["number"]) + test,
                         pay, esc(assigned_name), pay, "-"])

    return dt_out(rows, total)


def data_ranges_family(ctx: Ctx, name: str):
    uid, role = ctx.user_id, ctx.role
    start, length, search = page_args(ctx)

    # The Test role's SMS Test Numbers page uses the shared test inventory.
    if name == "data_smstestnumbers" and role == "test":
        params: list = []
        where = "n.is_test=1 AND n.status='available' AND r.status='active'"
        if search:
            where += " AND (n.number LIKE ? OR r.range_name LIKE ? OR r.prefix LIKE ?)"
            params += [f"%{search}%"] * 3
        total = to_int(ctx.db.query(
            f"SELECT COUNT(*) c FROM sms_numbers n JOIN sms_ranges r ON r.id=n.range_id "
            f"WHERE {where}", params).scalar())
        rows = [[esc(x["range_name"]), esc(x["prefix"]), esc(x["number"]),
                 x.get("payout_1_1") if x.get("payout_1_1") is not None else "-", "-"]
                for x in ctx.db.query(
                    f"SELECT n.number, r.range_name, r.prefix, r.payout_1_1 "
                    f"FROM sms_numbers n JOIN sms_ranges r ON r.id=n.range_id "
                    f"WHERE {where} ORDER BY r.range_name,n.number LIMIT {start},{length}",
                    params).fetchall()]
        return dt_out(rows, total)

    params = []
    if role == "manager":
        where = "1=1"
    elif role == "agent":
        where = "r.status='active'"
    else:
        where = ("r.status='active' AND r.id IN "
                 "(SELECT DISTINCT range_id FROM sms_numbers WHERE assigned_to=?)")
        params.append(uid)

    if name == "data_smstestnumbers":
        where += " AND r.test_number IS NOT NULL AND r.test_number<>''"
    if search:
        where += " AND (r.range_name LIKE ? OR r.prefix LIKE ?)"
        params += [f"%{search}%"] * 2

    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c FROM sms_ranges r WHERE {where}", params).scalar())

    rows = []
    for x in ctx.db.query(
        f"SELECT r.* FROM sms_ranges r WHERE {where} ORDER BY r.range_name "
        f"LIMIT {start},{length}", params).fetchall():
        def p(key):
            value = x.get(key)
            return value if value is not None else "-"
        p11, p71, p77, p3045 = p("payout_1_1"), p("payout_7_1"), p("payout_7_7"), p("payout_30_45")

        if name == "data_smstestnumbers":
            rows.append([esc(x["range_name"]), esc(x["prefix"]),
                         esc(x.get("test_number") or "-"), p11, "-"])
        elif name == "data_smsratecard":
            rows.append([esc(x["range_name"]), esc(x["prefix"]),
                         esc(x.get("test_number") or "-"), esc(x["currency"]),
                         p11, p71, p77, "-", "-", "-", "-", p3045, "-"])
        elif role == "manager":
            rows.append([esc(x["range_name"]), esc(x["prefix"]),
                         f"{to_int(x.get('available_numbers')):,}/"
                         f"{to_int(x.get('total_numbers')):,}",
                         esc(x.get("test_number") or "-"), esc(x["currency"]),
                         p11, p71, p77, p3045, esc(x.get("memo") or "-"), "-"])
        else:
            request_enabled = ("request_enabled" not in x
                               or to_int(x.get("request_enabled")) == 1)
            available = to_int(x.get("available_numbers"))
            if role == "agent":
                action = ("<span class='label label-important'>Request Off</span>"
                          if not request_enabled else
                          f"<a href='#' id='request' info='{to_int(x['id'])}' "
                          f"class='btn btn-mini btn-info'>Request</a>")
                rows.append([esc(x["range_name"]), esc(x["prefix"]),
                             esc(x.get("test_number") or "-"), esc(x["currency"]),
                             p11, p71, p77, p3045, esc(x.get("memo") or "-"), action])
            else:
                rows.append([esc(x["range_name"]), esc(x["prefix"]), f"{available:,}",
                             esc(x.get("test_number") or "-"), esc(x["currency"]),
                             p11, p71, p77, p3045, esc(x.get("memo") or "-"), "-"])

    return dt_out(rows, total)


def data_news(ctx: Ctx):
    uid, role = ctx.user_id, ctx.role
    start, length, _ = page_args(ctx)
    if role in ("manager", "agent"):
        where, params = "n.author_id=?", [uid]
    else:
        where = "n.status='published' AND (n.target_role='all' OR n.target_role=?)"
        params = [role]

    for key, op in (("fdate1", ">="), ("fdate2", "<=")):
        value = str(ctx.q(key) or "").strip()
        if value:
            where += f" AND n.created_at{op}?"
            params.append(value)

    total = to_int(ctx.db.query(f"SELECT COUNT(*) c FROM news n WHERE {where}", params).scalar())
    rows = []
    for x in ctx.db.query(
        f"SELECT n.* FROM news n WHERE {where} ORDER BY n.created_at DESC "
        f"LIMIT {start},{length}", params).fetchall():
        msg = esc(x["content"])
        rows.append([f"<input type='checkbox' class='checkbox' value='{to_int(x['id'])}'>",
                     esc(x.get("published_at") or x.get("created_at")), esc(x["title"]),
                     strip_tags(x["content"])[:100],
                     f"<a href='#' id='view' data='{msg}' class='btn btn-mini btn-info'>View</a>"])
    return dt_out(rows, total)


def data_myactivity(ctx: Ctx):
    start, length, search = page_args(ctx)
    where, params = "a.user_id=?", [ctx.user_id]
    for key, op in (("fdate1", ">="), ("fdate2", "<=")):
        value = str(ctx.q(key) or "").strip()
        if value:
            where += f" AND a.created_at{op}?"
            params.append(value)
    if search:
        where += " AND (a.action LIKE ? OR a.description LIKE ?)"
        params += [f"%{search}%"] * 2

    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c FROM user_activity a WHERE {where}", params).scalar())
    rows = [[esc(x["created_at"]), esc(x["action"]), esc(x.get("description") or "-"),
             esc(x.get("ip_address") or "-")]
            for x in ctx.db.query(
                f"SELECT * FROM user_activity a WHERE {where} ORDER BY created_at DESC "
                f"LIMIT {start},{length}", params).fetchall()]
    return dt_out(rows, total)


def data_notifications(ctx: Ctx):
    start, length, _ = page_args(ctx)
    where, params = "user_id=?", [ctx.user_id]
    for key, op in (("fdate1", ">="), ("fdate2", "<=")):
        value = str(ctx.q(key) or "").strip()
        if value:
            where += f" AND created_at{op}?"
            params.append(value)

    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c FROM notifications WHERE {where}", params).scalar())
    rows = []
    for x in ctx.db.query(
        f"SELECT * FROM notifications WHERE {where} ORDER BY created_at DESC "
        f"LIMIT {start},{length}", params).fetchall():
        msg = esc(x["message"])
        rows.append([esc(x["created_at"]), esc(x["title"]),
                     f"<a href='#' id='view' info='{to_int(x['id'])}' data='{msg}'>"
                     f"{strip_tags(x['message'])[:80]}</a>"])
    return dt_out(rows, total)


def data_paymentrequests(ctx: Ctx):
    uid, role = ctx.user_id, ctx.role
    start, length, _ = page_args(ctx)
    if role == "manager":
        where = ("(p.user_id=? OR p.user_id IN (SELECT id FROM users WHERE parent_id=? "
                 "OR parent_id IN (SELECT id FROM users WHERE parent_id=?)))")
        params = [uid, uid, uid]
    else:
        where, params = "p.user_id=?", [uid]

    for key, op in (("fdate1", ">="), ("fdate2", "<=")):
        value = str(ctx.q(key) or "").strip()
        if value:
            where += f" AND p.created_at{op}?"
            params.append(value)

    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c FROM payment_requests p WHERE {where}", params).scalar())
    rows = [[esc(x["created_at"]), esc(x["currency"]), num(x["amount"], 2), esc(x["status"]),
             esc(x.get("method") or "-"), esc(x.get("details") or "-"),
             num(x["amount"], 2) if x["status"] == "completed" else "0.00", "-",
             esc(x.get("processed_at") or x.get("updated_at"))]
            for x in ctx.db.query(
                f"SELECT p.* FROM payment_requests p WHERE {where} "
                f"ORDER BY created_at DESC LIMIT {start},{length}", params).fetchall()]
    return dt_out(rows, total)


def data_creditnotes(ctx: Ctx):
    uid, role = ctx.user_id, ctx.role
    start, length, _ = page_args(ctx)
    if role == "manager":
        where = ("(c.user_id=? OR c.user_id IN (SELECT id FROM users WHERE parent_id=? "
                 "OR parent_id IN (SELECT id FROM users WHERE parent_id=?)))")
        params = [uid, uid, uid]
    else:
        where, params = "c.user_id=?", [uid]

    for key, op in (("fdate1", ">="), ("fdate2", "<=")):
        value = str(ctx.q(key) or "").strip()
        if value:
            where += f" AND c.created_at{op}?"
            params.append(value)

    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c FROM credit_notes c WHERE {where}", params).scalar())
    rows = [[esc(x["created_at"]), esc(x.get("username") or "-"), esc(x["type"]),
             esc(x["currency"]), num(x["amount"]), "-", "Completed", "-"]
            for x in ctx.db.query(
                f"SELECT c.*,u.username FROM credit_notes c "
                f"LEFT JOIN users u ON u.id=c.user_id WHERE {where} "
                f"ORDER BY c.created_at DESC LIMIT {start},{length}", params).fetchall()]
    return dt_out(rows, total)


def data_stats_family(ctx: Ctx, name: str):
    uid, role = ctx.user_id, ctx.role
    start, length, _ = page_args(ctx)
    params: list = []
    scope = cdr_scope(role, uid, params, "c")

    # Role-aware payout expressions. A client CDR stores the Agent override in
    # agent_payout; an Agent-owned CDR stores the Agent payout in user_payout.
    if role == "agent":
        my_expr = "CASE WHEN u.role='client' THEN c.agent_payout ELSE c.user_payout END"
        out_expr = "CASE WHEN u.role='client' THEN c.user_payout ELSE 0 END"
    elif role == "client":
        my_expr, out_expr = "c.user_payout", "0"
    else:
        my_expr = "c.my_payout"
        out_expr = "CASE WHEN u.role='client' THEN c.agent_payout ELSE c.user_payout END"

    if name == "data_smsagentstats" and role == "manager":
        # Group client traffic under its parent Agent so the Manager's Agent
        # report does not show Client usernames as Agents.
        group = ("CASE WHEN u.role='client' THEN u.parent_id ELSE u.id END, "
                 "CASE WHEN u.role='client' THEN pu.username ELSE u.username END, c.currency")
        select = "CASE WHEN u.role='client' THEN pu.username ELSE u.username END label"
        fagent = ctx.q_int("fagent")
        if fagent:
            scope += (" AND (CASE WHEN u.role='client' THEN u.parent_id "
                      "ELSE u.id END)=?")
            params.append(fagent)
    elif name == "data_smsclientstats" and role == "agent":
        scope += " AND u.role='client' AND u.parent_id=?"
        params.append(uid)
        group, select = "c.user_id,u.username,c.currency", "u.username label"
        fclient = ctx.q_int("fclient")
        if fclient:
            scope += " AND c.user_id=?"
            params.append(fclient)
    elif name == "data_smsrangestats":
        group, select = "c.range_id,r.range_name,c.currency", "r.range_name label"
    elif name == "data_smsnumberstats":
        group, select = "c.number,c.currency", "c.number label"
    else:
        group, select = "c.user_id,u.username,c.currency", "u.username label"

    rows = [[esc(x.get("label") or "-"), to_int(x["sms"]), esc(x["currency"]),
             num(x["myp"]), num(x["up"])]
            for x in ctx.db.query(
                f"SELECT {select},c.currency,SUM(c.sms_count) sms,SUM({my_expr}) myp,"
                f"SUM({out_expr}) up FROM sms_cdr c "
                f"LEFT JOIN sms_ranges r ON r.id=c.range_id "
                f"LEFT JOIN users u ON u.id=c.user_id "
                f"LEFT JOIN users pu ON pu.id=u.parent_id "
                f"WHERE {scope} GROUP BY {group} ORDER BY sms DESC "
                f"LIMIT {start},{length}", params).fetchall()]
    return dt_out(rows, len(rows))


CDR_JOINS = (" FROM sms_cdr c LEFT JOIN sms_ranges r ON r.id=c.range_id "
             "LEFT JOIN users u ON u.id=c.user_id "
             "LEFT JOIN users pu ON pu.id=u.parent_id ")


def data_cdr_family(ctx: Ctx, name: str):
    uid, role = ctx.user_id, ctx.role
    start, length, search = page_args(ctx)
    params: list = []
    where = cdr_scope(role, uid, params, "c")
    if name == "data_testsmscdr":
        where += " AND c.sms_type='test'"

    fdate1 = str(ctx.q("fdate1") or "").strip()
    fdate2 = str(ctx.q("fdate2") or "").strip()
    frange = ctx.q_int("frange")
    fuser = ctx.q_int("fagent" if role == "manager" else "fclient")
    fnum = str(ctx.q("fnum") or "").strip()
    fcli = str(ctx.q("fcli") or "").strip()

    if fdate1:
        where += " AND c.date_time>=?"
        params.append(fdate1)
    if fdate2:
        where += " AND c.date_time<=?"
        params.append(fdate2)
    if frange:
        where += " AND c.range_id=?"
        params.append(frange)
    if fuser:
        if role == "manager":
            where += " AND (CASE WHEN u.role='client' THEN u.parent_id ELSE u.id END)=?"
        else:
            where += " AND c.user_id=?"
        params.append(fuser)
    if fnum:
        where += " AND c.number LIKE ?"
        params.append(f"%{fnum}%")
    if fcli:
        where += " AND c.cli LIKE ?"
        params.append(f"%{fcli}%")
    if search:
        where += (" AND (c.number LIKE ? OR c.cli LIKE ? OR r.range_name LIKE ? "
                  "OR u.username LIKE ? OR pu.username LIKE ?)")
        params += [f"%{search}%"] * 5

    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c {CDR_JOINS} WHERE {where}", params).scalar())

    view = str(ctx.q("view") or "reports")
    rows = []
    for x in ctx.db.query(
        f"SELECT c.*,r.range_name,u.username,u.role user_role,pu.username parent_username "
        f"{CDR_JOINS} WHERE {where} ORDER BY c.date_time DESC LIMIT {start},{length}",
        params).fetchall():
        # "SMS" column shows the actual message text when we have it; older
        # records saved before message text was captured fall back to the count.
        sms_cell = esc(x["message"]) if x.get("message") else to_int(x["sms_count"])

        if name == "data_testsmscdr":
            rows.append([esc(x["date_time"]), esc(x.get("range_name") or "-"),
                         esc(x["number"]), esc(x.get("cli") or "-"), sms_cell])
            continue

        if role == "client":
            rows.append([esc(x["date_time"]), esc(x.get("range_name") or "-"), esc(x["number"]),
                         esc(x.get("cli") or "-"), sms_cell, esc(x["currency"]),
                         num(x["user_payout"])])
        elif role == "agent":
            is_client = x.get("user_role") == "client"
            client_name = (x.get("username") or "-") if is_client else "-"
            my_payout = to_float(x["agent_payout"]) if is_client else to_float(x["user_payout"])
            client_payout = to_float(x["user_payout"]) if is_client else 0.0
            rows.append([esc(x["date_time"]), esc(x.get("range_name") or "-"), esc(x["number"]),
                         esc(x.get("cli") or "-"), esc(client_name), sms_cell,
                         esc(x["currency"]), num(my_payout), num(client_payout)])
        else:
            is_client = x.get("user_role") == "client"
            agent_name = (x.get("parent_username") or "-") if is_client else (x.get("username") or "-")
            agent_payout = to_float(x["agent_payout"]) if is_client else to_float(x["user_payout"])
            if view == "stats":
                rows.append([esc(x["date_time"]), esc(x.get("range_name") or "-"),
                             esc(x["number"]), esc(x.get("cli") or "-"), esc(agent_name),
                             sms_cell, esc(x["currency"]),
                             num(x["my_payout"]), num(agent_payout)])
            else:
                rows.append([esc(x["date_time"]), esc(x.get("range_name") or "-"),
                             esc(x["number"]), esc(x.get("cli") or "-"), esc(agent_name),
                             sms_cell, esc(x["sms_type"]), esc(x["currency"]),
                             num(x["my_payout"]), num(agent_payout)])

    # The legacy CDR pages expect one hidden summary row at the end of aaData.
    # Supplying it prevents the UI from treating the last real CDR as totals.
    if name == "data_smscdr":
        agg = ctx.db.query(
            f"SELECT c.currency, SUM(c.sms_count) sms, SUM(c.my_payout) manager_in, "
            f"SUM(CASE WHEN u.role='client' THEN c.agent_payout ELSE c.user_payout END) manager_out, "
            f"SUM(CASE WHEN u.role='client' THEN c.agent_payout ELSE c.user_payout END) agent_in, "
            f"SUM(CASE WHEN u.role='client' THEN c.user_payout ELSE 0 END) agent_out, "
            f"SUM(c.user_payout) client_in, SUM(c.profit) stored_profit "
            f"{CDR_JOINS} WHERE {where} GROUP BY c.currency", params).fetchall()

        cur = {c: {"sms": 0, "in": 0.0, "out": 0.0, "profit": 0.0}
               for c in ("USD", "EUR", "GBP")}
        all_sms = 0
        for a in agg:
            code = a["currency"]
            if code not in cur:
                continue
            sms = to_int(a["sms"])
            all_sms += sms
            cur[code]["sms"] = sms
            if role == "manager":
                cur[code]["in"] = to_float(a["manager_in"])
                cur[code]["out"] = to_float(a["manager_out"])
                cur[code]["profit"] = to_float(a["stored_profit"])
            elif role == "agent":
                cur[code]["in"] = to_float(a["agent_in"])
                cur[code]["out"] = to_float(a["agent_out"])
                cur[code]["profit"] = cur[code]["in"] - cur[code]["out"]
            else:
                cur[code]["in"] = to_float(a["client_in"])

        if role == "client":
            summary = [plain(cur[c]["in"]) for c in ("USD", "EUR", "GBP")] + [str(all_sms)]
            ncols = 7
        else:
            summary = [plain(cur[c]["in"]) for c in ("USD", "EUR", "GBP")]
            summary += [plain(cur[c]["out"]) for c in ("USD", "EUR", "GBP")]
            summary += [plain(cur[c]["profit"]) for c in ("USD", "EUR", "GBP")]
            for c in ("USD", "EUR", "GBP"):
                pct = (cur[c]["profit"] / cur[c]["in"] * 100) if cur[c]["in"] else 0
                summary.append(f"{pct:.2f}")
            summary.append(str(all_sms))
            ncols = 10 if (role == "manager" and view != "stats") else 9

        hidden = [",".join(summary)] + [""] * max(0, ncols - 1)
        rows.append(hidden)

    return dt_out(rows, total)


def data_smsbulkallocations(ctx: Ctx):
    start, length, _ = page_args(ctx)
    where, params = "a.user_id=? AND a.action='bulk_allocate'", [ctx.user_id]
    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c FROM user_activity a WHERE {where}", params).scalar())
    rows = []
    for x in ctx.db.query(
        f"SELECT a.id,a.created_at,a.description FROM user_activity a WHERE {where} "
        f"ORDER BY a.created_at DESC LIMIT {start},{length}", params).fetchall():
        try:
            payload = json.loads(x["description"] or "{}")
            if not isinstance(payload, dict):
                payload = {}
        except Exception:
            payload = {}
        names = [t["username"] for t in payload.get("targets", []) if t.get("username")]
        rows.append([esc(x["created_at"]), esc(", ".join(names) if names else "-"),
                     to_int(payload.get("qty_each")), to_int(payload.get("total")),
                     f"<a class='btn btn-mini btn-info' "
                     f"href='res/downloadbulk.php?id={to_int(x['id'])}'>Download</a>"])
    return dt_out(rows, total)


async def read_notifications(ctx: Ctx):
    body = await ctx.body()
    notification_id = to_int(body.get("id") or ctx.q("id"))
    if notification_id:
        ctx.db.query("UPDATE notifications SET is_read=1 WHERE id=? AND user_id=?",
                     [notification_id, ctx.user_id])
    return {"success": True}


def _assign_all_error_html(message: str) -> str:
    return f'<div class="alert alert-danger">{esc(message)}</div>'


async def assign_all_sms_numbers(ctx: Ctx):
    """GET/POST res/assignallsmsnumber.php — port of Power SMS RTX's number
    allocation system for BOTH roles:
    - Manager -> Agent: standalone manager/res/assignallsmsnumber.php,
      with Agent + Payterm selection and a live payout-rate preview.
    - Agent -> Client: the agent branch of res_actions.php's shared
      'assignallsmsnumber' case — reassigns numbers already held by the
      Agent to one of their own Clients (no Payterm; rate stays as-is)."""
    if ctx.role not in ("manager", "agent"):
        return _assign_all_error_html("Manager or Agent login required.")

    is_manager = ctx.role == "manager"
    child_role = "agent" if is_manager else "client"
    child_label = "Agent" if is_manager else "Client"
    target_field = "agent_id" if is_manager else "client_id"

    body = await ctx.body()
    owner_id = ctx.user_id

    # ── SAVE ASSIGNMENT ─────────────────────────────────────────────────
    if str(body.get("save") or "") in ("1", "true", "on"):
        target_id = to_int(body.get(target_field))
        ids = sorted({to_int(x) for x in str(body.get("ids") or "").split(",") if to_int(x)})

        if not target_id:
            return _assign_all_error_html(f"Please select a {child_label}.")
        if not ids:
            return _assign_all_error_html("Please select at least one number.")

        target = ctx.db.query(
            "SELECT id, username FROM users WHERE id=? AND role=? "
            "AND parent_id=? AND status='active' LIMIT 1",
            [target_id, child_role, owner_id]).fetch()
        if not target:
            return _assign_all_error_html(f"Invalid {child_label}.")

        placeholders = ",".join("?" * len(ids))
        pay_term = ""

        if is_manager:
            pay_term = sanitize(body.get("pay_term") or "")
            if pay_term not in PAY_COL:
                return _assign_all_error_html("Please select a Payterm.")
            col = PAY_COL[pay_term]
            owner_expr = manager_owner_sql("n.assigned_to")
            try:
                with ctx.db.transaction() as tx:
                    # Allow (re)allocation of numbers that are either
                    # unassigned, or already assigned but owned within this
                    # manager's own hierarchy. Numbers owned by a different
                    # manager stay protected.
                    result = tx.query(
                        f"UPDATE sms_numbers n JOIN sms_ranges r ON r.id=n.range_id "
                        f"SET n.assigned_to=?, n.assigned_at=UTC_TIMESTAMP(), "
                        f"n.status='assigned', n.pay_term=?, n.payout_rate=r.{col} "
                        f"WHERE n.id IN ({placeholders}) AND r.status='active' "
                        f"AND (n.assigned_to IS NULL OR {owner_expr}=?)",
                        [target_id, pay_term, *ids, owner_id])
                    assigned_count = to_int(result.rowcount)
            except Exception as exc:
                logger.warning("assignallsmsnumber save error: %s", exc)
                return _assign_all_error_html("Assignment failed.")
            if assigned_count < 1:
                return _assign_all_error_html(
                    "These numbers belong to another Manager or could not be "
                    "found. Refresh and try again.")
        else:
            try:
                with ctx.db.transaction() as tx:
                    # An Agent may only reassign numbers currently assigned
                    # to themself, to one of their own active Clients.
                    result = tx.query(
                        f"UPDATE sms_numbers SET assigned_to=?, assigned_at=UTC_TIMESTAMP(), "
                        f"status='assigned' WHERE id IN ({placeholders}) AND assigned_to=?",
                        [target_id, *ids, owner_id])
                    assigned_count = to_int(result.rowcount)
            except Exception as exc:
                logger.warning("assignallsmsnumber save error: %s", exc)
                return _assign_all_error_html("Assignment failed.")
            if assigned_count < 1:
                return _assign_all_error_html(
                    "These numbers are not currently assigned to you. "
                    "Refresh and try again.")

        create_notification(target_id, "Numbers Assigned",
                            "You have been assigned numbers", "success")
        log_activity(owner_id, "numbers_assigned",
                     f"Assigned numbers to user: {target['username']}")

        payterm_line = f'Payterm: <strong>{esc(pay_term)}</strong><br>' if pay_term else ""
        return (
            '<div style="padding:25px">'
            '<div class="alert alert-success">'
            f'<strong>Success!</strong><br>{assigned_count} number(s) assigned to '
            f'<strong>{esc(target["username"])}</strong><br>'
            f'{payterm_line}'
            '</div>'
            '<button type="button" class="btn btn-primary" '
            'data-dismiss="modal" onclick="window.location.reload();">Done</button>'
            '</div>'
        )

    # ── OPEN ALLOCATE MODAL ─────────────────────────────────────────────
    selected = sorted({to_int(x) for x in str(body.get("ids") or "").split(",") if to_int(x)})
    if not selected:
        return _assign_all_error_html("Please select at least one number.")

    placeholders = ",".join("?" * len(selected))
    if is_manager:
        num_rows = ctx.db.query(
            f"SELECT n.id, n.number, n.range_id FROM sms_numbers n "
            f"WHERE n.id IN ({placeholders}) ORDER BY n.number", selected).fetchall()
    else:
        # An Agent only ever sees/allocates numbers already assigned to them.
        num_rows = ctx.db.query(
            f"SELECT n.id, n.number, n.range_id FROM sms_numbers n "
            f"WHERE n.id IN ({placeholders}) AND n.assigned_to=? ORDER BY n.number",
            [*selected, owner_id]).fetchall()
    if not num_rows:
        return _assign_all_error_html("Selected numbers not found.")

    num_list = ", ".join(str(r["number"]) for r in num_rows)
    id_list = ",".join(str(to_int(r["id"])) for r in num_rows)
    range_ids = sorted({to_int(r["range_id"]) for r in num_rows})

    children = ctx.db.query(
        "SELECT id, username FROM users WHERE role=? AND parent_id=? "
        "AND status='active' ORDER BY username ASC", [child_role, owner_id]).fetchall()

    child_options = ['<option value="">Please Select</option>']
    for c in children:
        child_options.append(f'<option value="{to_int(c["id"])}">{esc(c["username"])}</option>')

    payterm_block = ""
    payterm_script = ""
    if is_manager:
        rate_row = None
        if len(range_ids) == 1:
            rate_row = ctx.db.query(
                "SELECT payout_1_1, payout_7_1, payout_7_7, payout_30_45 "
                "FROM sms_ranges WHERE id=? LIMIT 1", [range_ids[0]]).fetch()

        payterm_options = []
        for term in PAY_TERMS:
            col = PAY_COL[term]
            rate = rate_row.get(col) if rate_row else None
            if rate is not None and str(rate) != "":
                payterm_options.append(
                    f'<option value="{term}" data-rate="{to_float(rate):.6f}">'
                    f'{term} - {to_float(rate):.6f}</option>')
            else:
                payterm_options.append(f'<option value="{term}" data-rate="">{term} -</option>')

        multi_range_note = (
            '<p style="font-size:12px;color:#888">Selected numbers span multiple '
            "ranges - the correct payout for each number's own range is applied "
            'automatically when you allocate.</p>' if len(range_ids) > 1 else ""
        )

        payterm_block = (
            '<div class="control-group" style="margin-top:18px;">'
            '<label><strong>Payterm</strong></label>'
            '<select name="pay_term" id="assignPayTermSelect" class="input-xlarge" '
            f'style="width:100%;" required><option value="">Please Select</option>'
            f'{"".join(payterm_options)}</select>'
            '</div>'
            '<div class="control-group" style="margin-top:18px;">'
            '<label><strong>Payout</strong></label>'
            '<input type="text" id="assignPayoutDisplay" value="" readonly '
            'style="width:100%;background:#eee">'
            '</div>'
            f'{multi_range_note}'
        )
        payterm_script = (
            "$('#assignPayTermSelect').off('change.assignPreview').on('change.assignPreview', function(){"
            "var rate = $(this).find('option:selected').data('rate');"
            "$('#assignPayoutDisplay').val(rate ? rate : '');"
            "});"
        )

    return (
        '<form method="post" id="autoAssignNumbers" action="res/assignallsmsnumber.php">'
        '<input type="hidden" name="save" value="1">'
        f'<input type="hidden" name="ids" value="{esc(id_list)}">'
        '<div class="modal-header">'
        '<button type="button" class="close" data-dismiss="modal">&times;</button>'
        '<h3>Allocate All Numbers</h3>'
        '</div>'
        '<div class="modal-body">'
        '<div class="control-group">'
        '<label><strong>Numbers</strong></label>'
        '<p style="max-height:140px;overflow:auto;background:#f7f7f7;padding:8px;'
        f'border:1px solid #ddd">{esc(num_list)}</p>'
        '</div>'
        '<div class="control-group">'
        f'<label><strong>Select {esc(child_label)}</strong></label>'
        f'<select name="{target_field}" id="assignAgentSelect" class="agentListSelect" '
        f'style="width:100%;" required>{"".join(child_options)}</select>'
        '</div>'
        f'{payterm_block}'
        '</div>'
        '<div class="modal-footer">'
        '<button type="button" class="btn" data-dismiss="modal">Close</button>'
        '<button type="submit" name="save" value="1" class="btn btn-primary">Allocate</button>'
        '</div>'
        '</form>'
        '<script>'
        '(function(){'
        'function boot(){'
        "if (typeof jQuery === 'undefined') { return; }"
        "var $ = jQuery;"
        f"{payterm_script}"
        "if (typeof $.fn.select2 === 'function' && !$('#assignAgentSelect').data('select2')) {"
        "var $sel = $('#assignAgentSelect');"
        f"$sel.select2({{width:'100%', placeholder:'Select {child_label}', allowClear:true, dropdownParent: $sel.closest('.modal')}});"
        "$sel.on('select2:open', function () {"
        "var focusField = function(){"
        "var $field = $('.select2-container--open .select2-search__field, .select2-search__field');"
        "if ($field.length) { $field[0].focus(); }"
        "};"
        "focusField();"
        "setTimeout(focusField, 30);"
        "setTimeout(focusField, 100);"
        "});"
        "}"
        "}"
        "if (typeof jQuery !== 'undefined') { boot(); }"
        "else { var tries=0; var t=setInterval(function(){ tries++; "
        "if (typeof jQuery !== 'undefined') { clearInterval(t); boot(); } "
        "else if (tries > 40) { clearInterval(t); } }, 100); }"
        '})();'
        '</script>'
    )


# ── dispatch ────────────────────────────────────────────────────────────────
RANGE_FAMILY = {"data_smsranges", "data_smsratecard", "data_smstestnumbers"}
STATS_FAMILY = {"data_smsrangestats", "data_smsagentstats",
                "data_smsclientstats", "data_smsnumberstats"}
CDR_FAMILY = {"data_smscdr", "data_testsmscdr"}


PAY_TERM_LABELS = {"1/1": "Daily (1/1)", "7/1": "Weekly Payout, Daily SMS (7/1)",
                    "7/7": "Weekly (7/7)", "30/45": "Monthly (30/45)"}


def _request_form_html(rid: int, error: str = "") -> str:
    """Builds the 'Request Numbers' modal (header+body+footer) as one HTML
    blob — the frontend replaces div#requestm's entire innerHTML with this."""
    error_html = (f'<div class="alert alert-error" style="margin:0 0 15px;">{esc(error)}</div>'
                  if error else "")
    return (
        '<div class="modal-header">'
        '<button type="button" class="close" data-dismiss="modal">&times;</button>'
        '<h4>Request Numbers</h4>'
        '</div>'
        '<div class="modal-body">'
        f'{error_html}'
        f'<input type="hidden" id="rid" value="{to_int(rid)}">'
        '<div class="form-group">'
        '<label>Payment Term</label>'
        '<select id="payterm" class="form-control">'
        '<option value="">Please Select a payterm</option>'
        '__PAYTERM_OPTIONS__'
        '</select>'
        '</div>'
        '<div class="form-group">'
        '<label>Quantity</label>'
        '<input type="number" id="qty" class="form-control" value="5" min="1" max="200">'
        '</div>'
        '<div id="nres"></div>'
        '</div>'
        '<div class="modal-footer">'
        '<a href="#" class="btn" data-dismiss="modal">Close</a>'
        '<button type="button" id="requestnum" class="btn btn-primary">'
        'Request <span id="spinner" style="display:none;">...</span></button>'
        '</div>'
    )


async def request_numbers_form(ctx: Ctx):
    """GET/POST res/requestsmsnumber.php — returns the modal markup with the
    Payment Term dropdown built from this range's enabled/priced terms."""
    if ctx.role != "agent":
        return _request_form_html(0, "Only Agents can request numbers.")

    rid = ctx.q_int("rid") or to_int((await ctx.body()).get("rid"))
    rng = ctx.db.query(
        "SELECT r.* FROM sms_ranges r "
        "JOIN users a ON a.id=? AND a.role='agent' AND a.status='active' "
        "JOIN users m ON m.id=a.parent_id AND m.role='manager' AND m.status='active' "
        "WHERE r.id=? AND r.status='active' LIMIT 1", [ctx.user_id, rid]).fetch()
    if not rng:
        return _request_form_html(rid, "Range unavailable.")
    if to_int(rng.get("request_enabled", 1)) != 1:
        return _request_form_html(rid, "Admin has disabled requests for this range.")

    options = []
    for term in PAY_TERMS:
        rate = rng.get(PAY_COL[term])
        enabled_col = PAY_ENABLED_COL[term]
        if rate is None or (enabled_col in rng and to_int(rng[enabled_col]) != 1):
            continue
        options.append(f'<option value="{term}">{esc(PAY_TERM_LABELS[term])} '
                        f'(Payout - $ {to_float(rate):.6f})</option>')

    html = _request_form_html(rid).replace(
        "__PAYTERM_OPTIONS__", "".join(options) or "")
    return html


async def request_numbers_final(ctx: Ctx):
    """POST res/requestsmsnumberfinal.php — validates the daily quota and
    instantly allocates `qty` available numbers from the range to this Agent."""
    if ctx.role != "agent":
        return '<span class="text-error">Only Agents can request numbers.</span>'

    body = await ctx.body()
    rid = to_int(body.get("rid"))
    pay_term = sanitize(body.get("payterm") or "")
    qty = to_int(body.get("qty"))

    if not rid or pay_term not in PAY_TERMS or qty < 1 or qty > 200:
        return '<span class="text-error">Please select Payment Term and Quantity (1-200).</span>'

    rng = ctx.db.query(
        "SELECT r.* FROM sms_ranges r "
        "JOIN users a ON a.id=? AND a.role='agent' AND a.status='active' "
        "JOIN users m ON m.id=a.parent_id AND m.role='manager' AND m.status='active' "
        "WHERE r.id=? AND r.status='active' LIMIT 1", [ctx.user_id, rid]).fetch()
    if not rng:
        return '<span class="text-error">Range unavailable.</span>'
    if to_int(rng.get("request_enabled", 1)) != 1:
        return '<span class="text-error">Admin has disabled requests for this range.</span>'

    pay_col = PAY_COL[pay_term]
    enabled_col = PAY_ENABLED_COL[pay_term]
    if rng.get(pay_col) is None or (enabled_col in rng and to_int(rng[enabled_col]) != 1):
        return '<span class="text-error">Selected payment term is not available for this range.</span>'

    daily_limit = to_int(rng.get("max_numbers_per_agent_daily") or 0)
    used_today = to_int(ctx.db.query(
        "SELECT qty_requested FROM sms_range_agent_daily_requests "
        "WHERE range_id=? AND agent_id=? AND request_date=CURDATE()",
        [rid, ctx.user_id]).scalar() or 0)
    if daily_limit and (used_today + qty) > daily_limit:
        remaining = max(0, daily_limit - used_today)
        return (f'<span class="text-error">You aren\'t allowed to self request more than '
                f'{daily_limit} numbers from this range per day (you have {remaining} left today). '
                f'Please contact our sales team.</span>')

    rate = to_float(rng.get(pay_col))
    try:
        with ctx.db.transaction() as tx:
            rows = tx.query(
                "SELECT id FROM sms_numbers WHERE range_id=? AND assigned_to IS NULL "
                f"AND status='available' AND is_test=0 ORDER BY id ASC LIMIT {qty} FOR UPDATE",
                [rid]).fetchall()
            if len(rows) < qty:
                return (f'<span class="text-error">Only {len(rows)} number(s) are currently '
                         f'available in this range.</span>')
            for row in rows:
                tx.query(
                    "UPDATE sms_numbers SET assigned_to=?,assigned_at=UTC_TIMESTAMP(),"
                    "status='assigned',pay_term=?,payout_rate=? "
                    "WHERE id=? AND assigned_to IS NULL AND status='available'",
                    [ctx.user_id, pay_term, rate, to_int(row["id"])])
            available = to_int(tx.query(
                "SELECT COUNT(*) c FROM sms_numbers WHERE range_id=? AND assigned_to IS NULL "
                "AND status='available'", [rid]).scalar())
            tx.query("UPDATE sms_ranges SET available_numbers=? WHERE id=?", [available, rid])
            tx.query(
                "INSERT INTO sms_range_agent_daily_requests (range_id, agent_id, request_date, qty_requested) "
                "VALUES (?, ?, CURDATE(), ?) "
                "ON DUPLICATE KEY UPDATE qty_requested = qty_requested + VALUES(qty_requested)",
                [rid, ctx.user_id, qty])
            tx.query(
                "INSERT INTO sms_range_agent_requests (range_id, agent_id, request_count, last_requested_at) "
                "VALUES (?, ?, 1, UTC_TIMESTAMP()) "
                "ON DUPLICATE KEY UPDATE request_count = request_count + 1, last_requested_at = UTC_TIMESTAMP()",
                [rid, ctx.user_id])
    except Exception as exc:
        logger.warning("requestsmsnumberfinal error: %s", exc)
        return '<span class="text-error">Request failed. Please try again.</span>'

    log_activity(ctx.user_id, "number_self_request",
                 f"Self-requested {qty} numbers ({pay_term}) from range: {rng['range_name']}")
    create_notification(ctx.user_id, "Numbers Assigned",
                        f"{qty} numbers from {rng['range_name']} added to your account", "success")
    return (
        '<div class="modal-header"><h4>Request Numbers</h4></div>'
        '<div class="modal-body request-success-block">'
        f'<div class="alert alert-success">{to_int(qty)} number(s) have been added to your account.</div>'
        '</div>'
        '<div class="modal-footer"><a href="#" class="btn" data-dismiss="modal" '
        'onclick="location.reload();">Close</a></div>'
    )


async def dispatch(ctx: Ctx, name: str):
    if not ctx.session.logged_in:
        if name.startswith("aj_"):
            return {"results": [], "pagination": {"more": False}}
        return dt_out([], 0)

    try:
        if name in ("aj_agents", "aj_clients"):
            return aj_agents_clients(ctx, name)
        if name in ("aj_smsranges", "aj_smstestranges"):
            return aj_ranges(ctx, name)
        if name == "data_clients":
            return data_clients(ctx)
        if name == "data_smsnumbers":
            return data_smsnumbers(ctx)
        if name in RANGE_FAMILY:
            return data_ranges_family(ctx, name)
        if name == "data_news":
            return data_news(ctx)
        if name == "data_myactivity":
            return data_myactivity(ctx)
        if name == "data_notifications":
            return data_notifications(ctx)
        if name == "readnotifications":
            return await read_notifications(ctx)
        if name == "data_paymentrequests":
            return data_paymentrequests(ctx)
        if name == "data_creditnotes":
            return data_creditnotes(ctx)
        if name in STATS_FAMILY:
            return data_stats_family(ctx, name)
        if name in CDR_FAMILY:
            return data_cdr_family(ctx, name)
        if name == "data_smsbulkallocations":
            return data_smsbulkallocations(ctx)
        if name == "requestsmsnumber":
            return await request_numbers_form(ctx)
        if name == "requestsmsnumberfinal":
            return await request_numbers_final(ctx)
        if name == "assignallsmsnumber":
            return await assign_all_sms_numbers(ctx)
    except Exception as exc:
        logger.warning("legacy res error %s: %s", name, exc)
        if name.startswith("aj_"):
            return {"results": [], "pagination": {"more": False}}
        return dt_out([], 0)

    if name.startswith("data_"):
        return dt_out([], 0)
    if name.startswith("aj_"):
        return {"results": [], "pagination": {"more": False}}
    return ({"success": False,
             "message": "Backend endpoint is not implemented in this source package"}, 501)


@router.api_route("/ints/{role}/res/{name}", methods=["GET", "POST"])
@router.api_route("/ints/res/{name}", methods=["GET", "POST"])
async def legacy_res(role: str = "", name: str = "", *, request: Request,
                     ctx: Ctx = Depends(get_ctx)):
    endpoint = name[:-4] if name.endswith(".php") else name
    result = await dispatch(ctx, endpoint)
    if isinstance(result, str):
        return HTMLResponse(result)
    if isinstance(result, tuple):
        return json_response(result[0], result[1])
    return json_response(result)
