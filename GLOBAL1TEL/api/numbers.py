"""
SMS Numbers API — port of public/api/numbers.php.

Handles number listing per role, the Agent request workflow, and
Manager/Agent assignment. Every ownership rule from the PHP version is kept:
a Manager may only touch its own Agents, an Agent only its own Clients, and
the shared pool is guarded by row locks so two Managers cannot grab the same
number.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from core import config
from core.context import Ctx, get_auth_ctx
from core.helpers import (
    create_notification, db_column_exists, json_response, log_activity,
    manager_owner_sql, sanitize, to_float, to_int,
)

router = APIRouter()

PAY_TERMS = ["1/1", "7/1", "7/7", "30/45"]
PAY_COL = {"1/1": "payout_1_1", "7/1": "payout_7_1", "7/7": "payout_7_7", "30/45": "payout_30_45"}
PAY_ENABLED_COL = {
    "1/1": "payout_1_1_enabled", "7/1": "payout_7_1_enabled",
    "7/7": "payout_7_7_enabled", "30/45": "payout_30_45_enabled",
}


def _int_list(value) -> list:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    seen, out = set(), []
    for item in value:
        n = to_int(item)
        if n and n not in seen:
            seen.add(n)
            out.append(n)
    return out


# ── GET handlers ────────────────────────────────────────────────────────────
def list_numbers(ctx: Ctx):
    range_id = ctx.q_int("range_id")
    owner = manager_owner_sql("n.assigned_to")

    if ctx.role == "manager":
        base = (
            "SELECT n.*, u.username as assigned_username, r.range_name "
            "FROM sms_numbers n "
            "LEFT JOIN users u ON n.assigned_to = u.id "
            "LEFT JOIN sms_ranges r ON n.range_id = r.id WHERE "
        )
        scope = (f"((n.assigned_to IS NULL AND n.status='available' AND r.status='active') "
                 f"OR {owner} = ?)")
        if range_id:
            rows = ctx.db.query(base + f"n.range_id = ? AND {scope} ORDER BY n.number",
                                [range_id, ctx.user_id]).fetchall()
        else:
            rows = ctx.db.query(base + f"{scope} ORDER BY r.range_name, n.number",
                                [ctx.user_id]).fetchall()
    elif ctx.role == "agent":
        rows = ctx.db.query(
            "SELECT n.*, u.username as assigned_username, r.range_name "
            "FROM sms_numbers n "
            "LEFT JOIN users u ON n.assigned_to = u.id "
            "LEFT JOIN sms_ranges r ON n.range_id = r.id "
            "WHERE n.assigned_to = ? OR n.assigned_to IN (SELECT id FROM users WHERE parent_id = ?) "
            "ORDER BY r.range_name, n.number",
            [ctx.user_id, ctx.user_id],
        ).fetchall()
    else:
        rows = ctx.db.query(
            "SELECT n.*, r.range_name FROM sms_numbers n "
            "LEFT JOIN sms_ranges r ON n.range_id = r.id "
            "WHERE n.assigned_to = ? ORDER BY r.range_name, n.number",
            [ctx.user_id],
        ).fetchall()

    return json_response({"success": True, "data": rows})


def numbers_datatable(ctx: Ctx):
    params = ctx.all_params()
    draw = to_int(params.get("draw"), 1)
    start = max(0, to_int(params.get("start"), 0))
    length = to_int(params.get("length"), 25)
    length = 25 if length < 1 or length > 2000 else length
    search = params.get("search[value]") or params.get("search") or ""
    range_id = to_int(params.get("range_id"))
    assigned_to = to_int(params.get("assigned_to"))

    where = "1=1"
    sql_params: list = []

    if ctx.role == "manager":
        where += (f" AND ((n.assigned_to IS NULL AND n.status='available' AND r.status='active') "
                  f"OR {manager_owner_sql('n.assigned_to')} = ?)")
        sql_params.append(ctx.user_id)
        if range_id:
            where += " AND n.range_id = ?"
            sql_params.append(range_id)
    elif ctx.role == "agent":
        where += " AND (n.assigned_to = ? OR n.assigned_to IN (SELECT id FROM users WHERE parent_id = ?))"
        sql_params += [ctx.user_id, ctx.user_id]
    else:
        where += " AND n.assigned_to = ?"
        sql_params.append(ctx.user_id)

    if assigned_to:
        where += " AND n.assigned_to = ?"
        sql_params.append(assigned_to)

    if search:
        where += " AND (n.number LIKE ? OR r.range_name LIKE ? OR u.username LIKE ?)"
        sql_params += [f"%{search}%"] * 3

    records_total = to_int(ctx.db.query(
        f"SELECT COUNT(*) as count FROM sms_numbers n "
        f"LEFT JOIN sms_ranges r ON n.range_id = r.id "
        f"LEFT JOIN users u ON n.assigned_to = u.id WHERE {where}",
        sql_params,
    ).scalar())

    rows = ctx.db.query(
        f"SELECT n.*, r.range_name, u.username as assigned_username, u.role as assigned_role "
        f"FROM sms_numbers n "
        f"LEFT JOIN sms_ranges r ON n.range_id = r.id "
        f"LEFT JOIN users u ON n.assigned_to = u.id "
        f"WHERE {where} ORDER BY n.number ASC LIMIT {start}, {length}",
        sql_params,
    ).fetchall()

    data = []
    for row in rows:
        status = row.get("status")
        if status == "available":
            badge = '<span class="label label-success">Available</span>'
        elif status == "assigned":
            badge = '<span class="label label-info">Assigned</span>'
        else:
            badge = '<span class="label label-warning">Reserved</span>'
        test_badge = ' <span class="label label-important">Test</span>' if to_int(row.get("is_test")) else ""
        action = (f'<a href="#" class="btn btn-mini btn-info" onclick="viewNumber({row["id"]})">'
                  f'<i class="icon-eye-open"></i></a>') if ctx.role == "manager" else ""
        data.append([
            row.get("range_name"),
            f'{row["number"]}{test_badge}',
            row.get("assigned_username") or "-",
            badge,
            row.get("assigned_at") or "-",
            action,
        ])

    return json_response({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_total,
        "data": data,
    })


def available_numbers(ctx: Ctx):
    range_id = ctx.q_int("range_id")
    limit = max(1, min(200, ctx.q_int("limit", 10)))
    if not range_id:
        return json_response({"error": "Range ID required"}, 400)

    rng = ctx.db.query(
        "SELECT * FROM sms_ranges WHERE id=? AND status='active' LIMIT 1", [range_id]
    ).fetch()
    if not rng:
        return json_response({"error": "Range unavailable"}, 404)
    if ctx.role == "agent" and "request_enabled" in rng and to_int(rng["request_enabled"]) != 1:
        return json_response({"error": "Admin has disabled Agent requests for this range"}, 403)

    rows = ctx.db.query(
        f"SELECT n.*, r.range_name, r.currency, r.payout_1_1, r.payout_7_1, r.payout_7_7, r.payout_30_45 "
        f"FROM sms_numbers n JOIN sms_ranges r ON n.range_id = r.id "
        f"WHERE n.range_id = ? AND n.status = 'available' AND n.assigned_to IS NULL "
        f"AND n.is_test=0 AND r.status = 'active' ORDER BY n.number LIMIT {limit}",
        [range_id],
    ).fetchall()
    return json_response({"success": True, "data": rows})


def my_numbers(ctx: Ctx):
    rows = ctx.db.query(
        "SELECT n.*, r.range_name, r.prefix, r.currency, r.payout_1_1, r.payout_7_1, "
        "r.payout_7_7, r.payout_30_45 "
        "FROM sms_numbers n JOIN sms_ranges r ON n.range_id = r.id "
        "WHERE n.assigned_to = ? ORDER BY r.range_name, n.number",
        [ctx.user_id],
    ).fetchall()
    return json_response({"success": True, "data": rows})


def my_requests(ctx: Ctx):
    status = sanitize(ctx.q("status") or "")
    valid = ("pending", "approved", "rejected", "completed")

    if ctx.role == "manager":
        where = "a.role='agent' AND a.parent_id=?"
        params = [ctx.user_id]
        if status in valid:
            where += " AND nr.status=?"
            params.append(status)
        rows = ctx.db.query(
            f"SELECT nr.*,r.range_name,r.prefix,a.username agent_name "
            f"FROM number_requests nr JOIN users a ON a.id=nr.user_id "
            f"JOIN sms_ranges r ON nr.range_id=r.id WHERE {where} ORDER BY nr.created_at DESC",
            params,
        ).fetchall()
    else:
        where = "nr.user_id=?"
        params = [ctx.user_id]
        if status in valid:
            where += " AND nr.status=?"
            params.append(status)
        rows = ctx.db.query(
            f"SELECT nr.*,r.range_name,r.prefix FROM number_requests nr "
            f"JOIN sms_ranges r ON nr.range_id=r.id WHERE {where} ORDER BY nr.created_at DESC",
            params,
        ).fetchall()

    return json_response({"success": True, "data": rows})


# ── POST handlers ───────────────────────────────────────────────────────────
async def request_numbers(ctx: Ctx):
    # Admin provides one global inventory. Only an Agent may request numbers,
    # and the request is routed to that Agent's parent Manager.
    if ctx.role != "agent":
        return json_response({"error": "Only Agents can request numbers"}, 403)

    body = await ctx.body()
    range_id = to_int(body.get("range_id"))
    quantity = to_int(body.get("quantity"), 1)
    pay_term = sanitize(body.get("pay_term") or "1/1")
    notes = sanitize(body.get("notes") or "")

    if not range_id or quantity < 1 or quantity > 200:
        return json_response({"error": "Range ID and quantity between 1 and 200 required"}, 400)
    if pay_term not in PAY_TERMS:
        return json_response({"error": "Invalid payment term"}, 400)

    rng = ctx.db.query(
        "SELECT r.*,m.id AS request_manager_id FROM sms_ranges r "
        "JOIN users a ON a.id=? AND a.role='agent' AND a.status='active' "
        "JOIN users m ON m.id=a.parent_id AND m.role='manager' AND m.status='active' "
        "WHERE r.id=? AND r.status='active' LIMIT 1",
        [ctx.user_id, range_id],
    ).fetch()
    if not rng or not rng.get("request_manager_id"):
        return json_response({"error": "Range unavailable"}, 400)
    if "request_enabled" in rng and to_int(rng["request_enabled"]) != 1:
        return json_response({"error": "Admin has disabled Agent requests for this range"}, 403)

    pay_col = PAY_COL[pay_term]
    if rng.get(pay_col) is None or rng.get(pay_col) == "":
        return json_response({"error": "Selected payment term is not available for this range"}, 400)

    enabled_col = PAY_ENABLED_COL[pay_term]
    if enabled_col in rng and rng[enabled_col] is not None and to_int(rng[enabled_col]) != 1:
        return json_response({"error": "Admin has turned off this payment term for this range"}, 403)

    available = to_int(ctx.db.query(
        "SELECT COUNT(*) c FROM sms_numbers WHERE range_id=? AND assigned_to IS NULL "
        "AND status='available' AND is_test=0", [range_id]).scalar())
    if quantity > available:
        return json_response({"error": f"Only {available} number(s) are currently available"}, 409)

    pending = to_int(ctx.db.query(
        "SELECT COUNT(*) c FROM number_requests WHERE user_id=? AND range_id=? AND status='pending'",
        [ctx.user_id, range_id]).scalar())
    if pending:
        return json_response({"error": "You already have a pending request for this range"}, 409)

    result = ctx.db.query(
        "INSERT INTO number_requests (user_id, range_id, quantity, pay_term, notes, status) "
        "VALUES (?, ?, ?, ?, ?, 'pending')",
        [ctx.user_id, range_id, quantity, pay_term, notes],
    )
    request_id = result.lastrowid

    create_notification(to_int(rng["request_manager_id"]), "New Number Request",
                        f"Agent requested {quantity} numbers from global range: {rng['range_name']}",
                        "info")
    log_activity(ctx.user_id, "number_request",
                 f"Requested {quantity} numbers from range: {rng['range_name']}")
    return json_response({"success": True, "message": "Request submitted successfully",
                          "request_id": request_id})


async def assign_numbers(ctx: Ctx):
    if ctx.role not in ("manager", "agent"):
        return json_response({"error": "Only Managers and Agents can assign numbers"}, 403)

    body = await ctx.body()
    user_to = to_int(body.get("user_id") or body.get("client"))
    range_id = to_int(body.get("range_id") or body.get("range"))
    quantity = max(1, to_int(body.get("quantity") or body.get("qty"), 1))
    number_ids = _int_list(body.get("number_ids"))
    pay_term = sanitize(body.get("pay_term") or body.get("payterm") or "1/1")
    custom_payout = max(0.0, to_float(body.get("payout"), 0))

    if not user_to or (not range_id and not number_ids):
        return json_response({"error": "Target user and range or number IDs required"}, 400)
    if pay_term not in PAY_TERMS:
        pay_term = "1/1"

    if ctx.role == "manager":
        target = ctx.db.query(
            "SELECT id,username FROM users WHERE id=? AND role='agent' AND parent_id=? "
            "AND status='active' LIMIT 1", [user_to, ctx.user_id]).fetch()
        if not target:
            return json_response(
                {"error": "Manager can assign numbers only to an active Agent under this Manager"}, 403)
    else:
        target = ctx.db.query(
            "SELECT id,username FROM users WHERE id=? AND role='client' AND parent_id=? "
            "AND status='active' LIMIT 1", [user_to, ctx.user_id]).fetch()
        if not target:
            return json_response(
                {"error": "Agent can assign numbers only to an active Client under this Agent"}, 403)

    pay_col = PAY_COL[pay_term]
    enabled_col = PAY_ENABLED_COL[pay_term]
    enabled_expr = f"r.{enabled_col}" if db_column_exists(ctx.db, "sms_ranges", enabled_col) else "1"
    affected_ranges: set = set()

    try:
        with ctx.db.transaction() as tx:
            if number_ids:
                placeholders = ",".join("?" * len(number_ids))
                if ctx.role == "manager":
                    rows = tx.query(
                        f"SELECT n.id,n.range_id,r.{pay_col} payout,{enabled_expr} pay_term_enabled "
                        f"FROM sms_numbers n JOIN sms_ranges r ON r.id=n.range_id "
                        f"WHERE n.id IN ({placeholders}) AND r.status='active' "
                        f"AND n.assigned_to IS NULL AND n.status='available' AND n.is_test=0 FOR UPDATE",
                        number_ids,
                    ).fetchall()
                    if len(rows) != len(number_ids):
                        return json_response(
                            {"error": "One or more selected numbers are no longer available "
                                      "in the global pool"}, 409)
                    for row in rows:
                        if row["pay_term_enabled"] is not None and to_int(row["pay_term_enabled"]) != 1:
                            return json_response(
                                {"error": "Admin has turned off this payment term for one of the "
                                          "selected ranges"}, 403)
                    updated = 0
                    for row in rows:
                        rate = custom_payout if custom_payout > 0 else to_float(row.get("payout"))
                        res = tx.query(
                            "UPDATE sms_numbers SET assigned_to=?,assigned_at=UTC_TIMESTAMP(),"
                            "status='assigned',pay_term=?,payout_rate=? "
                            "WHERE id=? AND assigned_to IS NULL AND status='available'",
                            [user_to, pay_term, rate, to_int(row["id"])])
                        updated += res.rowcount
                        affected_ranges.add(to_int(row["range_id"]))
                    if updated != len(rows):
                        return json_response(
                            {"error": "Some numbers were assigned by another Manager. "
                                      "Refresh and try again."}, 409)
                else:
                    rows = tx.query(
                        f"SELECT n.id,n.range_id,n.payout_rate FROM sms_numbers n "
                        f"WHERE n.id IN ({placeholders}) AND n.assigned_to=? "
                        f"AND n.status='assigned' AND n.is_test=0",
                        number_ids + [ctx.user_id],
                    ).fetchall()
                    if len(rows) != len(number_ids):
                        return json_response(
                            {"error": "One or more selected numbers are not assigned to this Agent"}, 409)
                    for row in rows:
                        tx.query(
                            "UPDATE sms_numbers SET assigned_to=?,assigned_at=UTC_TIMESTAMP(),"
                            "status='assigned' WHERE id=? AND assigned_to=?",
                            [user_to, to_int(row["id"]), ctx.user_id])
            else:
                if quantity > 100000:
                    return json_response({"error": "Quantity is too large"}, 400)
                if ctx.role == "manager":
                    rng = tx.query(
                        f"SELECT id,{pay_col} payout,"
                        f"{enabled_expr.replace('r.', '')} pay_term_enabled "
                        f"FROM sms_ranges r WHERE id=? AND status='active' LIMIT 1", [range_id]).fetch()
                    if not rng:
                        return json_response({"error": "Global range not found or inactive"}, 404)
                    if rng["pay_term_enabled"] is not None and to_int(rng["pay_term_enabled"]) != 1:
                        return json_response(
                            {"error": "Admin has turned off this payment term for this range"}, 403)
                    rows = tx.query(
                        f"SELECT id FROM sms_numbers WHERE range_id=? AND assigned_to IS NULL "
                        f"AND status='available' AND is_test=0 ORDER BY id ASC LIMIT {quantity} FOR UPDATE",
                        [range_id]).fetchall()
                    if len(rows) < quantity:
                        return json_response({"error": "Not enough available numbers"}, 400)
                    rate = custom_payout if custom_payout > 0 else to_float(rng.get("payout"))
                    updated = 0
                    for row in rows:
                        res = tx.query(
                            "UPDATE sms_numbers SET assigned_to=?,assigned_at=UTC_TIMESTAMP(),"
                            "status='assigned',pay_term=?,payout_rate=? "
                            "WHERE id=? AND assigned_to IS NULL AND status='available'",
                            [user_to, pay_term, rate, to_int(row["id"])])
                        updated += res.rowcount
                    if updated != len(rows):
                        return json_response(
                            {"error": "Some numbers were assigned by another Manager. "
                                      "Refresh and try again."}, 409)
                    affected_ranges.add(range_id)
                else:
                    owned = to_int(tx.query(
                        "SELECT COUNT(*) c FROM sms_numbers WHERE range_id=? AND assigned_to=? "
                        "AND status='assigned' AND is_test=0", [range_id, ctx.user_id]).scalar())
                    if owned < quantity:
                        return json_response(
                            {"error": "Not enough numbers from this range are assigned to this Agent"}, 400)
                    rows = tx.query(
                        f"SELECT id FROM sms_numbers WHERE range_id=? AND assigned_to=? "
                        f"AND status='assigned' AND is_test=0 ORDER BY id ASC LIMIT {quantity}",
                        [range_id, ctx.user_id]).fetchall()
                    for row in rows:
                        tx.query(
                            "UPDATE sms_numbers SET assigned_to=?,assigned_at=UTC_TIMESTAMP(),"
                            "status='assigned' WHERE id=? AND assigned_to=?",
                            [user_to, to_int(row["id"]), ctx.user_id])

            for rid in affected_ranges:
                available = to_int(tx.query(
                    "SELECT COUNT(*) c FROM sms_numbers WHERE range_id=? AND assigned_to IS NULL "
                    "AND status='available'", [rid]).scalar())
                tx.query("UPDATE sms_ranges SET available_numbers=? WHERE id=?", [available, rid])
    except Exception as exc:
        return json_response(
            {"error": str(exc) if config.APP_DEBUG else "Failed to assign numbers"}, 500)

    create_notification(user_to, "Numbers Assigned", "You have been assigned numbers", "success")
    log_activity(ctx.user_id, "numbers_assigned", f"Assigned numbers to user: {target['username']}")
    return json_response({"success": True, "message": "Numbers assigned successfully"})


async def unassign_numbers(ctx: Ctx):
    if ctx.role not in ("manager", "agent"):
        return json_response({"error": "Not allowed"}, 403)

    body = await ctx.body()
    number_ids = _int_list(body.get("number_ids"))
    if not number_ids:
        return json_response({"error": "Number IDs required"}, 400)
    placeholders = ",".join("?" * len(number_ids))

    try:
        with ctx.db.transaction() as tx:
            if ctx.role == "manager":
                valid = to_int(tx.query(
                    f"SELECT COUNT(*) c FROM sms_numbers n JOIN users a ON a.id=n.assigned_to "
                    f"WHERE n.id IN ({placeholders}) AND a.role='agent' AND a.parent_id=?",
                    number_ids + [ctx.user_id]).scalar())
                if valid != len(number_ids):
                    return json_response(
                        {"error": "Manager can unassign only numbers currently assigned directly "
                                  "to this Manager's Agents"}, 409)
                tx.query(
                    f"UPDATE sms_numbers n JOIN users a ON a.id=n.assigned_to "
                    f"SET n.assigned_to=NULL,n.assigned_at=NULL,n.status='available' "
                    f"WHERE n.id IN ({placeholders}) AND a.role='agent' AND a.parent_id=?",
                    number_ids + [ctx.user_id])
            else:
                valid = to_int(tx.query(
                    f"SELECT COUNT(*) c FROM sms_numbers n JOIN users c ON c.id=n.assigned_to "
                    f"WHERE n.id IN ({placeholders}) AND c.role='client' AND c.parent_id=?",
                    number_ids + [ctx.user_id]).scalar())
                if valid != len(number_ids):
                    return json_response(
                        {"error": "Agent can take back only numbers assigned to this "
                                  "Agent's Clients"}, 409)
                # Taking a number back moves it to the Agent, not to the free pool.
                tx.query(
                    f"UPDATE sms_numbers n JOIN users c ON c.id=n.assigned_to "
                    f"SET n.assigned_to=?,n.assigned_at=UTC_TIMESTAMP(),n.status='assigned' "
                    f"WHERE n.id IN ({placeholders}) AND c.role='client' AND c.parent_id=?",
                    [ctx.user_id] + number_ids + [ctx.user_id])

            ranges = tx.query(
                f"SELECT DISTINCT range_id FROM sms_numbers WHERE id IN ({placeholders})",
                number_ids).fetchall()
            for row in ranges:
                rid = to_int(row["range_id"])
                count = to_int(tx.query(
                    "SELECT COUNT(*) c FROM sms_numbers WHERE range_id=? AND assigned_to IS NULL "
                    "AND status='available'", [rid]).scalar())
                tx.query("UPDATE sms_ranges SET available_numbers=? WHERE id=?", [count, rid])
    except Exception as exc:
        return json_response(
            {"error": str(exc) if config.APP_DEBUG else "Failed to update numbers"}, 500)

    log_activity(ctx.user_id, "numbers_unassigned",
                 f"Unassigned/took back {len(number_ids)} numbers")
    return json_response({"success": True, "message": "Numbers updated successfully"})


async def approve_request(ctx: Ctx):
    if ctx.role != "manager":
        return json_response({"error": "Only Managers can approve Agent requests"}, 403)

    body = await ctx.body()
    request_id = to_int(body.get("request_id"))
    if not request_id:
        return json_response({"error": "Request ID required"}, 400)

    req = ctx.db.query(
        "SELECT nr.*,a.username agent_name FROM number_requests nr "
        "JOIN users a ON a.id=nr.user_id "
        "WHERE nr.id=? AND nr.status='pending' AND a.role='agent' AND a.parent_id=? LIMIT 1",
        [request_id, ctx.user_id],
    ).fetch()
    if not req:
        return json_response({"error": "Request not found in this Manager hierarchy"}, 404)

    qty = to_int(req["quantity"])
    if qty < 1 or qty > 200:
        return json_response({"error": "Invalid request quantity (maximum 200)"}, 400)
    term = req["pay_term"] if req["pay_term"] in PAY_TERMS else "1/1"
    col = PAY_COL[term]

    try:
        with ctx.db.transaction() as tx:
            rng = tx.query("SELECT * FROM sms_ranges WHERE id=? AND status='active' LIMIT 1 FOR UPDATE",
                           [to_int(req["range_id"])]).fetch()
            if not rng:
                return json_response({"error": "Global range is inactive or unavailable"}, 404)
            if "request_enabled" in rng and to_int(rng["request_enabled"]) != 1:
                return json_response({"error": "Admin has disabled requests for this range"}, 403)
            if rng.get(col) is None or rng.get(col) == "":
                return json_response({"error": "Requested payment term is no longer available"}, 409)

            rows = tx.query(
                f"SELECT id FROM sms_numbers WHERE range_id=? AND assigned_to IS NULL "
                f"AND status='available' AND is_test=0 ORDER BY id ASC LIMIT {qty} FOR UPDATE",
                [to_int(req["range_id"])]).fetchall()
            if len(rows) < qty:
                return json_response({"error": "Not enough available Admin-provided numbers"}, 409)

            rate = to_float(rng[col])
            updated = 0
            for row in rows:
                res = tx.query(
                    "UPDATE sms_numbers SET assigned_to=?,assigned_at=UTC_TIMESTAMP(),"
                    "status='assigned',pay_term=?,payout_rate=? "
                    "WHERE id=? AND assigned_to IS NULL AND status='available'",
                    [to_int(req["user_id"]), term, rate, to_int(row["id"])])
                updated += res.rowcount
            if updated != len(rows):
                return json_response(
                    {"error": "Some requested numbers were taken from the global pool. "
                              "Refresh and try again."}, 409)

            available = to_int(tx.query(
                "SELECT COUNT(*) c FROM sms_numbers WHERE range_id=? AND assigned_to IS NULL "
                "AND status='available' AND is_test=0", [to_int(req["range_id"])]).scalar())
            tx.query("UPDATE sms_ranges SET available_numbers=? WHERE id=?",
                     [available, to_int(req["range_id"])])
            tx.query(
                "UPDATE number_requests SET status='approved',processed_by=?,"
                "processed_at=UTC_TIMESTAMP() WHERE id=? AND status='pending'",
                [ctx.user_id, request_id])
    except Exception as exc:
        return json_response(
            {"error": str(exc) if config.APP_DEBUG else "Failed to process request"}, 500)

    create_notification(to_int(req["user_id"]), "Request Approved",
                        "Your number request has been approved and the numbers were assigned "
                        "to your account.", "success")
    log_activity(ctx.user_id, "request_approved",
                 f"Approved Agent number request ID: {request_id} ({qty} number(s))")
    return json_response({"success": True,
                          "message": "Request approved and numbers assigned to Agent"})


async def reject_request(ctx: Ctx):
    if ctx.role != "manager":
        return json_response({"error": "Only Managers can reject Agent requests"}, 403)

    body = await ctx.body()
    request_id = to_int(body.get("request_id"))
    reason = sanitize(body.get("reason") or "")
    if not request_id:
        return json_response({"error": "Request ID required"}, 400)

    req = ctx.db.query(
        "SELECT nr.*,a.username agent_name FROM number_requests nr JOIN users a ON a.id=nr.user_id "
        "WHERE nr.id=? AND nr.status='pending' AND a.role='agent' AND a.parent_id=? LIMIT 1",
        [request_id, ctx.user_id],
    ).fetch()
    if not req:
        return json_response({"error": "Request not found in this Manager hierarchy"}, 404)

    ctx.db.query(
        "UPDATE number_requests SET status='rejected',"
        "notes=CONCAT(COALESCE(notes,''),' | Rejection: ',?),processed_by=?,"
        "processed_at=UTC_TIMESTAMP() WHERE id=?",
        [reason, ctx.user_id, request_id])
    create_notification(to_int(req["user_id"]), "Request Rejected",
                        "Your number request has been rejected", "error")
    log_activity(ctx.user_id, "request_rejected", f"Rejected Agent number request ID: {request_id}")
    return json_response({"success": True, "message": "Request rejected"})


@router.api_route("/api/numbers.php", methods=["GET", "POST", "PUT", "DELETE"])
@router.api_route("/api/numbers", methods=["GET", "POST", "PUT", "DELETE"])
async def numbers_endpoint(request: Request, ctx: Ctx = Depends(get_auth_ctx)):
    action = ctx.q("action") or "list"

    if ctx.method == "GET":
        if action == "datatable":
            return numbers_datatable(ctx)
        if action == "available":
            return available_numbers(ctx)
        if action == "my":
            return my_numbers(ctx)
        if action == "requests":
            return my_requests(ctx)
        return list_numbers(ctx)

    if ctx.method == "POST":
        handlers = {
            "request": request_numbers,
            "assign": assign_numbers,
            "unassign": unassign_numbers,
            "approve": approve_request,
            "reject": reject_request,
        }
        handler = handlers.get(action)
        if not handler:
            return json_response({"error": "Invalid action"}, 400)
        return await handler(ctx)

    return json_response({"error": "Method not allowed"}, 405)
