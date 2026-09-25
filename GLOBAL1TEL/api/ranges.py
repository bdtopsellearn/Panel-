"""
SMS Ranges API — port of public/api/ranges.php.

Range creation, editing, deletion and number upload are Admin-only, so this
endpoint stays read-only (GET) for Manager / Agent / Client views exactly as
the PHP version did; any other method returns 403.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from core.context import Ctx, get_auth_ctx
from core.helpers import json_response, to_int

router = APIRouter()

DATATABLE_COLUMNS = [
    "range_name", "prefix", "total_numbers", "test_number", "currency",
    "payout_1_1", "payout_7_1", "payout_7_7", "payout_30_45", "memo",
]


def list_ranges(ctx: Ctx):
    if ctx.role == "manager":
        # Ranges are created by Admin and are global for every Manager.
        rows = ctx.db.query(
            "SELECT r.*, "
            " (SELECT COUNT(*) FROM sms_numbers WHERE range_id = r.id) as total_numbers, "
            " (SELECT COUNT(*) FROM sms_numbers WHERE range_id = r.id AND assigned_to IS NULL "
            "  AND status = 'available') as available_numbers "
            "FROM sms_ranges r ORDER BY r.created_at DESC"
        ).fetchall()
    else:
        rows = ctx.db.query(
            "SELECT id, range_name, prefix, currency, payout_1_1, payout_7_1, payout_7_7, "
            "payout_30_45, available_numbers, status "
            "FROM sms_ranges WHERE status = 'active' AND available_numbers > 0 ORDER BY range_name"
        ).fetchall()
    return json_response({"success": True, "data": rows})


def get_range(ctx: Ctx):
    range_id = ctx.q_int("id")
    if not range_id:
        return json_response({"error": "Range ID required"}, 400)

    if ctx.role == "manager":
        row = ctx.db.query("SELECT * FROM sms_ranges WHERE id = ?", [range_id]).fetch()
    else:
        row = ctx.db.query(
            "SELECT id, range_name, prefix, currency, payout_1_1, payout_7_1, payout_7_7, "
            "payout_30_45, status FROM sms_ranges WHERE id = ? AND status = 'active'",
            [range_id],
        ).fetch()

    if not row:
        return json_response({"error": "Range not found"}, 404)
    return json_response({"success": True, "data": row})


def ranges_datatable(ctx: Ctx):
    params = ctx.all_params()
    draw = to_int(params.get("draw"), 1)
    start = to_int(params.get("start"), 0)
    length = to_int(params.get("length"), 25)
    search = params.get("search[value]") or params.get("search") or ""
    order_column = to_int(params.get("order[0][column]"), 0)
    order_dir = "desc" if str(params.get("order[0][dir]", "asc")).lower() == "desc" else "asc"

    # Whitelisted: order_by/direction are interpolated, never taken raw.
    order_by = DATATABLE_COLUMNS[order_column] if 0 <= order_column < len(DATATABLE_COLUMNS) else "range_name"
    start = max(0, start)
    length = 25 if length < 1 or length > 2000 else length

    records_total = to_int(ctx.db.query("SELECT COUNT(*) as count FROM sms_ranges").scalar())

    where = "1=1"
    sql_params: list = []
    if search:
        where += " AND (range_name LIKE ? OR prefix LIKE ? OR memo LIKE ?)"
        sql_params += [f"%{search}%"] * 3

    records_filtered = to_int(
        ctx.db.query(f"SELECT COUNT(*) as count FROM sms_ranges WHERE {where}", sql_params).scalar()
    )

    rows = ctx.db.query(
        f"SELECT r.*, "
        f" (SELECT COUNT(*) FROM sms_numbers WHERE range_id = r.id) as total_numbers, "
        f" (SELECT COUNT(*) FROM sms_numbers WHERE range_id = r.id AND assigned_to IS NULL "
        f"  AND status = 'available') as available_numbers "
        f"FROM sms_ranges r WHERE {where} ORDER BY {order_by} {order_dir} LIMIT {start}, {length}",
        sql_params,
    ).fetchall()

    data = [[
        row["range_name"],
        row["prefix"],
        row["total_numbers"],
        row.get("test_number"),
        row["currency"],
        row.get("payout_1_1") if row.get("payout_1_1") is not None else "N/A",
        row.get("payout_7_1") if row.get("payout_7_1") is not None else "N/A",
        row.get("payout_7_7") if row.get("payout_7_7") is not None else "N/A",
        row.get("payout_30_45") if row.get("payout_30_45") is not None else "N/A",
        row.get("memo") or "",
        f'<a href="#" class="btn btn-mini btn-info" onclick="viewNumbers({row["id"]})">'
        f'<i class="icon-eye-open"></i></a>',
    ] for row in rows]

    return json_response({
        "draw": draw,
        "recordsTotal": records_total,
        "recordsFiltered": records_filtered,
        "data": data,
    })


def ranges_dropdown(ctx: Ctx):
    search = ctx.q("q") or ""
    page = max(1, ctx.q_int("page", 1))
    per_page = max(1, min(100, ctx.q_int("max", 25)))
    offset = (page - 1) * per_page

    where = "status = 'active' AND available_numbers > 0"
    params: list = []
    if search:
        where += " AND (range_name LIKE ? OR prefix LIKE ?)"
        params += [f"%{search}%"] * 2

    rows = ctx.db.query(
        f"SELECT id, range_name as title FROM sms_ranges WHERE {where} "
        f"ORDER BY range_name LIMIT {per_page} OFFSET {offset}",
        params,
    ).fetchall()
    total = to_int(
        ctx.db.query(f"SELECT COUNT(*) as count FROM sms_ranges WHERE {where}", params).scalar()
    )

    return json_response({
        "results": [{"id": r["id"], "title": r["title"]} for r in rows],
        "pagination": {"more": (offset + per_page) < total},
    })


@router.api_route("/api/ranges.php", methods=["GET", "POST", "PUT", "DELETE"])
@router.api_route("/api/ranges", methods=["GET", "POST", "PUT", "DELETE"])
async def ranges_endpoint(request: Request, ctx: Ctx = Depends(get_auth_ctx)):
    if ctx.method != "GET":
        return json_response(
            {"error": "SMS ranges and number uploads are managed by Admin only"}, 403
        )

    action = ctx.q("action") or "list"
    if action == "get":
        return get_range(ctx)
    if action == "datatable":
        return ranges_datatable(ctx)
    if action == "dropdown":
        return ranges_dropdown(ctx)
    return list_ranges(ctx)
