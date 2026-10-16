"""
Profile, Notifications and News — ports of public/api/profile.php,
public/api/notifications.php and public/api/news.php.
"""
from __future__ import annotations

import logging
import re

from fastapi import APIRouter, Depends, Request

from core.context import Ctx, get_auth_ctx, get_ctx
from core.helpers import (
    create_notification, db_table_exists, generate_hash, generate_token,
    json_response, log_activity, sanitize, to_int,
)

router = APIRouter()
client_logger = logging.getLogger("g1t.client")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]*>", "", str(value or ""))


# ═══════════════════════════════ PROFILE ════════════════════════════════════
@router.api_route("/api/profile.php", methods=["GET", "POST"])
@router.api_route("/api/profile", methods=["GET", "POST"])
async def profile_endpoint(request: Request, ctx: Ctx = Depends(get_auth_ctx)):
    action = ctx.q("action") or "get"
    user_id = ctx.user_id

    if ctx.method == "GET":
        if action == "token":
            row = ctx.db.query("SELECT api_token FROM users WHERE id=?", [user_id]).fetch()
            return json_response({"success": True,
                                  "api_token": row.get("api_token") if row else None})

        if action == "activity":
            limit = max(1, min(200, ctx.q_int("limit", 50)))
            offset = max(0, ctx.q_int("start", 0))
            rows = ctx.db.query(
                f"SELECT * FROM user_activity WHERE user_id=? "
                f"ORDER BY created_at DESC LIMIT {offset},{limit}", [user_id]).fetchall()
            total = to_int(ctx.db.query(
                "SELECT COUNT(*) c FROM user_activity WHERE user_id=?", [user_id]).scalar())
            return json_response({"success": True, "data": rows, "total": total})

        profile = ctx.db.query(
            "SELECT u.id,u.username,u.email,u.role,u.status,u.api_token,u.created_at,"
            "u.last_login,p.full_name,p.phone,p.address,p.company,p.timezone,p.avatar "
            "FROM users u LEFT JOIN user_profiles p ON p.user_id=u.id WHERE u.id=?",
            [user_id]).fetch()
        if not profile:
            return json_response({"error": "Profile not found"}, 404)

        profile = dict(profile)
        profile["balances"] = ctx.db.query(
            "SELECT currency,balance FROM user_balances WHERE user_id=?", [user_id]
        ).fetch_key_pair()
        parent_id = to_int(ctx.session.get("parent_id"))
        if parent_id:
            profile["parent"] = ctx.db.query(
                "SELECT id,username,email FROM users WHERE id=?", [parent_id]).fetch()
        return json_response({"success": True, "profile": profile})

    if ctx.method != "POST":
        return json_response({"error": "Method not allowed"}, 405)

    body = await ctx.body()

    if action == "update":
        full_name = str(body.get("full_name") or body.get("name") or "").strip()
        phone = str(body.get("phone") or body.get("contact") or "").strip()
        address = str(body.get("address") or "").strip()
        company = str(body.get("company") or body.get("cname") or "").strip()
        timezone = str(body.get("timezone") or "UTC").strip() or "UTC"
        email = str(body.get("email") or "").strip()

        if email and not EMAIL_RE.match(email):
            return json_response({"error": "Invalid email address"}, 400)

        exists = ctx.db.query("SELECT id FROM user_profiles WHERE user_id=?", [user_id]).fetch()
        if exists:
            ctx.db.query(
                "UPDATE user_profiles SET full_name=?,phone=?,address=?,company=?,timezone=? "
                "WHERE user_id=?",
                [full_name, phone, address, company, timezone, user_id])
        else:
            ctx.db.query(
                "INSERT INTO user_profiles (user_id,full_name,phone,address,company,timezone) "
                "VALUES (?,?,?,?,?,?)",
                [user_id, full_name, phone, address, company, timezone])
        if email:
            ctx.db.query("UPDATE users SET email=? WHERE id=?", [email, user_id])

        log_activity(user_id, "profile_update", "Updated profile information")
        return json_response({"success": True, "message": "Profile updated successfully"})

    if action == "password":
        current = str(body.get("current_password") or body.get("opassword") or "")
        new = str(body.get("new_password") or body.get("npassword") or "")
        confirm = str(body.get("confirm_password") or body.get("cpassword") or "")

        if len(new) < 6:
            return json_response({"error": "Password must be at least 6 characters"}, 400)
        if new != confirm:
            return json_response({"error": "Passwords do not match"}, 400)

        row = ctx.db.query("SELECT password FROM users WHERE id=?", [user_id]).fetch()
        if not row or str(row["password"]) != generate_hash(current):
            return json_response({"error": "Current password is incorrect"}, 400)

        ctx.db.query("UPDATE users SET password=? WHERE id=?", [generate_hash(new), user_id])
        log_activity(user_id, "password_change", "Changed password")
        return json_response({"success": True, "message": "Password changed successfully"})

    if action == "token":
        token = generate_token()
        ctx.db.query("UPDATE users SET api_token=? WHERE id=?", [token, user_id])
        log_activity(user_id, "token_regenerate", "Regenerated API token")
        return json_response({"success": True, "api_token": token})

    return json_response({"error": "Invalid action"}, 400)


# ══════════════════════════ NOTIFICATIONS ═══════════════════════════════════
@router.api_route("/api/notifications.php", methods=["GET", "POST"])
@router.api_route("/api/notifications", methods=["GET", "POST"])
async def notifications_endpoint(request: Request, ctx: Ctx = Depends(get_auth_ctx)):
    action = ctx.q("action") or "list"
    user_id = ctx.user_id

    if ctx.method == "GET":
        if action == "unread":
            count = to_int(ctx.db.query(
                "SELECT COUNT(*) as count FROM notifications WHERE user_id = ? AND is_read = 0",
                [user_id]).scalar())
            return json_response({"success": True, "count": count})

        limit = max(1, min(500, ctx.q_int("limit", 20)))
        offset = max(0, ctx.q_int("offset", 0))
        where = "user_id = ?"
        params: list = [user_id]
        if ctx.q("unread"):
            where += " AND is_read = 0"
        rows = ctx.db.query(
            f"SELECT * FROM notifications WHERE {where} "
            f"ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}", params).fetchall()
        return json_response({"success": True, "data": rows})

    if ctx.method != "POST":
        return json_response({"error": "Method not allowed"}, 405)

    body = await ctx.body()

    if action == "mark_read":
        notification_id = to_int(body.get("id"))
        if not notification_id:
            return json_response({"error": "Notification ID required"}, 400)
        ctx.db.query("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
                     [notification_id, user_id])
        return json_response({"success": True, "message": "Notification marked as read"})

    if action == "mark_all_read":
        ctx.db.query("UPDATE notifications SET is_read = 1 WHERE user_id = ?", [user_id])
        return json_response({"success": True, "message": "All notifications marked as read"})

    if action == "delete":
        notification_id = to_int(body.get("id"))
        if not notification_id:
            return json_response({"error": "Notification ID required"}, 400)
        ctx.db.query("DELETE FROM notifications WHERE id = ? AND user_id = ?",
                     [notification_id, user_id])
        return json_response({"success": True, "message": "Notification deleted"})

    return json_response({"error": "Invalid action"}, 400)


# ═════════════════════════════════ NEWS ═════════════════════════════════════
@router.api_route("/api/news.php", methods=["GET", "POST"])
@router.api_route("/api/news", methods=["GET", "POST"])
async def news_endpoint(request: Request, ctx: Ctx = Depends(get_auth_ctx)):
    action = ctx.q("action") or "list"
    user_id, role = ctx.user_id, ctx.role

    if ctx.method == "GET":
        if action == "get":
            news_id = ctx.q_int("id")
            if not news_id:
                return json_response({"error": "News ID required"}, 400)
            row = ctx.db.query(
                "SELECT n.*, u.username as author_name FROM news n "
                "JOIN users u ON n.author_id = u.id WHERE n.id = ?", [news_id]).fetch()
            if not row:
                return json_response({"error": "News not found"}, 404)
            return json_response({"success": True, "data": row})

        if action == "datatable":
            if role != "admin":
                return json_response({"error": "Only admins can manage Agent news"}, 403)
            params_get = ctx.all_params()
            draw = to_int(params_get.get("draw"), 1)
            start = max(0, to_int(params_get.get("start"), 0))
            length = to_int(params_get.get("length"), 25)
            length = 25 if length < 1 or length > 2000 else length
            search = params_get.get("search[value]") or params_get.get("search") or ""

            where = "author_id = ?"
            params: list = [user_id]
            if search:
                where += " AND (title LIKE ? OR content LIKE ?)"
                params += [f"%{search}%"] * 2

            total = to_int(ctx.db.query(
                f"SELECT COUNT(*) as count FROM news WHERE {where}", params).scalar())
            rows = ctx.db.query(
                f"SELECT * FROM news WHERE {where} ORDER BY created_at DESC "
                f"LIMIT {start}, {length}", params).fetchall()

            data = []
            for row in rows:
                status_badge = ('<span class="label label-success">Published</span>'
                                if row.get("status") == "published"
                                else '<span class="label label-warning">Draft</span>')
                target = str(row.get("target_role") or "")
                target_badge = f'<span class="label label-info">{target.capitalize()}</span>'
                excerpt = _strip_tags(row.get("content"))[:100] + "..."
                data.append([
                    row.get("title"), excerpt, target_badge, status_badge,
                    row.get("published_at"),
                    f'<a href="#" class="btn btn-mini btn-info" onclick="viewNews({row["id"]})">'
                    f'<i class="icon-eye-open"></i></a> '
                    f'<a href="#" class="btn btn-mini btn-warning" onclick="editNews({row["id"]})">'
                    f'<i class="icon-edit"></i></a> '
                    f'<a href="#" class="btn btn-mini btn-danger" onclick="deleteNews({row["id"]})">'
                    f'<i class="icon-trash"></i></a>',
                ])

            return json_response({"draw": draw, "recordsTotal": total,
                                  "recordsFiltered": total, "data": data})

        limit = max(1, min(200, ctx.q_int("limit", 10)))
        rows = ctx.db.query(
            f"SELECT n.*, u.username as author_name FROM news n "
            f"JOIN users u ON n.author_id = u.id "
            f"WHERE n.status = 'published' AND (n.target_role = 'all' OR n.target_role = ?) "
            f"ORDER BY n.published_at DESC LIMIT {limit}", [role]).fetchall()
        return json_response({"success": True, "data": rows})

    if ctx.method != "POST":
        return json_response({"error": "Method not allowed"}, 405)

    if role != "admin":
        verb = {"create": "create", "update": "update", "delete": "delete"}.get(action, "manage")
        return json_response({"error": f"Only admins can {verb} Agent news"}, 403)

    body = await ctx.body()

    if action == "create":
        title = sanitize(body.get("title") or "")
        content = body.get("content") or ""
        target_role = sanitize(body.get("target_role") or "all")
        status = sanitize(body.get("status") or "published")
        if not title or not content:
            return json_response({"error": "Title and content are required"}, 400)

        result = ctx.db.query(
            "INSERT INTO news (author_id, title, content, target_role, status, published_at) "
            "VALUES (?, ?, ?, ?, ?, NOW())",
            [user_id, title, content, target_role, status])
        news_id = result.lastrowid

        if target_role == "all":
            users = ctx.db.query("SELECT id FROM users WHERE status = 'active'").fetchall()
        else:
            users = ctx.db.query(
                "SELECT id FROM users WHERE role = ? AND status = 'active'", [target_role]).fetchall()
        for user in users:
            create_notification(user["id"], "New Announcement", title, "info")

        log_activity(user_id, "news_created", f"Created news: {title}")
        return json_response({"success": True, "message": "News created successfully",
                              "id": news_id})

    if action == "update":
        news_id = to_int(body.get("id"))
        if not news_id:
            return json_response({"error": "News ID required"}, 400)
        if not ctx.db.query("SELECT * FROM news WHERE id = ? AND author_id = ?",
                            [news_id, user_id]).fetch():
            return json_response({"error": "News not found"}, 404)

        fields, params = [], []
        for field in ("title", "content", "target_role", "status"):
            if field in body:
                fields.append(f"{field} = ?")
                params.append(sanitize(body[field]))
        if fields:
            params += [news_id, user_id]
            ctx.db.query(
                f"UPDATE news SET {', '.join(fields)} WHERE id = ? AND author_id = ?", params)

        log_activity(user_id, "news_updated", f"Updated news ID: {news_id}")
        return json_response({"success": True, "message": "News updated successfully"})

    if action == "delete":
        news_id = to_int(body.get("id"))
        if not news_id:
            return json_response({"error": "News ID required"}, 400)
        ctx.db.query("DELETE FROM news WHERE id = ? AND author_id = ?", [news_id, user_id])
        log_activity(user_id, "news_deleted", f"Deleted news ID: {news_id}")
        return json_response({"success": True, "message": "News deleted successfully"})

    return json_response({"error": "Invalid action"}, 400)




# Payment / Bank / Statements dispatcher

@router.api_route("/api/misc.php", methods=["GET", "POST"])
@router.api_route("/api/misc", methods=["GET", "POST"])
async def misc_endpoint(request: Request, action: str = "",
                        currency: str = "USD",
                        ctx: Ctx = Depends(get_auth_ctx)):
    db = Database.get_instance()

    if action == "payment_requests":
        rows = db.query(
            "SELECT * FROM payment_requests WHERE user_id = ? ORDER BY created_at DESC",
            [ctx.user_id]).fetchall()
        return json_response({"rows": rows})

    if action == "payment_request_create":
        body = await request.json()
        cur = body.get("currency", "USD")
        if cur not in ("USD", "EUR", "GBP"):
            return json_response({"error": "Invalid currency"}, 422)
        amount = float(body.get("amount") or 0)
        if amount <= 0:
            return json_response({"error": "Amount must be positive"}, 422)
        method = sanitize(body.get("method", ""), 50)
        details = sanitize(body.get("details", ""), 500)
        db.query("INSERT INTO payment_requests (user_id, currency, amount, method, details) "
                 "VALUES (?, ?, ?, ?, ?)", [ctx.user_id, cur, amount, method, details])
        create_notification(ctx.user_id, f"Payment request for {amount:.2f} {cur} submitted")
        return json_response({"success": True})

    if action == "bank_accounts":
        if not db_table_exists(db, "bank_accounts"):
            return json_response({"rows": []})
        rows = db.query("SELECT * FROM bank_accounts WHERE user_id = ? ORDER BY created_at DESC",
                        [ctx.user_id]).fetchall()
        return json_response({"rows": rows})

    if action == "bank_account_save":
        body = await request.json()
        bname = sanitize(body.get("bank_name", ""), 100)
        atitle = sanitize(body.get("account_title", ""), 150)
        anum = sanitize(body.get("account_number", ""), 100)
        cur = body.get("currency", "USD")
        atype = sanitize(body.get("account_type", "bank"), 30)
        if not bname or not anum:
            return json_response({"error": "Bank name and account number required"}, 422)
        if not db_table_exists(db, "bank_accounts"):
            db.query("CREATE TABLE IF NOT EXISTS bank_accounts ("
                     "id INT UNSIGNED NOT NULL AUTO_INCREMENT, "
                     "user_id INT UNSIGNED NOT NULL, "
                     "bank_name VARCHAR(100) NOT NULL, "
                     "account_title VARCHAR(150) NOT NULL, "
                     "account_number VARCHAR(100) NOT NULL, "
                     "currency VARCHAR(10) DEFAULT 'USD', "
                     "account_type VARCHAR(30) DEFAULT 'bank', "
                     "created_at DATETIME DEFAULT CURRENT_TIMESTAMP, "
                     "PRIMARY KEY(id), KEY idx_user(user_id))")
        db.query("INSERT INTO bank_accounts (user_id,bank_name,account_title,"
                 "account_number,currency,account_type) VALUES (?,?,?,?,?,?)",
                 [ctx.user_id, bname, atitle, anum, cur, atype])
        return json_response({"success": True})

    if action == "bank_account_delete":
        body = await request.json()
        db.query("DELETE FROM bank_accounts WHERE id = ? AND user_id = ?",
                 [body.get("id"), ctx.user_id])
        return json_response({"success": True})

    if action == "statements":
        from_d = request.query_params.get("from", "2020-01-01")
        to_d = request.query_params.get("to", "2099-12-31")
        rows = db.query(
            "SELECT date_time AS date, "
            "CONCAT('OTP from ', cli, ' on ', number) AS description, "
            "user_payout AS credit, 0 AS debit, 0 AS balance "
            "FROM sms_cdr WHERE user_id = ? AND currency = ? "
            "AND date_time BETWEEN ? AND CONCAT(?, ' 23:59:59') "
            "ORDER BY date_time",
            [ctx.user_id, currency, from_d, to_d]).fetchall()
        bal = 0.0
        for r in rows:
            bal += float(r.get("credit") or 0) - float(r.get("debit") or 0)
            r["balance"] = round(bal, 6)
        return json_response({"rows": rows})

    return json_response({"error": "Unknown action"}, 400)


# ── client-side error reporting ──────────────────────────────────────────────
# The browser can't write to the server's terminal on its own. This endpoint
# is the bridge: client-error-reporter.js (loaded on every page) catches any
# uncaught JS error or rejected promise in the browser and POSTs it here, and
# we print it straight to the same terminal `python run.py` runs in — no
# browser devtools needed, just copy/paste from the terminal.
@router.api_route("/api/client-error", methods=["POST"])
async def client_error_endpoint(request: Request, ctx: Ctx = Depends(get_ctx)):
    try:
        body = await request.json()
    except Exception:
        body = {}

    message = str(body.get("message") or "(no message)")[:2000]
    source = str(body.get("source") or "")[:500]
    line = body.get("line") or "?"
    col = body.get("col") or "?"
    stack = str(body.get("stack") or "")[:4000]
    url = str(body.get("url") or "")[:500]
    kind = str(body.get("kind") or "error")[:40]
    user = f"user #{ctx.user_id} ({ctx.role})" if getattr(ctx, "user_id", None) else "not logged in"

    client_logger.error(
        "\n"
        "\U0001F534 ================ BROWSER ERROR (%s) ================\n"
        "  Page    : %s\n"
        "  User    : %s\n"
        "  Message : %s\n"
        "  At      : %s:%s:%s\n"
        "  Stack   : %s\n"
        "======================================================",
        kind, url, user, message, source, line, col, stack or "(none)",
    )
    return json_response({"success": True})
