"""
Users API — port of public/api/users.php.

Manages agents and clients within the caller's own hierarchy. A Manager may
only touch its own Agents (and their Clients), an Agent only its own Clients;
a Client may only see itself. Those checks live in can_access_user() and
is_direct_child(), matching the PHP helpers of the same name.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from core import config
from core.context import Ctx, get_auth_ctx
from core.helpers import (
    create_notification, generate_hash, generate_token, json_response, log_activity,
    sanitize, to_float, to_int,
)

router = APIRouter()

APP_BRAND = config.APP_NAME


def can_access_user(ctx: Ctx, target_id) -> bool:
    target_id = to_int(target_id)
    if target_id == ctx.user_id:
        return True
    if ctx.role == "manager":
        return bool(ctx.db.query(
            "SELECT id FROM users WHERE id=? AND (parent_id=? OR parent_id IN "
            "(SELECT id FROM users WHERE role='agent' AND parent_id=?)) LIMIT 1",
            [target_id, ctx.user_id, ctx.user_id]).fetch())
    if ctx.role == "agent":
        return bool(ctx.db.query(
            "SELECT id FROM users WHERE id=? AND parent_id=? AND role='client' LIMIT 1",
            [target_id, ctx.user_id]).fetch())
    return False


def is_direct_child(ctx: Ctx, target_id) -> bool:
    if ctx.role not in ("manager", "agent"):
        return False
    want = "agent" if ctx.role == "manager" else "client"
    return bool(ctx.db.query(
        "SELECT id FROM users WHERE id=? AND parent_id=? AND role=? LIMIT 1",
        [to_int(target_id), ctx.user_id, want]).fetch())


# ── GET ─────────────────────────────────────────────────────────────────────
def list_users(ctx: Ctx):
    if ctx.role == "manager":
        rows = ctx.db.query(
            "SELECT u.*, p.full_name, p.phone, "
            "(SELECT COUNT(*) FROM users WHERE parent_id = u.id) as client_count, "
            "(SELECT COUNT(*) FROM sms_numbers WHERE assigned_to = u.id) as number_count "
            "FROM users u LEFT JOIN user_profiles p ON u.id = p.user_id "
            "WHERE u.role = 'agent' AND u.parent_id = ? ORDER BY u.created_at DESC",
            [ctx.user_id]).fetchall()
    elif ctx.role == "agent":
        rows = ctx.db.query(
            "SELECT u.*, p.full_name, p.phone, "
            "(SELECT COUNT(*) FROM sms_numbers WHERE assigned_to = u.id) as number_count "
            "FROM users u LEFT JOIN user_profiles p ON u.id = p.user_id "
            "WHERE u.role = 'client' AND u.parent_id = ? ORDER BY u.created_at DESC",
            [ctx.user_id]).fetchall()
    else:
        rows = ctx.db.query(
            "SELECT u.*, p.full_name, p.phone FROM users u "
            "LEFT JOIN user_profiles p ON u.id = p.user_id WHERE u.id = ?",
            [ctx.user_id]).fetchall()

    for row in rows:
        row.pop("password", None)
    return json_response({"success": True, "data": rows})


def get_user(ctx: Ctx):
    user_id = ctx.q_int("id")
    if not user_id:
        return json_response({"error": "User ID required"}, 400)
    if not can_access_user(ctx, user_id):
        return json_response({"error": "Access denied"}, 403)

    user = ctx.db.query(
        "SELECT u.*, p.full_name, p.phone, p.address, p.company, p.timezone, p.avatar, "
        "b.currency, b.balance FROM users u "
        "LEFT JOIN user_profiles p ON u.id = p.user_id "
        "LEFT JOIN user_balances b ON u.id = b.user_id WHERE u.id = ?",
        [user_id]).fetch()
    if not user:
        return json_response({"error": "User not found"}, 404)

    user = dict(user)
    user.pop("password", None)
    return json_response({"success": True, "data": user})


def users_dropdown(ctx: Ctx):
    search = sanitize(ctx.q("q") or "")
    user_role = sanitize(ctx.q("role") or "")
    page = max(1, ctx.q_int("page", 1))
    per_page = max(1, min(100, ctx.q_int("max", 25)))
    offset = (page - 1) * per_page

    where = "status = 'active'"
    params: list = []

    if ctx.role == "manager":
        where += " AND parent_id = ? AND role = ?"
        params += [ctx.user_id, user_role or "agent"]
    elif ctx.role == "agent":
        where += " AND parent_id = ? AND role = 'client'"
        params.append(ctx.user_id)
    else:
        return json_response({"results": [], "pagination": {"more": False}})

    if search:
        where += (" AND (username LIKE ? OR (SELECT full_name FROM user_profiles "
                  "WHERE user_id = users.id) LIKE ?)")
        params += [f"%{search}%"] * 2

    rows = ctx.db.query(
        f"SELECT id, username as title FROM users WHERE {where} "
        f"ORDER BY username LIMIT {per_page} OFFSET {offset}", params).fetchall()
    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) as count FROM users WHERE {where}", params).scalar())

    return json_response({
        "results": [{"id": r["id"], "title": r["title"]} for r in rows],
        "pagination": {"more": (offset + per_page) < total},
    })


def get_profile(ctx: Ctx):
    user = ctx.db.query(
        "SELECT u.*, p.full_name, p.phone, p.address, p.company, p.timezone, p.avatar "
        "FROM users u LEFT JOIN user_profiles p ON u.id = p.user_id WHERE u.id = ?",
        [ctx.user_id]).fetch()
    if not user:
        return json_response({"error": "User not found"}, 404)
    user = dict(user)
    user.pop("password", None)
    user["balances"] = ctx.db.query(
        "SELECT currency, balance FROM user_balances WHERE user_id = ?",
        [ctx.user_id]).fetch_key_pair()
    return json_response({"success": True, "data": user})


def get_activity(ctx: Ctx):
    target = ctx.q_int("user_id", ctx.user_id) or ctx.user_id
    limit = max(1, min(500, ctx.q_int("limit", 50)))
    if not can_access_user(ctx, target):
        return json_response({"error": "Access denied"}, 403)
    rows = ctx.db.query(
        f"SELECT * FROM user_activity WHERE user_id = ? ORDER BY created_at DESC LIMIT {limit}",
        [target]).fetchall()
    return json_response({"success": True, "data": rows})


def users_datatable(ctx: Ctx):
    params_get = ctx.all_params()
    draw = to_int(params_get.get("draw"), 1)
    start = max(0, to_int(params_get.get("start"), 0))
    length = to_int(params_get.get("length"), 25)
    length = 25 if length < 1 or length > 2000 else length
    search = params_get.get("search[value]") or params_get.get("search") or ""
    user_role = sanitize(params_get.get("role") or "agent")

    where = "u.role = ?"
    params: list = [user_role]

    if ctx.role == "manager":
        where += " AND u.parent_id = ?"
        params.append(ctx.user_id)
    elif ctx.role == "agent":
        where += " AND u.parent_id = ? AND u.role = 'client'"
        params.append(ctx.user_id)
    else:
        return json_response({"draw": draw, "recordsTotal": 0,
                              "recordsFiltered": 0, "data": []})

    if search:
        where += " AND (u.username LIKE ? OR p.full_name LIKE ? OR u.email LIKE ?)"
        params += [f"%{search}%"] * 3

    records_total = to_int(ctx.db.query(
        f"SELECT COUNT(*) as count FROM users u "
        f"LEFT JOIN user_profiles p ON u.id = p.user_id WHERE {where}", params).scalar())

    rows = ctx.db.query(
        f"SELECT u.*, p.full_name, p.phone, "
        f"(SELECT COUNT(*) FROM sms_numbers WHERE assigned_to = u.id) as number_count, "
        f"(SELECT GROUP_CONCAT(CONCAT(currency, ':', balance) SEPARATOR ',') "
        f" FROM user_balances WHERE user_id = u.id) as balances "
        f"FROM users u LEFT JOIN user_profiles p ON u.id = p.user_id "
        f"WHERE {where} ORDER BY u.created_at DESC LIMIT {start}, {length}", params).fetchall()

    data = []
    for row in rows:
        status_badge = ('<span class="label label-success">Active</span>'
                        if row.get("status") == "active"
                        else '<span class="label label-important">Inactive</span>')
        last_login = row.get("last_login")
        last_login = last_login.strftime("%Y-%m-%d %H:%M") if hasattr(last_login, "strftime") \
            else (str(last_login)[:16] if last_login else "Never")

        balances = []
        if row.get("balances"):
            for item in str(row["balances"]).split(","):
                if ":" in item:
                    cur, bal = item.split(":", 1)
                    balances.append(f"{cur}: {to_float(bal):,.2f}")

        toggle = (f'<a href="#" class="btn btn-mini btn-danger" '
                  f"onclick=\"toggleUser({row['id']}, 'inactive')\">"
                  f'<i class="icon-ban-circle"></i></a>'
                  if row.get("status") == "active" else
                  f'<a href="#" class="btn btn-mini btn-success" '
                  f"onclick=\"toggleUser({row['id']}, 'active')\">"
                  f'<i class="icon-ok"></i></a>')

        data.append([
            row.get("username"),
            row.get("full_name") or "-",
            row.get("email") or "-",
            row.get("number_count"),
            ", ".join(balances) or "-",
            status_badge,
            last_login,
            f'<a href="#" class="btn btn-mini btn-info" onclick="viewUser({row["id"]})">'
            f'<i class="icon-eye-open"></i></a> '
            f'<a href="#" class="btn btn-mini btn-warning" onclick="editUser({row["id"]})">'
            f'<i class="icon-edit"></i></a> ' + toggle,
        ])

    return json_response({"draw": draw, "recordsTotal": records_total,
                          "recordsFiltered": records_total, "data": data})


# ── POST ────────────────────────────────────────────────────────────────────
async def create_user(ctx: Ctx):
    body = await ctx.body()
    username = sanitize(body.get("username") or "")
    password = body.get("password") or ""
    email = sanitize(body.get("email") or "")
    user_role = sanitize(body.get("role") or "client")
    full_name = sanitize(body.get("full_name") or "")
    phone = sanitize(body.get("phone") or "")

    if not username or not password:
        return json_response({"error": "Username and password are required"}, 400)
    if ctx.role == "manager" and user_role not in ("agent", "client"):
        return json_response({"error": "Managers can only create agents or clients"}, 403)
    if ctx.role == "agent" and user_role != "client":
        return json_response({"error": "Agents can only create clients"}, 403)
    if ctx.role not in ("manager", "agent"):
        return json_response({"error": "Access denied"}, 403)

    if ctx.db.query("SELECT id FROM users WHERE username = ?", [username]).fetch():
        return json_response({"error": "Username already exists"}, 400)

    parent_id = ctx.user_id
    if ctx.role == "manager" and user_role == "client":
        # A Client must belong to one of this Manager's Agents.
        parent_id = to_int(body.get("agent_id"))
        if not parent_id or not ctx.db.query(
            "SELECT id FROM users WHERE id=? AND parent_id=? AND role='agent' "
            "AND status='active' LIMIT 1", [parent_id, ctx.user_id]).fetch():
            return json_response({"error": "A valid Agent is required for a Client account"}, 400)

    try:
        with ctx.db.transaction() as tx:
            result = tx.query(
                "INSERT INTO users (username, password, email, role, parent_id, status, api_token) "
                "VALUES (?, ?, ?, ?, ?, 'active', ?)",
                [username, generate_hash(password), email, user_role, parent_id, generate_token()])
            new_user_id = result.lastrowid
            tx.query("INSERT INTO user_profiles (user_id, full_name, phone) VALUES (?, ?, ?)",
                     [new_user_id, full_name, phone])
            tx.query(
                "INSERT INTO user_balances (user_id, currency, balance) "
                "VALUES (?, 'USD', 0), (?, 'EUR', 0), (?, 'GBP', 0)",
                [new_user_id, new_user_id, new_user_id])
    except Exception as exc:
        return json_response({"error": f"Failed to create user: {exc}"}, 500)

    log_activity(ctx.user_id, "user_created", f"Created {user_role}: {username}")
    create_notification(new_user_id, "Account Created",
                        f"Your account has been created. Welcome to {APP_BRAND}!", "success")
    return json_response({"success": True,
                          "message": f"{user_role.capitalize()} created successfully",
                          "id": new_user_id})


async def update_user(ctx: Ctx):
    body = await ctx.body()
    user_id = to_int(body.get("id"))
    if not user_id:
        return json_response({"error": "User ID required"}, 400)

    target = ctx.db.query("SELECT * FROM users WHERE id = ?", [user_id]).fetch()
    if not target:
        return json_response({"error": "User not found"}, 404)
    if not can_access_user(ctx, user_id):
        return json_response({"error": "Access denied"}, 403)

    user_fields, user_params = [], []
    profile_fields, profile_params = [], []

    if "email" in body:
        user_fields.append("email = ?")
        user_params.append(sanitize(body["email"]))

    if "status" in body and is_direct_child(ctx, user_id):
        status = sanitize(body["status"])
        if status in ("active", "inactive", "suspended"):
            user_fields.append("status = ?")
            user_params.append(status)

    for field in ("full_name", "phone", "address", "company", "timezone"):
        if field in body:
            profile_fields.append(f"{field} = ?")
            profile_params.append(sanitize(body[field]))

    if user_fields:
        ctx.db.query(f"UPDATE users SET {', '.join(user_fields)} WHERE id = ?",
                     user_params + [user_id])
    if profile_fields:
        # INSERT..ON DUPLICATE so a profile row that was never created still
        # gets written instead of the update silently affecting zero rows.
        ctx.db.query("INSERT IGNORE INTO user_profiles (user_id) VALUES (?)", [user_id])
        ctx.db.query(f"UPDATE user_profiles SET {', '.join(profile_fields)} WHERE user_id = ?",
                     profile_params + [user_id])

    log_activity(ctx.user_id, "user_updated", f"Updated user ID: {user_id}")
    return json_response({"success": True, "message": "User updated successfully"})


async def delete_user(ctx: Ctx):
    body = await ctx.body()
    user_id = to_int(body.get("id"))
    if not user_id:
        return json_response({"error": "User ID required"}, 400)
    if not is_direct_child(ctx, user_id):
        return json_response({"error": "User not found or access denied"}, 403)

    target = ctx.db.query("SELECT * FROM users WHERE id = ? AND parent_id = ?",
                          [user_id, ctx.user_id]).fetch()
    if not target:
        return json_response({"error": "User not found"}, 404)

    assigned = to_int(ctx.db.query(
        "SELECT COUNT(*) as count FROM sms_numbers WHERE assigned_to = ?", [user_id]).scalar())
    if assigned > 0:
        return json_response({"error": "Cannot delete user with assigned numbers"}, 400)

    ctx.db.query("DELETE FROM users WHERE id = ?", [user_id])
    log_activity(ctx.user_id, "user_deleted", f"Deleted user: {target['username']}")
    return json_response({"success": True, "message": "User deleted successfully"})


async def update_profile(ctx: Ctx):
    body = await ctx.body()
    ctx.db.query(
        "INSERT INTO user_profiles (user_id, full_name, phone, address, company, timezone) "
        "VALUES (?, ?, ?, ?, ?, ?) ON DUPLICATE KEY UPDATE full_name = VALUES(full_name), "
        "phone = VALUES(phone), address = VALUES(address), company = VALUES(company), "
        "timezone = VALUES(timezone)",
        [ctx.user_id, sanitize(body.get("full_name") or ""), sanitize(body.get("phone") or ""),
         sanitize(body.get("address") or ""), sanitize(body.get("company") or ""),
         sanitize(body.get("timezone") or "UTC")])

    email = sanitize(body.get("email") or "")
    if email:
        ctx.db.query("UPDATE users SET email = ? WHERE id = ?", [email, ctx.user_id])

    log_activity(ctx.user_id, "profile_updated", "Profile updated")
    return json_response({"success": True, "message": "Profile updated successfully"})


async def change_password(ctx: Ctx):
    body = await ctx.body()
    current = body.get("current_password") or ""
    new = body.get("new_password") or ""
    confirm = body.get("confirm_password") or ""

    if not current or not new:
        return json_response({"error": "Current and new password are required"}, 400)
    if new != confirm:
        return json_response({"error": "Passwords do not match"}, 400)
    if len(new) < 6:
        return json_response({"error": "Password must be at least 6 characters"}, 400)

    user = ctx.db.query("SELECT password FROM users WHERE id = ?", [ctx.user_id]).fetch()
    if not user or str(user["password"]) != generate_hash(current):
        return json_response({"error": "Current password is incorrect"}, 400)

    ctx.db.query("UPDATE users SET password = ? WHERE id = ?",
                 [generate_hash(new), ctx.user_id])
    log_activity(ctx.user_id, "password_changed", "Password changed")
    return json_response({"success": True, "message": "Password changed successfully"})


async def toggle_status(ctx: Ctx):
    body = await ctx.body()
    user_id = to_int(body.get("id"))
    status = sanitize(body.get("status") or "active")
    if not user_id or status not in ("active", "inactive", "suspended"):
        return json_response({"error": "Invalid parameters"}, 400)
    if not is_direct_child(ctx, user_id):
        return json_response({"error": "User not found or access denied"}, 403)

    ctx.db.query("UPDATE users SET status = ? WHERE id = ? AND parent_id = ?",
                 [status, user_id, ctx.user_id])
    log_activity(ctx.user_id, "user_status_changed",
                 f"Changed user ID {user_id} status to {status}")
    return json_response({"success": True, "message": "User status updated"})


@router.api_route("/api/users.php", methods=["GET", "POST"])
@router.api_route("/api/users", methods=["GET", "POST"])
async def users_endpoint(request: Request, ctx: Ctx = Depends(get_auth_ctx)):
    action = ctx.q("action") or "list"

    if ctx.method == "GET":
        handlers = {
            "get": get_user, "dropdown": users_dropdown, "profile": get_profile,
            "activity": get_activity, "datatable": users_datatable,
        }
        return handlers.get(action, list_users)(ctx)

    if ctx.method == "POST":
        handlers = {
            "create": create_user, "update": update_user, "delete": delete_user,
            "profile": update_profile, "password": change_password, "toggle": toggle_status,
        }
        handler = handlers.get(action)
        if not handler:
            return json_response({"error": "Invalid action"}, 400)
        return await handler(ctx)

    return json_response({"error": "Method not allowed"}, 405)
