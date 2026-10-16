"""
Admin API — port of public/api/admin.php (all 31 actions).

Security note: inbound SMS bodies and verification codes are intentionally not
returned or stored here. The API exposes only an otp_detected flag.

TWO BUGS FIXED IN THIS PORT
  1. `system_settings.setting_type` is an ENUM('string','number','boolean').
     The integration code wrote 'json', so MySQL raised "Data truncated for
     column 'setting_type'" and Save HTTP Provider / Save Webhook / Generate
     API Token every one of them returned 500. ensure_json_setting_type()
     widens the ENUM once, automatically, and the writes now succeed.
  2. `pgrep -f jasmind` matched the shell running the check itself, so the
     panel always reported Jasmin as running. Replaced with `pgrep -x`.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import re
import secrets
import shutil
import subprocess
from datetime import datetime

from fastapi import APIRouter, Depends, Request

from core import config
from core.context import Ctx, get_ctx
from core.db import Database
from core.helpers import (
    ApiError, clean_string, create_notification, db_column_exists, db_table_exists,
    generate_hash, generate_token, json_response, limit_value, log_activity,
    manager_owner_sql, offset_value, to_bool_int, to_float, to_int,
)
from core.smpp_service import service as smpp_service
from core.sms_ingest import ingest_sms

logger = logging.getLogger("g1t.admin")
router = APIRouter()

USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,100}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PREFIX_RE = re.compile(r"^\+?[0-9]{1,20}$")
NUMBER_RE = re.compile(r"^\+?[0-9]{4,30}$")
CONFIG_NAME_RE = re.compile(r"^[A-Za-z0-9_. -]{1,50}$")

_setting_type_checked = False


def ensure_json_setting_type(db: Database) -> None:
    """Widen system_settings.setting_type so 'json' is a legal value.

    Without this every integration save fails with "Data truncated for column
    'setting_type' at row 1". Runs once per process and is a no-op if the ENUM
    already includes json.
    """
    global _setting_type_checked
    if _setting_type_checked:
        return
    _setting_type_checked = True
    try:
        row = db.query(
            "SELECT COLUMN_TYPE ct FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='system_settings' "
            "AND COLUMN_NAME='setting_type' LIMIT 1").fetch()
        if not row:
            return
        if "json" in str(row["ct"]).lower():
            return
        db.query("ALTER TABLE system_settings MODIFY COLUMN setting_type "
                 "ENUM('string','number','boolean','json') NOT NULL DEFAULT 'string'")
        logger.info("system_settings.setting_type widened to include 'json'")
    except Exception as exc:
        logger.warning("Could not widen setting_type ENUM: %s", exc)


def password_hash(password: str) -> str:
    """Stand-in for PHP's password_hash(). Salted PBKDF2-SHA256, self-describing
    so verify_password can read it back."""
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000).hex()
    return f"pbkdf2$120000${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    if not stored:
        return False
    if stored.startswith("pbkdf2$"):
        try:
            _, rounds, salt, digest = stored.split("$", 3)
            check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(),
                                        int(rounds)).hex()
            return secrets.compare_digest(check, digest)
        except Exception:
            return False
    return secrets.compare_digest(password, stored)


def jasmin_running() -> bool:
    """Exact-name match: `pgrep -f jasmind` also matched its own shell."""
    if not shutil.which("pgrep"):
        return False
    try:
        result = subprocess.run(["pgrep", "-x", "jasmind"], capture_output=True, timeout=3)
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        return False


def normalize_sms_number(value) -> str:
    value = str(value or "")
    value = value.lstrip("\ufeff").replace("\xa0", " ").strip()
    m = re.match(r"^=\s*[\"'](.+)[\"']$", value)
    if m:
        value = m.group(1)
    value = value.strip("'\"")
    return re.sub(r"[\s\-().]", "", value).strip()


def safe_scalar(db: Database, sql: str, params=None, fallback=0,
                warnings=None, label: str = ""):
    """A missing optional table must never blank the whole Admin overview."""
    try:
        row = db.query(sql, params or []).fetch()
        if not row:
            return fallback
        value = list(row.values())[0]
        return value if isinstance(value, (int, float)) else to_float(value, fallback)
    except Exception as exc:
        logger.warning("Admin safe scalar failed [%s]: %s", label, exc)
        if warnings is not None and label:
            warnings.append(label)
        return fallback


def safe_rows(db: Database, sql: str, params=None, warnings=None, label: str = "") -> list:
    try:
        return db.query(sql, params or []).fetchall()
    except Exception as exc:
        logger.warning("Admin safe rows failed [%s]: %s", label, exc)
        if warnings is not None and label:
            warnings.append(label)
        return []


def role_parent_valid(db: Database, role: str, parent_id) -> bool:
    if role in ("manager", "test"):
        return True  # Managers and Test accounts are owned directly by Admin
    if role == "agent":
        return bool(parent_id) and bool(db.query(
            "SELECT id FROM users WHERE id=? AND role='manager' AND status='active' LIMIT 1",
            [parent_id]).fetch())
    if role == "client":
        return bool(parent_id) and bool(db.query(
            "SELECT id FROM users WHERE id=? AND role='agent' AND status='active' LIMIT 1",
            [parent_id]).fetch())
    return False


def parse_uploaded_numbers(content: str, filename: str) -> list:
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()
    if ext not in ("txt", "csv"):
        raise ApiError("Only TXT and CSV number files are supported", 400)

    numbers, seen = [], set()
    for index, line in enumerate(re.split(r"\r\n|\r|\n", content)):
        line = line.strip()
        if not line:
            continue
        if ext == "csv":
            raw = line.split(",")[0].strip().strip('"').strip("'")
            if index == 0 and re.match(r"^(number|phone|msisdn)$",
                                       raw.lstrip("\ufeff"), re.IGNORECASE):
                continue
            number = normalize_sms_number(raw)
        else:
            number = normalize_sms_number(line)
        if not number or not NUMBER_RE.match(number):
            continue
        if number not in seen:
            seen.add(number)
            numbers.append(number)
    return numbers


# ═══════════════════════════════ SUMMARY ════════════════════════════════════
def admin_summary(ctx: Ctx):
    db = ctx.db
    warnings: list = []
    counts = {
        "manager": 0, "agent": 0, "client": 0, "numbers": 0, "ranges": 0,
        "sms_total": 0, "sms_today": 0, "otp_total": 0, "otp_today": 0,
        "pending_payments": 0, "active_manager": 0, "active_agent": 0, "active_client": 0,
    }

    for role in ("manager", "agent", "client"):
        counts[role] = to_int(safe_scalar(
            db, "SELECT COUNT(*) c FROM users WHERE role=?", [role], 0, warnings, f"{role}_count"))
        counts[f"active_{role}"] = to_int(safe_scalar(
            db, "SELECT COUNT(*) c FROM users WHERE role=? AND status='active'",
            [role], 0, warnings, f"active_{role}_count"))

    if db_table_exists(db, "sms_numbers"):
        counts["numbers"] = to_int(safe_scalar(
            db, "SELECT COUNT(*) c FROM sms_numbers", [], 0, warnings, "number_count"))
    if db_table_exists(db, "sms_ranges"):
        counts["ranges"] = to_int(safe_scalar(
            db, "SELECT COUNT(*) c FROM sms_ranges", [], 0, warnings, "range_count"))

    has_cdr = db_table_exists(db, "sms_cdr")
    has_otp = has_cdr and db_column_exists(db, "sms_cdr", "otp_detected")
    if has_cdr:
        counts["sms_total"] = to_int(safe_scalar(
            db, "SELECT COALESCE(SUM(sms_count),0) c FROM sms_cdr", [], 0, warnings, "sms_total"))
        counts["sms_today"] = to_int(safe_scalar(
            db, "SELECT COALESCE(SUM(sms_count),0) c FROM sms_cdr WHERE DATE(date_time)=UTC_DATE()",
            [], 0, warnings, "sms_today"))
        if has_otp:
            counts["otp_total"] = to_int(safe_scalar(
                db, "SELECT COALESCE(SUM(otp_detected),0) c FROM sms_cdr",
                [], 0, warnings, "otp_total"))
            counts["otp_today"] = to_int(safe_scalar(
                db, "SELECT COALESCE(SUM(otp_detected),0) c FROM sms_cdr "
                    "WHERE DATE(date_time)=UTC_DATE()", [], 0, warnings, "otp_today"))
    if db_table_exists(db, "payment_requests"):
        counts["pending_payments"] = to_int(safe_scalar(
            db, "SELECT COUNT(*) c FROM payment_requests WHERE status='pending'",
            [], 0, warnings, "pending_payments"))

    owner_num = manager_owner_sql("n.assigned_to")
    owner_cdr = manager_owner_sql("c.user_id")
    top_managers = safe_rows(db,
        f"SELECT m.id,m.username,m.status, "
        f"(SELECT COUNT(*) FROM users a WHERE a.role='agent' AND a.parent_id=m.id) agent_count, "
        f"(SELECT COUNT(DISTINCT n.range_id) FROM sms_numbers n WHERE {owner_num}=m.id) range_count, "
        f"(SELECT COUNT(*) FROM sms_numbers n WHERE {owner_num}=m.id) number_count, "
        f"(SELECT COALESCE(SUM(c.sms_count),0) FROM sms_cdr c WHERE {owner_cdr}=m.id "
        f" AND c.date_time>=DATE_SUB(UTC_TIMESTAMP(),INTERVAL 30 DAY)) sms_30d "
        f"FROM users m WHERE m.role='manager' "
        f"ORDER BY sms_30d DESC,m.created_at DESC LIMIT 8", [], warnings, "manager_performance")

    recent = []
    if has_cdr:
        otp_expr = "c.otp_detected" if has_otp else "0"
        recent = safe_rows(db,
            f"SELECT c.date_time,c.number,c.cli,c.sms_count,c.sms_type,{otp_expr} otp_detected,"
            f"c.currency,r.range_name, "
            f"CASE WHEN u.role='agent' THEN mgr1.username WHEN u.role='client' THEN mgr2.username "
            f" ELSE '-' END manager_name, "
            f"CASE WHEN u.role='client' THEN pu.username WHEN u.role='agent' THEN u.username "
            f" ELSE '-' END agent_name, "
            f"CASE WHEN u.role='client' THEN u.username ELSE '-' END client_name "
            f"FROM sms_cdr c "
            f"LEFT JOIN sms_ranges r ON r.id=c.range_id "
            f"LEFT JOIN users u ON u.id=c.user_id "
            f"LEFT JOIN users pu ON pu.id=u.parent_id "
            f"LEFT JOIN users mgr1 ON mgr1.id=u.parent_id AND u.role='agent' "
            f"LEFT JOIN users mgr2 ON mgr2.id=pu.parent_id AND u.role='client' "
            f"ORDER BY c.date_time DESC LIMIT 12", [], warnings, "recent_sms")

    warnings = sorted(set(warnings))
    return json_response({"success": True, "counts": counts, "top_managers": top_managers,
                          "recent_sms": recent, "degraded": bool(warnings),
                          "warnings": warnings})


# ═══════════════════════════════ USERS ══════════════════════════════════════
def admin_users(ctx: Ctx):
    db = ctx.db
    role = clean_string(ctx.q("role") or "manager", 20)
    status = clean_string(ctx.q("status") or "", 20)
    search = clean_string(ctx.q("search") or "", 100)
    limit = limit_value(ctx.q("limit"), 100, 500)
    offset = offset_value(ctx.q("offset"))

    if role not in ("manager", "agent", "client", "test"):
        return json_response({"error": "Invalid role"}, 400)

    has_profiles = db_table_exists(db, "user_profiles")
    has_skype = has_profiles and db_column_exists(db, "user_profiles", "skype_id")
    has_country = has_profiles and db_column_exists(db, "user_profiles", "country")
    has_balances = db_table_exists(db, "user_balances")
    has_numbers = db_table_exists(db, "sms_numbers")

    where, params = "u.role=?", [role]
    if status in ("active", "inactive", "suspended"):
        where += " AND u.status=?"
        params.append(status)
    if search:
        if has_profiles:
            parts = ["u.username LIKE ?", "COALESCE(u.email,'') LIKE ?",
                     "COALESCE(p.full_name,'') LIKE ?", "COALESCE(p.phone,'') LIKE ?",
                     "COALESCE(p.company,'') LIKE ?", "COALESCE(p.address,'') LIKE ?"]
            if has_skype:
                parts.append("COALESCE(p.skype_id,'') LIKE ?")
            if has_country:
                parts.append("COALESCE(p.country,'') LIKE ?")
            where += " AND (" + " OR ".join(parts) + ")"
            params += [f"%{search}%"] * len(parts)
        else:
            where += " AND (u.username LIKE ? OR COALESCE(u.email,'') LIKE ?)"
            params += [f"%{search}%"] * 2

    profile_join = " LEFT JOIN user_profiles p ON p.user_id=u.id " if has_profiles else ""
    if has_profiles:
        profile_select = ("p.full_name,p.phone,p.company,p.address,"
                          + ("p.skype_id" if has_skype else "NULL skype_id") + ","
                          + ("p.country" if has_country else "NULL country"))
    else:
        profile_select = ("NULL full_name,NULL phone,NULL company,NULL address,"
                          "NULL skype_id,NULL country")

    try:
        total = to_int(db.query(
            f"SELECT COUNT(*) c FROM users u {profile_join} WHERE {where}", params).scalar())
        rows = db.query(
            f"SELECT u.id,u.username,u.email,u.role,u.parent_id,u.status,u.last_login,"
            f"u.created_at,{profile_select}, parent.username parent_username,"
            f"parent.role parent_role FROM users u {profile_join} "
            f"LEFT JOIN users parent ON parent.id=u.parent_id "
            f"WHERE {where} ORDER BY u.created_at DESC,u.id DESC LIMIT {offset},{limit}",
            params).fetchall()
    except Exception as exc:
        logger.warning("Admin users primary query failed: %s", exc)
        simple_where, simple_params = "role=?", [role]
        if status in ("active", "inactive", "suspended"):
            simple_where += " AND status=?"
            simple_params.append(status)
        if search:
            simple_where += " AND (username LIKE ? OR COALESCE(email,'') LIKE ?)"
            simple_params += [f"%{search}%"] * 2
        total = to_int(db.query(
            f"SELECT COUNT(*) c FROM users WHERE {simple_where}", simple_params).scalar())
        rows = db.query(
            f"SELECT id,username,email,role,parent_id,status,last_login,created_at,"
            f"NULL full_name,NULL phone,NULL company,NULL address,NULL skype_id,NULL country,"
            f"NULL parent_username,NULL parent_role FROM users WHERE {simple_where} "
            f"ORDER BY created_at DESC,id DESC LIMIT {offset},{limit}", simple_params).fetchall()

    if rows:
        ids = [to_int(r["id"]) for r in rows]
        ph = ",".join("?" * len(ids))
        children = {to_int(x["parent_id"]): to_int(x["c"]) for x in db.query(
            f"SELECT parent_id,COUNT(*) c FROM users WHERE parent_id IN ({ph}) "
            f"GROUP BY parent_id", ids).fetchall()}
        numbers = {}
        if has_numbers:
            numbers = {to_int(x["assigned_to"]): to_int(x["c"]) for x in db.query(
                f"SELECT assigned_to,COUNT(*) c FROM sms_numbers WHERE assigned_to IN ({ph}) "
                f"GROUP BY assigned_to", ids).fetchall()}
        balances: dict = {}
        if has_balances:
            for x in db.query(
                f"SELECT user_id,currency,balance FROM user_balances WHERE user_id IN ({ph}) "
                f"ORDER BY currency", ids).fetchall():
                balances.setdefault(to_int(x["user_id"]), []).append(
                    f"{x['currency']}:{to_float(x['balance']):.4f}")
        for row in rows:
            uid = to_int(row["id"])
            row["child_count"] = children.get(uid, 0)
            row["direct_number_count"] = numbers.get(uid, 0)
            row["balances"] = ", ".join(balances.get(uid, []))

    return json_response({"success": True, "total": total, "data": rows})


async def admin_create_user(ctx: Ctx):
    db, admin_id = ctx.db, ctx.user_id
    body = await ctx.body()

    username = clean_string(body.get("username"), 100)
    password = str(body.get("password") or "")
    email = clean_string(body.get("email"), 255)
    full_name = clean_string(body.get("full_name"), 255)
    phone = clean_string(body.get("phone"), 50)
    skype_id = clean_string(body.get("skype_id"), 100)
    company = clean_string(body.get("company"), 255)
    address = clean_string(body.get("address"), 2000)
    country = clean_string(body.get("country"), 120)
    role = clean_string(body.get("role"), 20)
    parent_id = to_int(body.get("parent_id")) or None

    if not USERNAME_RE.match(username):
        return json_response(
            {"error": "Username must be 3-100 letters, numbers, dot, dash or underscore"}, 400)
    if len(password) < 8:
        return json_response({"error": "Password must be at least 8 characters"}, 400)
    if email and not EMAIL_RE.match(email):
        return json_response({"error": "Invalid email address"}, 400)
    if role not in ("manager", "agent", "client", "test"):
        return json_response({"error": "Invalid role"}, 400)
    if not role_parent_valid(db, role, parent_id):
        return json_response({"error": "Select a valid parent account for this role"}, 400)
    if db.query("SELECT id FROM users WHERE username=? LIMIT 1", [username]).fetch():
        return json_response({"error": "Username already exists"}, 409)

    # Managers are directly owned by Admin; Agents by Managers; Clients by Agents.
    if role in ("manager", "test"):
        parent_id = admin_id

    try:
        with db.transaction() as tx:
            result = tx.query(
                "INSERT INTO users (username,password,email,role,parent_id,status,api_token) "
                "VALUES (?,?,?,?,?,'active',?)",
                [username, generate_hash(password), email or None, role, parent_id,
                 generate_token()])
            new_id = result.lastrowid
            tx.query("INSERT INTO user_profiles (user_id,full_name,phone,address,company) "
                     "VALUES (?,?,?,?,?)",
                     [new_id, full_name or None, phone or None, address or None, company or None])
            if db_column_exists(db, "user_profiles", "skype_id"):
                tx.query("UPDATE user_profiles SET skype_id=? WHERE user_id=?",
                         [skype_id or None, new_id])
            if db_column_exists(db, "user_profiles", "country"):
                tx.query("UPDATE user_profiles SET country=? WHERE user_id=?",
                         [country or None, new_id])
            tx.query("INSERT INTO user_balances (user_id,currency,balance) "
                     "VALUES (?, 'USD',0),(?, 'EUR',0),(?, 'GBP',0)", [new_id, new_id, new_id])
    except Exception as exc:
        logger.warning("Admin create user failed: %s", exc)
        return json_response({"error": "Could not create user"}, 500)

    log_activity(admin_id, "admin_user_created", f"Admin created {role}: {username}")
    return json_response({"success": True,
                          "message": f"{role.capitalize()} created successfully", "id": new_id})


async def admin_user_status(ctx: Ctx):
    body = await ctx.body()
    user_id = to_int(body.get("id"))
    status = clean_string(body.get("status"), 20)
    if not user_id or status not in ("active", "inactive", "suspended"):
        return json_response({"error": "Invalid user or status"}, 400)
    user = ctx.db.query("SELECT id,username,role FROM users WHERE id=? AND role<>'admin' LIMIT 1",
                        [user_id]).fetch()
    if not user:
        return json_response({"error": "User not found"}, 404)
    ctx.db.query("UPDATE users SET status=? WHERE id=?", [status, user_id])
    log_activity(ctx.user_id, "admin_user_status",
                 f"Set {user['role']} {user['username']} to {status}")
    return json_response({"success": True, "message": "Status updated"})


async def admin_delete_user(ctx: Ctx):
    db, admin_id = ctx.db, ctx.user_id
    body = await ctx.body()
    user_id = to_int(body.get("id"))
    if not user_id:
        return json_response({"error": "Invalid user"}, 400)
    user = db.query("SELECT id,username,role FROM users WHERE id=? AND role<>'admin' LIMIT 1",
                    [user_id]).fetch()
    if not user:
        return json_response({"error": "User not found"}, 404)

    children = to_int(db.query("SELECT COUNT(*) c FROM users WHERE parent_id=?",
                               [user_id]).scalar())
    numbers = to_int(db.query("SELECT COUNT(*) c FROM sms_numbers WHERE assigned_to=?",
                              [user_id]).scalar()) if db_table_exists(db, "sms_numbers") else 0
    if children or numbers:
        return json_response(
            {"error": "Cannot delete this user while child accounts or assigned numbers still "
                      "exist. Suspend the account instead."}, 409)

    # Legacy ranges may still point at an old Manager. Re-home them to Admin
    # first so the FK cannot cascade-delete inventory.
    if user["role"] == "manager" and db_table_exists(db, "sms_ranges"):
        db.query("UPDATE sms_ranges SET manager_id=? WHERE manager_id=?", [admin_id, user_id])

    db.query("DELETE FROM users WHERE id=?", [user_id])
    log_activity(admin_id, "admin_user_deleted", f"Deleted {user['role']}: {user['username']}")
    return json_response({"success": True, "message": "User deleted successfully"})


# ═══════════════════════════════ RANGES ═════════════════════════════════════
def admin_ranges(ctx: Ctx):
    db = ctx.db
    search = clean_string(ctx.q("search") or "", 100)
    status = clean_string(ctx.q("status") or "", 20)
    limit = limit_value(ctx.q("limit"), 100, 500)
    offset = offset_value(ctx.q("offset"))

    where, params = "1=1", []
    if search:
        where += " AND (r.range_name LIKE ? OR r.prefix LIKE ? OR COALESCE(r.memo,'') LIKE ?)"
        params += [f"%{search}%"] * 3
    if status in ("active", "inactive", "exhausted"):
        where += " AND r.status=?"
        params.append(status)

    total = to_int(db.query(f"SELECT COUNT(*) c FROM sms_ranges r WHERE {where}", params).scalar())

    def col(name, fallback):
        return f"r.{name}" if db_column_exists(db, "sms_ranges", name) else fallback

    rows = db.query(
        f"SELECT r.id,r.manager_id,r.range_name,r.prefix,r.currency,r.payout_1_1,r.payout_7_1,"
        f"r.payout_7_7,r.payout_30_45, "
        f"{col('payout_1_1_enabled','1')} payout_1_1_enabled,"
        f"{col('payout_7_1_enabled','1')} payout_7_1_enabled,"
        f"{col('payout_7_7_enabled','1')} payout_7_7_enabled,"
        f"{col('payout_30_45_enabled','1')} payout_30_45_enabled,"
        f"r.test_number,r.total_numbers,r.available_numbers,r.memo,r.status,"
        f"{col('request_enabled','1')} request_enabled,"
        f"{col('max_requests_per_agent','NULL')} max_requests_per_agent,"
        f"{col('max_numbers_per_agent_daily','NULL')} max_numbers_per_agent_daily,"
        f"r.created_at,r.updated_at,'All Managers' manager_name,'global' manager_status, "
        f"(SELECT COUNT(*) FROM sms_numbers n WHERE n.range_id=r.id) actual_total, "
        f"(SELECT COUNT(*) FROM sms_numbers n WHERE n.range_id=r.id AND n.assigned_to IS NULL "
        f" AND n.status='available') actual_available, "
        f"(SELECT COUNT(*) FROM sms_numbers n WHERE n.range_id=r.id "
        f" AND n.assigned_to IS NOT NULL) assigned_numbers "
        f"FROM sms_ranges r WHERE {where} ORDER BY r.created_at DESC,r.id DESC "
        f"LIMIT {offset},{limit}", params).fetchall()

    return json_response({"success": True, "total": total, "data": rows,
                          "scope": "all_managers"})


async def admin_save_range(ctx: Ctx):
    db, admin_id = ctx.db, ctx.user_id

    # Range creation accepts a multipart upload (numbers file) or plain JSON.
    upload_name, upload_content, body = "", "", {}
    content_type = (ctx.request.headers.get("content-type") or "").lower()
    if "multipart/form-data" in content_type:
        form = await ctx.request.form()
        body = {k: v for k, v in form.items() if not hasattr(v, "filename")}
        upload = form.get("numbersfile")
        if upload is not None and hasattr(upload, "filename") and upload.filename:
            raw = await upload.read()
            if len(raw) > 10 * 1024 * 1024:
                return json_response({"error": "Numbers file is too large (maximum 10 MB)"}, 400)
            upload_name = upload.filename
            upload_content = raw.decode("utf-8", errors="replace")
    else:
        body = await ctx.body()

    range_id = max(0, to_int(body.get("id")))
    name = clean_string(body.get("range_name") or body.get("rangename"), 255)
    prefix = clean_string(body.get("prefix"), 20)
    currency = clean_string(body.get("currency") or "USD", 3).upper()
    status = clean_string(body.get("status") or "active", 20)
    request_enabled = to_bool_int(body.get("request_enabled", 1))
    max_requests_raw = re.sub(r"[^0-9]", "", str(body.get("max_requests_per_agent") or ""))
    max_requests = to_int(max_requests_raw) if max_requests_raw and to_int(max_requests_raw) > 0 else None
    max_daily_raw = re.sub(r"[^0-9]", "", str(body.get("max_numbers_per_agent_daily") or ""))
    max_daily = to_int(max_daily_raw) if max_daily_raw and to_int(max_daily_raw) > 0 else None
    memo = clean_string(body.get("memo"), 2000)
    test_number = normalize_sms_number(body.get("test_number") or body.get("testnumber") or "")

    def payout(key):
        value = body.get(key, "")
        return to_float(value) if str(value) != "" else None

    p11, p71, p77, p3045 = (payout("payout_1_1"), payout("payout_7_1"),
                            payout("payout_7_7"), payout("payout_30_45"))
    toggles = {
        "request_enabled": request_enabled,
        "max_requests_per_agent": max_requests,
        "max_numbers_per_agent_daily": max_daily,
        "payout_1_1_enabled": to_bool_int(body.get("payout_1_1_enabled", 1)),
        "payout_7_1_enabled": to_bool_int(body.get("payout_7_1_enabled", 1)),
        "payout_7_7_enabled": to_bool_int(body.get("payout_7_7_enabled", 1)),
        "payout_30_45_enabled": to_bool_int(body.get("payout_30_45_enabled", 1)),
    }

    if not name or not prefix:
        return json_response({"error": "Range name and prefix are required"}, 400)
    if not PREFIX_RE.match(prefix):
        return json_response(
            {"error": "Prefix may contain digits and an optional leading + only"}, 400)
    if currency not in ("USD", "EUR", "GBP"):
        return json_response({"error": "Invalid currency"}, 400)
    if status not in ("active", "inactive", "exhausted"):
        return json_response({"error": "Invalid range status"}, 400)
    if p11 is None or p11 < 0 or any(v is not None and v < 0 for v in (p71, p77, p3045)):
        return json_response(
            {"error": "Payout values must be zero or greater; 1/1 payout is required"}, 400)
    if test_number and not NUMBER_RE.match(test_number):
        return json_response({"error": "Invalid test number"}, 400)

    existing = None
    if range_id:
        existing = db.query("SELECT * FROM sms_ranges WHERE id=? LIMIT 1", [range_id]).fetch()
        if not existing:
            return json_response({"error": "Range not found"}, 404)

    numbers: list = []
    if upload_content:
        numbers = parse_uploaded_numbers(upload_content, upload_name)
        if not numbers:
            return json_response(
                {"error": "No valid phone numbers were found in the uploaded file"}, 400)
    elif not existing:
        return json_response(
            {"error": "Upload a TXT or CSV numbers file when creating a range"}, 400)

    if test_number:
        digits = re.sub(r"\D+", "", test_number)
        matched = next((n for n in numbers
                        if n == test_number or re.sub(r"\D+", "", n) == digits), None)
        if matched:
            test_number = matched
        elif existing:
            row = db.query(
                "SELECT number FROM sms_numbers WHERE range_id=? "
                "AND REPLACE(number,'+','')=REPLACE(?,'+','') LIMIT 1",
                [range_id, test_number]).fetch()
            if row:
                test_number = row["number"]
            else:
                return json_response(
                    {"error": "Test number must belong to this range or be included in the "
                              "uploaded number file"}, 400)
        else:
            return json_response(
                {"error": "Test number must be included in the uploaded number file"}, 400)

    skipped: list = []
    try:
        with db.transaction() as tx:
            cols = ["manager_id", "range_name", "prefix", "currency", "payout_1_1", "payout_7_1",
                    "payout_7_7", "payout_30_45", "test_number", "memo", "status"]
            vals = [admin_id, name, prefix, currency, p11, p71, p77, p3045,
                    test_number or None, memo or None, status]
            # Optional toggle columns are only written when the matching
            # migration has been applied, so this still works on older databases.
            for col_name, value in toggles.items():
                if db_column_exists(db, "sms_ranges", col_name):
                    cols.append(col_name)
                    vals.append(value)
                else:
                    skipped.append(col_name)

            if existing:
                set_sql = ",".join(f"{c}=?" for c in cols)
                tx.query(f"UPDATE sms_ranges SET {set_sql} WHERE id=?", vals + [range_id])
                new_range_id = range_id
            else:
                placeholders = ",".join("?" * len(cols))
                result = tx.query(
                    f"INSERT INTO sms_ranges ({','.join(cols)}) VALUES ({placeholders})", vals)
                new_range_id = result.lastrowid

            inserted = duplicates = 0
            test_digits = re.sub(r"\D+", "", test_number) if test_number else ""
            for number in numbers:
                if tx.query("SELECT id FROM sms_numbers WHERE number=? LIMIT 1", [number]).fetch():
                    duplicates += 1
                    continue
                is_test = 1 if test_digits and re.sub(r"\D+", "", number) == test_digits else 0
                tx.query("INSERT INTO sms_numbers (range_id,number,is_test,status) "
                         "VALUES (?,?,?,'available')", [new_range_id, number, is_test])
                inserted += 1

            if test_number:
                matched_row = tx.query(
                    "SELECT id,number FROM sms_numbers WHERE range_id=? "
                    "AND REPLACE(number,'+','')=REPLACE(?,'+','') LIMIT 1",
                    [new_range_id, test_number]).fetch()
                if matched_row:
                    test_number = matched_row["number"]
                    tx.query("UPDATE sms_numbers SET is_test=CASE WHEN id=? THEN 1 ELSE 0 END "
                             "WHERE range_id=?", [to_int(matched_row["id"]), new_range_id])
                    tx.query("UPDATE sms_ranges SET test_number=? WHERE id=?",
                             [test_number, new_range_id])
            else:
                tx.query("UPDATE sms_numbers SET is_test=0 WHERE range_id=?", [new_range_id])

            counts = tx.query(
                "SELECT COUNT(*) total,SUM(CASE WHEN assigned_to IS NULL AND status='available' "
                "THEN 1 ELSE 0 END) available FROM sms_numbers WHERE range_id=?",
                [new_range_id]).fetch() or {}
            tx.query("UPDATE sms_ranges SET total_numbers=?,available_numbers=? WHERE id=?",
                     [to_int(counts.get("total")), to_int(counts.get("available")), new_range_id])
    except ApiError:
        raise
    except Exception as exc:
        logger.warning("Admin range save failed: %s", exc)
        return json_response(
            {"error": str(exc) if config.APP_DEBUG else "Could not save SMS range"}, 500)

    mode = "updated" if existing else "created"
    log_activity(admin_id, f"admin_range_{mode}",
                 f"{mode.capitalize()} global range #{new_range_id} {name} for all Managers; "
                 f"Agent request {'enabled' if request_enabled else 'disabled'}; "
                 f"imported {inserted} number(s), skipped {duplicates} duplicate(s)")

    message = f"Range {mode} successfully"
    if skipped:
        message += (" — NOTE: " + ", ".join(skipped) +
                    " could not be saved because the database is missing that column. "
                    "Use Database Upgrade in the Admin panel, then try again.")
    elif db_column_exists(db, "sms_ranges", "max_requests_per_agent"):
        verify = db.query("SELECT max_requests_per_agent,max_numbers_per_agent_daily "
                          "FROM sms_ranges WHERE id=? LIMIT 1", [new_range_id]).fetch()
        stored = verify.get("max_requests_per_agent") if verify else None
        shown = "Unlimited" if stored is None or to_int(stored) <= 0 else to_int(stored)
        message += f" (Max Requests / Agent saved as: {shown})"
        if verify and db_column_exists(db, "sms_ranges", "max_numbers_per_agent_daily"):
            daily = verify.get("max_numbers_per_agent_daily")
            daily_shown = "Unlimited" if daily is None or to_int(daily) <= 0 else to_int(daily)
            message += f" (Daily Number Limit / Agent saved as: {daily_shown})"

    return json_response({"success": True, "message": message, "id": new_range_id,
                          "inserted": inserted, "duplicates": duplicates,
                          "skipped_columns": skipped})


async def admin_delete_range(ctx: Ctx):
    body = await ctx.body()
    range_id = to_int(body.get("id"))
    if not range_id:
        return json_response({"error": "Range ID required"}, 400)
    rng = ctx.db.query("SELECT id,range_name FROM sms_ranges WHERE id=? LIMIT 1",
                       [range_id]).fetch()
    if not rng:
        return json_response({"error": "Range not found"}, 404)
    assigned = to_int(ctx.db.query(
        "SELECT COUNT(*) c FROM sms_numbers WHERE range_id=? AND assigned_to IS NOT NULL",
        [range_id]).scalar())
    if assigned > 0:
        return json_response(
            {"error": f"Cannot delete this range while {assigned} number(s) are assigned. "
                      f"Unassign them first."}, 409)
    ctx.db.query("DELETE FROM sms_ranges WHERE id=?", [range_id])
    log_activity(ctx.user_id, "admin_range_deleted",
                 f"Deleted global range #{range_id} {rng['range_name']}")
    return json_response({"success": True, "message": "Range deleted"})


# ═══════════════════════════════ NUMBERS ════════════════════════════════════
NUMBER_JOINS = (" FROM sms_numbers n JOIN sms_ranges r ON r.id=n.range_id "
                "LEFT JOIN users au ON au.id=n.assigned_to "
                "LEFT JOIN users ap ON ap.id=au.parent_id "
                "LEFT JOIN users mgr ON mgr.id=(CASE WHEN au.role='manager' THEN au.id "
                "WHEN au.role='agent' THEN au.parent_id "
                "WHEN au.role='client' THEN ap.parent_id ELSE NULL END) ")


def admin_numbers(ctx: Ctx):
    search = clean_string(ctx.q("search") or "", 100)
    manager_id = ctx.q_int("manager_id")
    status = clean_string(ctx.q("status") or "", 20)
    limit = limit_value(ctx.q("limit"), 100, 500)
    offset = offset_value(ctx.q("offset"))

    where, params = "1=1", []
    if search:
        where += (" AND (n.number LIKE ? OR r.range_name LIKE ? OR r.prefix LIKE ? "
                  "OR au.username LIKE ? OR mgr.username LIKE ?)")
        params += [f"%{search}%"] * 5
    if manager_id:
        where += " AND mgr.id=?"
        params.append(manager_id)
    if status in ("available", "assigned", "reserved"):
        where += " AND n.status=?"
        params.append(status)

    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c {NUMBER_JOINS} WHERE {where}", params).scalar())
    rows = ctx.db.query(
        f"SELECT n.id,n.number,n.status,n.pay_term,n.payout_rate,n.is_test,n.assigned_at,"
        f"r.range_name,r.prefix,r.currency,mgr.id manager_id,"
        f"COALESCE(mgr.username,'Global Pool') manager_name,"
        f"au.id assigned_user_id,au.username assigned_username,au.role assigned_role "
        f"{NUMBER_JOINS} WHERE {where} ORDER BY n.created_at DESC,n.id DESC "
        f"LIMIT {offset},{limit}", params).fetchall()

    return json_response({"success": True, "total": total, "data": rows})


async def admin_unassign_number(ctx: Ctx):
    body = await ctx.body()
    number_id = to_int(body.get("id"))
    if not number_id:
        return json_response({"error": "Invalid number"}, 400)
    row = ctx.db.query(
        "SELECT n.id,n.number,n.status,au.username assigned_username,au.role assigned_role "
        "FROM sms_numbers n LEFT JOIN users au ON au.id=n.assigned_to WHERE n.id=? LIMIT 1",
        [number_id]).fetch()
    if not row:
        return json_response({"error": "Number not found"}, 404)
    if row["status"] != "assigned" or not row.get("assigned_username"):
        return json_response({"error": "This number is not currently assigned to anyone"}, 409)

    ctx.db.query("UPDATE sms_numbers SET assigned_to=NULL,assigned_at=NULL,status='available' "
                 "WHERE id=?", [number_id])
    log_activity(ctx.user_id, "admin_number_unassigned",
                 f"Unassigned SMS number {row['number']} from "
                 f"{row['assigned_role']} {row['assigned_username']}")
    return json_response({"success": True, "message": "Number returned to the available pool"})


async def admin_return_range_numbers(ctx: Ctx):
    body = await ctx.body()
    range_id = to_int(body.get("range_id"))
    if not range_id:
        return json_response({"error": "Range is required"}, 400)
    rng = ctx.db.query("SELECT id,range_name FROM sms_ranges WHERE id=? LIMIT 1",
                       [range_id]).fetch()
    if not rng:
        return json_response({"error": "Range not found"}, 404)
    count = to_int(ctx.db.query(
        "SELECT COUNT(*) c FROM sms_numbers WHERE range_id=? AND status='assigned'",
        [range_id]).scalar())
    if count == 0:
        return json_response({"success": True,
                              "message": "No assigned numbers in this range. Nothing to return.",
                              "returned": 0})
    ctx.db.query("UPDATE sms_numbers SET assigned_to=NULL,assigned_at=NULL,status='available' "
                 "WHERE range_id=? AND status='assigned'", [range_id])
    log_activity(ctx.user_id, "admin_range_numbers_returned",
                 f"Returned {count} number(s) from range {rng['range_name']} "
                 f"to the available pool")
    return json_response({"success": True,
                          "message": f"{count} number(s) returned to the available pool",
                          "returned": count})


# ═══════════════════════════ REPORTS / PAYMENTS ═════════════════════════════
REPORT_JOINS = (" FROM sms_cdr c LEFT JOIN sms_ranges r ON r.id=c.range_id "
                "LEFT JOIN users u ON u.id=c.user_id "
                "LEFT JOIN users pu ON pu.id=u.parent_id "
                "LEFT JOIN users mgr ON mgr.id=(CASE WHEN u.role='manager' THEN u.id "
                "WHEN u.role='agent' THEN u.parent_id "
                "WHEN u.role='client' THEN pu.parent_id ELSE NULL END) ")


def admin_reports(ctx: Ctx):
    search = clean_string(ctx.q("search") or "", 100)
    date_from = clean_string(ctx.q("from") or "", 25)
    date_to = clean_string(ctx.q("to") or "", 25)
    manager_id = ctx.q_int("manager_id")
    agent_id = ctx.q_int("agent_id")
    otp_only = to_bool_int(ctx.q("otp_only") or 0)
    limit = limit_value(ctx.q("limit"), 100, 500)
    offset = offset_value(ctx.q("offset"))

    where, params = "1=1", []
    if date_from:
        where += " AND c.date_time>=?"
        params.append(date_from)
    if date_to:
        where += " AND c.date_time<=?"
        params.append(date_to)
    if manager_id:
        where += " AND mgr.id=?"
        params.append(manager_id)
    if agent_id:
        where += (" AND (CASE WHEN u.role='client' THEN u.parent_id "
                  "WHEN u.role='agent' THEN u.id ELSE NULL END)=?")
        params.append(agent_id)
    if otp_only:
        where += " AND c.otp_detected=1"
    if search:
        where += (" AND (c.number LIKE ? OR c.cli LIKE ? OR r.range_name LIKE ? "
                  "OR mgr.username LIKE ? OR u.username LIKE ? OR pu.username LIKE ?)")
        params += [f"%{search}%"] * 6

    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c {REPORT_JOINS} WHERE {where}", params).scalar())
    rows = ctx.db.query(
        f"SELECT c.id,c.date_time,c.number,c.cli,c.sms_count,c.sms_type,c.otp_detected,"
        f"c.currency,c.my_payout,c.user_payout,c.agent_payout,c.profit,c.smpp_status,"
        f"r.range_name,mgr.id manager_id,COALESCE(mgr.username,'-') manager_name, "
        f"CASE WHEN u.role='client' THEN pu.id WHEN u.role='agent' THEN u.id "
        f" ELSE NULL END agent_id, "
        f"CASE WHEN u.role='client' THEN pu.username WHEN u.role='agent' THEN u.username "
        f" ELSE '-' END agent_name, "
        f"CASE WHEN u.role='client' THEN u.username ELSE '-' END client_name "
        f"{REPORT_JOINS} WHERE {where} ORDER BY c.date_time DESC LIMIT {offset},{limit}",
        params).fetchall()
    summary = ctx.db.query(
        f"SELECT COALESCE(SUM(c.sms_count),0) sms,COALESCE(SUM(c.otp_detected),0) otp,"
        f"COALESCE(SUM(c.my_payout),0) payout_in,COALESCE(SUM(c.profit),0) profit "
        f"{REPORT_JOINS} WHERE {where}", params).fetch()

    return json_response({"success": True, "total": total, "summary": summary,
                          "data": rows, "message_content_exposed": False})


def admin_payments(ctx: Ctx):
    status = clean_string(ctx.q("status") or "", 20)
    limit = limit_value(ctx.q("limit"), 100, 500)
    offset = offset_value(ctx.q("offset"))

    where, params = "1=1", []
    if status in ("pending", "approved", "rejected", "completed"):
        where += " AND p.status=?"
        params.append(status)

    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c FROM payment_requests p WHERE {where}", params).scalar())
    rows = ctx.db.query(
        f"SELECT p.id,p.created_at,p.currency,p.amount,p.method,p.details,p.status,"
        f"p.processed_at,u.username,u.role,par.username parent_username "
        f"FROM payment_requests p JOIN users u ON u.id=p.user_id "
        f"LEFT JOIN users par ON par.id=u.parent_id "
        f"WHERE {where} ORDER BY p.created_at DESC LIMIT {offset},{limit}", params).fetchall()

    return json_response({"success": True, "total": total, "data": rows})


async def admin_payment_status(ctx: Ctx):
    body = await ctx.body()
    payment_id = to_int(body.get("id"))
    status = clean_string(body.get("status"), 20)
    if not payment_id or status not in ("pending", "approved", "rejected", "completed"):
        return json_response({"error": "Invalid payment request or status"}, 400)
    row = ctx.db.query("SELECT id,user_id,status FROM payment_requests WHERE id=? LIMIT 1",
                       [payment_id]).fetch()
    if not row:
        return json_response({"error": "Payment request not found"}, 404)

    processed_at = (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    if status in ("approved", "rejected", "completed") else None)
    ctx.db.query("UPDATE payment_requests SET status=?,processed_by=?,processed_at=? WHERE id=?",
                 [status, ctx.user_id, processed_at, payment_id])
    create_notification(to_int(row["user_id"]), "Payment Request Updated",
                        f"Your payment request status is now {status.capitalize()}",
                        "warning" if status == "rejected" else "info")
    log_activity(ctx.user_id, "admin_payment_status",
                 f"Payment request #{payment_id} set to {status}")
    return json_response({"success": True, "message": "Payment request updated"})


# ═══════════════════════════════ TEST SMS ═══════════════════════════════════
async def admin_test_sms_send(ctx: Ctx):
    """Admin-only: manually inject a fake inbound SMS for any number, exactly
    as if it had arrived from a real carrier. This goes through the same
    ingest_sms() pipeline used by the SMPP engine and the HTTP/Jasmin
    webhooks, so a test message shows up wherever a real one would (CDR,
    dashboard counts, balances, notifications) — not a separate mock table.
    Unlike the existing Test Panel, this is not limited to numbers flagged
    is_test=1; any number in the system can be used."""
    body = await ctx.body()
    destination = clean_string(body.get("number"), 40)
    message = str(body.get("message") or "").strip()
    source = clean_string(body.get("source"), 40) or "ADMIN-TEST"

    if not destination:
        return json_response({"error": "Number is required"}, 400)
    if not message:
        return json_response({"error": "Message is required"}, 400)
    if len(message) > 1600:
        return json_response({"error": "Message too long (max 1600 characters)"}, 400)

    message_id = f"admintest_{secrets.token_hex(8)}"
    result = ingest_sms(
        source_addr=source,
        destination_addr=destination,
        message=message,
        message_id=message_id,
        connector_id="admin_manual_test",
    )

    if not result.get("success"):
        return json_response({"error": result.get("error", "Failed to send test SMS")}, 500)

    log_activity(ctx.user_id, "admin_test_sms_send",
                 f"Sent fake SMS to {destination}"
                 + (f" (routed to user #{result['client_id']})" if result.get("assigned") else
                    " (number not assigned to any account)"))

    return json_response({
        "success": True,
        "message": ("Test SMS delivered and credited" if result.get("assigned") else
                     "Test SMS logged, but this number is not assigned to any account"),
        "assigned": result.get("assigned", False),
        "number": result.get("number", destination),
        "range": result.get("range"),
        "otp_detected": result.get("otp_detected", False),
        "cdr_id": result.get("cdr_id"),
        "payouts": result.get("payouts"),
    })


# ═══════════════════════════════ SMPP ═══════════════════════════════════════
def admin_smpp_control(ctx: Ctx):
    db = ctx.db
    engine = smpp_service.status()
    out = {
        "installed": db_table_exists(db, "smpp_config"),
        "jasmin_running": jasmin_running(),
        "smpp_engine_running": engine["server_running"],
        "bound_accounts": engine["bound_accounts"],
        "listen_port": engine["listen_port"],
        "active_config": None,
        "configs": [],
        "stats": {"hourly": 0, "daily": 0},
    }
    if not out["installed"]:
        return json_response(out)
    try:
        rows = db.query(
            "SELECT id,config_name,inbound_host,inbound_port,inbound_system_id,status,"
            "total_received,last_received_at,created_at,updated_at "
            "FROM smpp_config ORDER BY id DESC").fetchall()
        out["configs"] = rows
        out["active_config"] = next((r for r in rows if r["status"] == "active"), None)
        out["stats"]["hourly"] = to_int(db.query(
            "SELECT COUNT(*) c FROM smpp_cdr "
            "WHERE submit_date>=DATE_SUB(UTC_TIMESTAMP(),INTERVAL 1 HOUR)").scalar())
        out["stats"]["daily"] = to_int(db.query(
            "SELECT COUNT(*) c FROM smpp_cdr "
            "WHERE submit_date>=DATE_SUB(UTC_TIMESTAMP(),INTERVAL 24 HOUR)").scalar())
    except Exception:
        out["error"] = ("SMPP tables are not ready. "
                        "Run database/migrations/smpp_tables.sql first.")
    return json_response(out)


def admin_get_smpp_config(ctx: Ctx):
    db = ctx.db
    if not db_table_exists(db, "smpp_config"):
        return json_response({
            "success": True, "installed": False, "configs": [], "active_config": None,
            "stats": {"hourly": 0, "daily": 0}, "jasmin_running": False,
            "message": "SMPP tables are not installed. "
                       "Run database/migrations/admin_smpp_news_upgrade.sql.",
        })

    rows = db.query(
        "SELECT id,config_name,inbound_host,inbound_port,inbound_system_id,status,"
        "total_received,last_received_at,created_at,updated_at, "
        "CASE WHEN inbound_password IS NULL OR inbound_password='' THEN 0 ELSE 1 END "
        "password_configured FROM smpp_config "
        "ORDER BY CASE status WHEN 'active' THEN 0 WHEN 'maintenance' THEN 1 ELSE 2 END,"
        "id DESC").fetchall()
    active = next((r for r in rows if r["status"] == "active"), None)

    hourly = daily = 0
    if db_table_exists(db, "smpp_cdr"):
        hourly = to_int(db.query(
            "SELECT COUNT(*) c FROM smpp_cdr "
            "WHERE submit_date>=DATE_SUB(UTC_TIMESTAMP(),INTERVAL 1 HOUR)").scalar())
        daily = to_int(db.query(
            "SELECT COUNT(*) c FROM smpp_cdr "
            "WHERE submit_date>=DATE_SUB(UTC_TIMESTAMP(),INTERVAL 24 HOUR)").scalar())

    return json_response({
        "success": True, "installed": True, "configs": rows, "active_config": active,
        "stats": {"hourly": hourly, "daily": daily},
        "jasmin_running": jasmin_running(),
        "smpp_engine_running": smpp_service.status()["server_running"],
        "connection_info": {"api_port": str(config.JASMIN_API_PORT)},
    })


async def admin_save_smpp_config(ctx: Ctx):
    db, admin_id = ctx.db, ctx.user_id
    if not db_table_exists(db, "smpp_config"):
        return json_response(
            {"error": "SMPP tables are not installed. "
                      "Run database/migrations/admin_smpp_news_upgrade.sql first."}, 409)

    body = await ctx.body()
    config_id = max(0, to_int(body.get("id")))
    name = clean_string(body.get("config_name"), 50)
    host = clean_string(body.get("inbound_host"), 100)
    port = to_int(body.get("inbound_port"))
    system_id = clean_string(body.get("inbound_system_id"), 50)
    password = str(body.get("inbound_password") or "")
    status = clean_string(body.get("status") or "inactive", 20)

    if not name or not CONFIG_NAME_RE.match(name):
        return json_response(
            {"error": "Config name may contain letters, numbers, spaces, dot, dash "
                      "and underscore only"}, 400)
    if not host or re.search(r"[\x00-\x1F\x7F]", host):
        return json_response({"error": "Valid inbound host is required"}, 400)
    if port < 1 or port > 65535:
        return json_response({"error": "Inbound port must be between 1 and 65535"}, 400)
    if not system_id:
        return json_response({"error": "System ID is required"}, 400)
    if status not in ("active", "inactive", "maintenance"):
        return json_response({"error": "Invalid SMPP status"}, 400)
    if password and len(password) < 8:
        return json_response({"error": "SMPP password must be at least 8 characters"}, 400)

    existing = None
    if config_id:
        existing = db.query("SELECT id,config_name FROM smpp_config WHERE id=? LIMIT 1",
                            [config_id]).fetch()
        if not existing:
            return json_response({"error": "SMPP profile not found"}, 404)
    if not existing and not password:
        return json_response({"error": "Password is required for a new SMPP profile"}, 400)

    if db.query("SELECT id FROM smpp_config WHERE config_name=? AND id<>? LIMIT 1",
                [name, config_id]).fetch():
        return json_response({"error": "Another SMPP profile already uses this config name"}, 409)

    try:
        with db.transaction() as tx:
            if status == "active":
                tx.query("UPDATE smpp_config SET status='inactive' "
                         "WHERE status='active' AND id<>?", [config_id])
            if existing:
                if password:
                    tx.query(
                        "UPDATE smpp_config SET config_name=?,inbound_host=?,inbound_port=?,"
                        "inbound_system_id=?,inbound_password=?,status=? WHERE id=?",
                        [name, host, port, system_id, password_hash(password), status, config_id])
                else:
                    tx.query(
                        "UPDATE smpp_config SET config_name=?,inbound_host=?,inbound_port=?,"
                        "inbound_system_id=?,status=? WHERE id=?",
                        [name, host, port, system_id, status, config_id])
            else:
                result = tx.query(
                    "INSERT INTO smpp_config (config_name,inbound_host,inbound_port,"
                    "inbound_system_id,inbound_password,status,created_by) VALUES (?,?,?,?,?,?,?)",
                    [name, host, port, system_id, password_hash(password), status, admin_id])
                config_id = result.lastrowid
    except Exception as exc:
        logger.warning("Admin SMPP save failed: %s", exc)
        return json_response({"error": "Could not save SMPP configuration"}, 500)

    log_activity(admin_id, "admin_smpp_config", f"Saved SMPP profile: {name} ({status})")
    return json_response({"success": True, "message": "SMPP configuration saved", "id": config_id})


def admin_smpp_accounts(ctx: Ctx):
    if not db_table_exists(ctx.db, "smpp_users"):
        return json_response({"installed": False, "accounts": [],
                              "error": "Run database/migrations/smpp_tables.sql first."})
    rows = ctx.db.query(
        "SELECT id,username,supplier_name,supplier_contact,bind_type,max_connections,"
        "allowed_ranges,status,total_messages,last_connected_at,created_at "
        "FROM smpp_users ORDER BY id DESC").fetchall()
    return json_response({"installed": True, "accounts": rows})


async def admin_smpp_account_save(ctx: Ctx):
    db, admin_id = ctx.db, ctx.user_id
    if not db_table_exists(db, "smpp_users"):
        return json_response({"error": "SMPP migration is required."}, 503)

    body = await ctx.body()
    account_id = to_int(body.get("id"))
    username = clean_string(body.get("username"), 50)
    supplier = clean_string(body.get("supplier_name"), 100)
    contact = clean_string(body.get("supplier_contact"), 100)
    bind = body.get("bind_type") if body.get("bind_type") in ("TX", "RX", "TR") else "TR"
    max_conn = max(1, min(1000, to_int(body.get("max_connections"), 10)))
    status = body.get("status") if body.get("status") in ("active", "suspended", "disabled") else "active"
    ranges = clean_string(body.get("allowed_ranges"), 2000)
    password = str(body.get("password_hash") or body.get("password") or "")
    system_id = clean_string(body.get("system_id"), 50) or username
    link = body.get("interconnect_type")
    link = link if link in ("smpp-server", "smpp-client") else "smpp-server"
    host = clean_string(body.get("host"), 190)
    port = to_int(body.get("port"))

    if not username:
        return json_response({"error": "Username is required"}, 422)
    if link == "smpp-client" and (not host or port <= 0):
        return json_response(
            {"error": "Host and port are required when we dial out to the carrier "
                      "(interconnect_type = smpp-client)."}, 422)

    # The engine needs the bind password back in plaintext (an SMPP bind PDU
    # carries it in the clear), so it is kept base64-encoded in bind_password
    # alongside the one-way password_hash the rest of the panel uses.
    has_bind_cols = db_column_exists(db, "smpp_users", "bind_password")
    bind_secret = base64.b64encode(password.encode()).decode() if password else None

    try:
        if account_id > 0:
            fields = ["username=?", "supplier_name=?", "supplier_contact=?",
                      "bind_type=?", "max_connections=?", "allowed_ranges=?", "status=?"]
            params = [username, supplier, contact, bind, max_conn, ranges, status]
            if password:
                fields.append("password_hash=?")
                params.append(password_hash(password))
            if has_bind_cols:
                fields += ["system_id=?", "interconnect_type=?", "host=?", "port=?"]
                params += [system_id, link, host or None, port or None]
                if password:
                    fields.append("bind_password=?")
                    params.append(bind_secret)
            db.query(f"UPDATE smpp_users SET {','.join(fields)} WHERE id=?",
                     params + [account_id])
        else:
            if not password:
                return json_response({"error": "Password is required for a new SMPP account"}, 422)
            cols = ["username", "password_hash", "supplier_name", "supplier_contact",
                    "bind_type", "max_connections", "allowed_ranges", "status", "created_by"]
            vals = [username, password_hash(password), supplier, contact, bind, max_conn,
                    ranges, status, admin_id]
            if has_bind_cols:
                cols += ["system_id", "bind_password", "interconnect_type", "host", "port"]
                vals += [system_id, bind_secret, link, host or None, port or None]
            result = db.query(
                f"INSERT INTO smpp_users({','.join(cols)}) "
                f"VALUES ({','.join(['?'] * len(cols))})", vals)
            account_id = result.lastrowid
    except Exception as exc:
        logger.warning("SMPP account save: %s", exc)
        return json_response(
            {"error": "Could not save SMPP account. Username may already exist."}, 500)

    log_activity(admin_id, "smpp_account_save", f"SMPP account updated: {username}")

    # Inbound binds re-read the account list on every attempt, but outbound
    # ('smpp-client') connections are long-lived, so they are rebuilt here.
    # Without this an edited carrier stays on the old credentials until restart.
    try:
        await smpp_service.sync_outbound()
    except Exception as exc:
        logger.warning("SMPP resync after account save failed: %s", exc)

    warning = None
    if not has_bind_cols:
        warning = ("Saved, but this account cannot bind yet: run the one-click "
                   "Database Upgrade (or migrations/smpp_bind_credentials_upgrade.sql) "
                   "to add the SMPP bind columns.")
    return json_response({"success": True, "message": warning or "SMPP account saved",
                          "id": account_id, "bind_ready": has_bind_cols})


def admin_smpp_sessions(ctx: Ctx):
    if not db_table_exists(ctx.db, "smpp_users"):
        return json_response({"sessions": [], "telemetry": False})
    # last_connected_at is written by the live SMPP engine, so this is a real
    # session list rather than a permanently empty table.
    rows = ctx.db.query(
        "SELECT username,supplier_name,bind_type,total_messages messages,last_connected_at,status "
        "FROM smpp_users WHERE status='active' AND last_connected_at IS NOT NULL "
        "AND last_connected_at>=DATE_SUB(UTC_TIMESTAMP(),INTERVAL 15 MINUTE) "
        "ORDER BY last_connected_at DESC").fetchall()
    bound = set(smpp_service.status()["bound_accounts"])
    for row in rows:
        row["ip"] = "—"
        row["live"] = row.get("id") in bound if "id" in row else None
    return json_response({"telemetry": True, "sessions": rows,
                          "live_bound_accounts": list(bound)})


def admin_smpp_dlr(ctx: Ctx):
    if not db_table_exists(ctx.db, "smpp_cdr"):
        return json_response({"delivered": 0, "pending": 0, "failed": 0,
                              "dlr_rate": 0, "rows": []})
    delivered = to_int(ctx.db.query(
        "SELECT COUNT(*) c FROM smpp_cdr WHERE message_status='delivered'").scalar())
    pending = to_int(ctx.db.query(
        "SELECT COUNT(*) c FROM smpp_cdr WHERE message_status='pending'").scalar())
    failed = to_int(ctx.db.query(
        "SELECT COUNT(*) c FROM smpp_cdr WHERE message_status='failed'").scalar())
    total = delivered + pending + failed
    rate = round((delivered / total) * 100, 2) if total else 0
    rows = ctx.db.query(
        "SELECT message_id,source_addr,destination_addr,message_status,submit_date,connector_id "
        "FROM smpp_cdr ORDER BY id DESC LIMIT 100").fetchall()
    return json_response({"delivered": delivered, "pending": pending, "failed": failed,
                          "dlr_rate": rate, "rows": rows})


def admin_smpp_throughput(ctx: Ctx):
    if not db_table_exists(ctx.db, "smpp_cdr"):
        return json_response({"current_mps": 0, "peak_mps": 0, "total_24h": 0, "rows": []})
    total = to_int(ctx.db.query(
        "SELECT COUNT(*) c FROM smpp_cdr "
        "WHERE submit_date>=DATE_SUB(UTC_TIMESTAMP(),INTERVAL 24 HOUR)").scalar())
    current = to_int(ctx.db.query(
        "SELECT COUNT(*) c FROM smpp_cdr "
        "WHERE submit_date>=DATE_SUB(UTC_TIMESTAMP(),INTERVAL 60 SECOND)").scalar())
    rows = ctx.db.query(
        "SELECT DATE_FORMAT(submit_date,'%Y-%m-%d %H:%i:00') minute,COUNT(*) messages,"
        "ROUND(COUNT(*)/60,2) mps FROM smpp_cdr "
        "WHERE submit_date>=DATE_SUB(UTC_TIMESTAMP(),INTERVAL 60 MINUTE) "
        "GROUP BY minute ORDER BY minute DESC").fetchall()
    peak = max([to_float(r["mps"]) for r in rows], default=0)
    return json_response({"current_mps": round(current / 60, 2), "peak_mps": peak,
                          "total_24h": total, "rows": rows})


def admin_smpp_security(ctx: Ctx):
    events = []
    if db_table_exists(ctx.db, "smpp_cdr"):
        events = ctx.db.query(
            "SELECT submit_date time,'Inbound SMS' event,"
            "CONCAT('Message ',message_id,' from ',source_addr) details "
            "FROM smpp_cdr ORDER BY id DESC LIMIT 30").fetchall()
    return json_response({"events": events})


def admin_smpp_logs(ctx: Ctx):
    if not db_table_exists(ctx.db, "smpp_cdr"):
        return json_response({"rows": []})
    rows = ctx.db.query(
        "SELECT submit_date time,'Inbound SMS' event,connector_id account,'—' ip,"
        "message_status status FROM smpp_cdr ORDER BY id DESC LIMIT 100").fetchall()
    return json_response({"rows": rows})


# ═══════════════════════════ INTEGRATIONS ═══════════════════════════════════
INTEGRATION_FIELDS = {
    "http": ["provider_name", "status", "url", "method", "api_key", "sender_id",
             "timeout", "notes"],
    "api": ["status", "version", "base_url", "rate_limit", "scopes"],
    "webhook": ["url", "method", "secret", "timeout", "retries", "events"],
}
URL_RE = re.compile(r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE)


def integration_key(kind: str) -> str:
    return "integration_" + re.sub(r"[^a-z0-9_-]", "", kind.lower())


def admin_get_integration_settings(ctx: Ctx):
    kind = clean_string(ctx.q("type") or "", 20)
    if kind not in INTEGRATION_FIELDS:
        return json_response({"error": "Invalid integration type"}, 400)

    row = ctx.db.query("SELECT setting_value FROM system_settings WHERE setting_key=? LIMIT 1",
                       [integration_key(kind)]).fetch()
    cfg = {}
    if row and row.get("setting_value"):
        try:
            parsed = json.loads(str(row["setting_value"]))
            if isinstance(parsed, dict):
                cfg = parsed
        except Exception:
            cfg = {}
    # Never return secrets to the browser.
    for secret_key in ("api_key", "secret"):
        if secret_key in cfg:
            cfg[secret_key] = ""
    return json_response({"success": True, "type": kind, "config": cfg})


async def admin_save_integration_settings(ctx: Ctx):
    db, admin_id = ctx.db, ctx.user_id
    ensure_json_setting_type(db)   # <- the fix that makes this endpoint work at all

    body = await ctx.body()
    kind = clean_string(body.get("type"), 20)
    if kind not in INTEGRATION_FIELDS:
        return json_response({"error": "Invalid integration type"}, 400)

    cfg = body.get("config") if isinstance(body.get("config"), dict) else {}
    clean: dict = {}
    for field in INTEGRATION_FIELDS[kind]:
        if field not in cfg:
            continue
        value = str(cfg[field] or "").strip()
        if field in ("url", "base_url") and value and not URL_RE.match(value):
            return json_response({"error": f"{field} must be a valid URL"}, 400)
        if field == "method" and value.upper() not in ("GET", "POST", "PUT", "PATCH", "DELETE"):
            return json_response({"error": "Invalid HTTP method"}, 400)
        if field in ("timeout", "retries", "rate_limit") and value:
            try:
                float(value)
            except ValueError:
                return json_response({"error": f"{field} must be numeric"}, 400)
        clean[field] = clean_string(value, 2000)

    # Preserve secrets when the form intentionally leaves them blank.
    key = integration_key(kind)
    old_row = db.query("SELECT setting_value FROM system_settings WHERE setting_key=? LIMIT 1",
                       [key]).fetch()
    old_cfg = {}
    if old_row:
        try:
            parsed = json.loads(str(old_row["setting_value"] or "{}"))
            if isinstance(parsed, dict):
                old_cfg = parsed
        except Exception:
            old_cfg = {}
    for secret_key in ("api_key", "secret"):
        if not clean.get(secret_key) and old_cfg.get(secret_key):
            clean[secret_key] = old_cfg[secret_key]

    db.query(
        "INSERT INTO system_settings (setting_key,setting_value,setting_type,updated_by) "
        "VALUES (?,?,?,?) ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value),"
        "setting_type=VALUES(setting_type),updated_by=VALUES(updated_by)",
        [key, json.dumps(clean, separators=(",", ":")), "json", admin_id])

    log_activity(admin_id, "integration_settings_updated", f"Updated {kind} integration settings")
    return json_response({"success": True,
                          "message": f"{kind.upper()} integration settings saved"})


async def admin_generate_integration_token(ctx: Ctx):
    db, admin_id = ctx.db, ctx.user_id
    ensure_json_setting_type(db)

    token = "g1t_" + secrets.token_hex(24)
    row = db.query("SELECT setting_value FROM system_settings "
                   "WHERE setting_key='integration_api_tokens' LIMIT 1").fetch()
    items = []
    if row:
        try:
            parsed = json.loads(str(row["setting_value"] or "[]"))
            if isinstance(parsed, list):
                items = parsed
        except Exception:
            items = []
    items.append({"name": "Admin API Token", "hash": password_hash(token),
                  "created_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), "active": 1})

    db.query(
        "INSERT INTO system_settings (setting_key,setting_value,setting_type,updated_by) "
        "VALUES (?,?,?,?) ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value),"
        "setting_type=VALUES(setting_type),updated_by=VALUES(updated_by)",
        ["integration_api_tokens", json.dumps(items, separators=(",", ":")), "json", admin_id])

    log_activity(admin_id, "api_token_created", "Generated an Admin API token")
    return json_response({"success": True, "token": token})


# ═══════════════════════════ NEWS / SETTINGS ════════════════════════════════
def admin_agent_news(ctx: Ctx):
    search = clean_string(ctx.q("search") or "", 100)
    status = clean_string(ctx.q("status") or "", 20)
    limit = limit_value(ctx.q("limit"), 100, 500)
    offset = offset_value(ctx.q("offset"))

    where, params = "n.target_role='agent'", []
    if status in ("draft", "published", "archived"):
        where += " AND n.status=?"
        params.append(status)
    if search:
        where += " AND (n.title LIKE ? OR n.content LIKE ? OR u.username LIKE ?)"
        params += [f"%{search}%"] * 3

    total = to_int(ctx.db.query(
        f"SELECT COUNT(*) c FROM news n LEFT JOIN users u ON u.id=n.author_id WHERE {where}",
        params).scalar())
    rows = ctx.db.query(
        f"SELECT n.id,n.title,n.content,n.target_role,n.status,n.published_at,n.created_at,"
        f"n.updated_at,u.username author_name,u.role author_role "
        f"FROM news n LEFT JOIN users u ON u.id=n.author_id "
        f"WHERE {where} ORDER BY n.created_at DESC LIMIT {offset},{limit}", params).fetchall()

    return json_response({"success": True, "total": total, "data": rows})


async def admin_save_agent_news(ctx: Ctx):
    db, admin_id = ctx.db, ctx.user_id
    body = await ctx.body()
    news_id = max(0, to_int(body.get("id")))
    title = clean_string(body.get("title"), 255)
    content = clean_string(body.get("content"), 10000)
    status = clean_string(body.get("status") or "published", 20)

    if not title or not content:
        return json_response({"error": "Headline and news content are required"}, 400)
    if status not in ("draft", "published", "archived"):
        return json_response({"error": "Invalid news status"}, 400)

    notify = False
    if news_id:
        old = db.query("SELECT id,title,status FROM news WHERE id=? AND target_role='agent' "
                       "LIMIT 1", [news_id]).fetch()
        if not old:
            return json_response({"error": "Agent news not found"}, 404)
        notify = status == "published" and old["status"] != "published"
        if notify:
            db.query("UPDATE news SET title=?,content=?,status=?,target_role='agent',"
                     "published_at=UTC_TIMESTAMP() WHERE id=?", [title, content, status, news_id])
        else:
            db.query("UPDATE news SET title=?,content=?,status=?,target_role='agent' WHERE id=?",
                     [title, content, status, news_id])
        log_activity(admin_id, "admin_agent_news_updated",
                     f"Updated Agent news #{news_id}: {title}")
        message = "Agent news updated"
    else:
        published_at = (datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                        if status == "published" else None)
        result = db.query(
            "INSERT INTO news (author_id,title,content,target_role,status,published_at) "
            "VALUES (?,?,?,'agent',?,?)", [admin_id, title, content, status, published_at])
        news_id = result.lastrowid
        notify = status == "published"
        log_activity(admin_id, "admin_agent_news_created",
                     f"Created Agent news #{news_id}: {title}")
        message = "Agent news created"

    if notify:
        for row in db.query("SELECT id FROM users WHERE role='agent' AND status='active'").fetchall():
            create_notification(to_int(row["id"]), "New Announcement", title, "info")

    return json_response({"success": True, "message": message, "id": news_id})


async def admin_delete_agent_news(ctx: Ctx):
    body = await ctx.body()
    news_id = to_int(body.get("id"))
    if not news_id:
        return json_response({"error": "News ID required"}, 400)
    row = ctx.db.query("SELECT id,title FROM news WHERE id=? AND target_role='agent' LIMIT 1",
                       [news_id]).fetch()
    if not row:
        return json_response({"error": "Agent news not found"}, 404)
    ctx.db.query("DELETE FROM news WHERE id=?", [news_id])
    log_activity(ctx.user_id, "admin_agent_news_deleted",
                 f"Deleted Agent news #{news_id}: {row['title']}")
    return json_response({"success": True, "message": "Agent news deleted"})


ALLOWED_SETTINGS = {
    "site_name": "string", "minimum_withdrawal_usd": "number",
    "minimum_withdrawal_eur": "number", "minimum_withdrawal_gbp": "number",
    "payment_requests_enabled": "boolean", "maintenance_mode": "boolean",
    "default_page_size": "number", "support_note": "string",
}


def admin_get_settings(ctx: Ctx):
    rows = ctx.db.query("SELECT setting_key,setting_value,setting_type,updated_at "
                        "FROM system_settings ORDER BY setting_key").fetchall()
    settings = {r["setting_key"]: {"value": r["setting_value"], "type": r["setting_type"],
                                   "updated_at": r["updated_at"]} for r in rows}
    return json_response({"success": True, "settings": settings})


async def admin_save_settings(ctx: Ctx):
    body = await ctx.body()
    for key, kind in ALLOWED_SETTINGS.items():
        if key not in body:
            continue
        value = body[key]
        if kind == "boolean":
            value = str(to_bool_int(value))
        elif kind == "number":
            try:
                value = str(max(0.0, float(value)))
            except (TypeError, ValueError):
                return json_response({"error": f"{key} must be numeric"}, 400)
        else:
            value = clean_string(value, 1000 if key == "support_note" else 255)
        ctx.db.query(
            "INSERT INTO system_settings (setting_key,setting_value,setting_type,updated_by) "
            "VALUES (?,?,?,?) ON DUPLICATE KEY UPDATE setting_value=VALUES(setting_value),"
            "setting_type=VALUES(setting_type),updated_by=VALUES(updated_by)",
            [key, value, kind, ctx.user_id])

    log_activity(ctx.user_id, "admin_settings_updated", "Updated global system settings")
    return json_response({"success": True, "message": "Settings saved"})


def admin_activity(ctx: Ctx):
    limit = limit_value(ctx.q("limit"), 100, 300)
    rows = ctx.db.query(
        f"SELECT a.id,a.created_at,a.action,a.description,a.ip_address,u.username,u.role "
        f"FROM user_activity a LEFT JOIN users u ON u.id=a.user_id "
        f"ORDER BY a.created_at DESC LIMIT {limit}").fetchall()
    return json_response({"success": True, "data": rows})


# ═══════════════════════════ DB UPGRADE ═════════════════════════════════════
SMPP_USER_COLUMNS = {
    "system_id":
        "ALTER TABLE smpp_users ADD COLUMN system_id VARCHAR(50) NULL AFTER username",
    "bind_password":
        "ALTER TABLE smpp_users ADD COLUMN bind_password VARCHAR(255) NULL "
        "AFTER password_hash",
    "interconnect_type":
        "ALTER TABLE smpp_users ADD COLUMN interconnect_type VARCHAR(20) NOT NULL "
        "DEFAULT 'smpp-server' AFTER bind_type",
    "host":
        "ALTER TABLE smpp_users ADD COLUMN host VARCHAR(190) NULL "
        "AFTER interconnect_type",
    "port":
        "ALTER TABLE smpp_users ADD COLUMN port INT UNSIGNED NULL AFTER host",
}

RANGE_COLUMNS = {
    "request_enabled":
        "ALTER TABLE sms_ranges ADD COLUMN request_enabled TINYINT(1) NOT NULL DEFAULT 1 "
        "AFTER status",
    "max_requests_per_agent":
        "ALTER TABLE sms_ranges ADD COLUMN max_requests_per_agent INT UNSIGNED DEFAULT NULL "
        "AFTER request_enabled",
    "max_numbers_per_agent_daily":
        "ALTER TABLE sms_ranges ADD COLUMN max_numbers_per_agent_daily INT UNSIGNED DEFAULT NULL "
        "AFTER max_requests_per_agent",
    "payout_1_1_enabled":
        "ALTER TABLE sms_ranges ADD COLUMN payout_1_1_enabled TINYINT(1) NOT NULL DEFAULT 1 "
        "AFTER payout_30_45",
    "payout_7_1_enabled":
        "ALTER TABLE sms_ranges ADD COLUMN payout_7_1_enabled TINYINT(1) NOT NULL DEFAULT 1 "
        "AFTER payout_1_1_enabled",
    "payout_7_7_enabled":
        "ALTER TABLE sms_ranges ADD COLUMN payout_7_7_enabled TINYINT(1) NOT NULL DEFAULT 1 "
        "AFTER payout_7_1_enabled",
    "payout_30_45_enabled":
        "ALTER TABLE sms_ranges ADD COLUMN payout_30_45_enabled TINYINT(1) NOT NULL DEFAULT 1 "
        "AFTER payout_7_7_enabled",
}

RANGE_REQUEST_TABLE = """CREATE TABLE sms_range_agent_requests (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  range_id INT UNSIGNED NOT NULL,
  agent_id INT UNSIGNED NOT NULL,
  request_count INT UNSIGNED NOT NULL DEFAULT 0,
  last_requested_at DATETIME DEFAULT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_range_agent (range_id, agent_id),
  KEY idx_agent (agent_id),
  CONSTRAINT fk_rar_range FOREIGN KEY (range_id) REFERENCES sms_ranges(id) ON DELETE CASCADE,
  CONSTRAINT fk_rar_agent FOREIGN KEY (agent_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"""

RANGE_DAILY_REQUEST_TABLE = """CREATE TABLE sms_range_agent_daily_requests (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  range_id INT UNSIGNED NOT NULL,
  agent_id INT UNSIGNED NOT NULL,
  request_date DATE NOT NULL,
  qty_requested INT UNSIGNED NOT NULL DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_range_agent_date (range_id, agent_id, request_date),
  KEY idx_agent (agent_id),
  CONSTRAINT fk_radr_range FOREIGN KEY (range_id) REFERENCES sms_ranges(id) ON DELETE CASCADE,
  CONSTRAINT fk_radr_agent FOREIGN KEY (agent_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"""


async def admin_db_upgrade(ctx: Ctx):
    """One-click, idempotent schema upgrade, runnable from inside the Admin
    panel (no server/CLI access required). Safe to click any number of times."""
    db, admin_id = ctx.db, ctx.user_id
    applied, already = [], []

    try:
        if not db_table_exists(db, "sms_ranges"):
            return json_response(
                {"error": "sms_ranges table does not exist. Import database/schema.sql first."},
                409)

        for column, sql in RANGE_COLUMNS.items():
            if db_column_exists(db, "sms_ranges", column):
                already.append(f"sms_ranges.{column}")
                continue
            db.query(sql)
            applied.append(f"sms_ranges.{column}")

        if not db_table_exists(db, "sms_range_agent_requests"):
            db.query(RANGE_REQUEST_TABLE)
            applied.append("sms_range_agent_requests (table)")
        else:
            already.append("sms_range_agent_requests (table)")

        if not db_table_exists(db, "sms_range_agent_daily_requests"):
            db.query(RANGE_DAILY_REQUEST_TABLE)
            applied.append("sms_range_agent_daily_requests (table)")
        else:
            already.append("sms_range_agent_daily_requests (table)")

        if not db_column_exists(db, "sms_cdr", "message"):
            db.query("ALTER TABLE sms_cdr ADD COLUMN message TEXT DEFAULT NULL "
                     "COMMENT 'Full SMS text, shown in CDR reports' AFTER sms_type")
            applied.append("sms_cdr.message")
        else:
            already.append("sms_cdr.message")

        # Also repair the setting_type ENUM here, so the Integration pages start
        # working straight after a one-click upgrade.
        row = db.query(
            "SELECT COLUMN_TYPE ct FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='system_settings' "
            "AND COLUMN_NAME='setting_type' LIMIT 1").fetch()
        if row and "json" not in str(row["ct"]).lower():
            db.query("ALTER TABLE system_settings MODIFY COLUMN setting_type "
                     "ENUM('string','number','boolean','json') NOT NULL DEFAULT 'string'")
            applied.append("system_settings.setting_type (json)")
        elif row:
            already.append("system_settings.setting_type (json)")

        # SMPP bind credentials. `password_hash` is one-way, but an SMPP bind
        # PDU carries the password in plaintext, so without a reversible copy
        # no carrier can ever bind and every inbound OTP is lost.
        if db_table_exists(db, "smpp_users"):
            for column, sql in SMPP_USER_COLUMNS.items():
                if db_column_exists(db, "smpp_users", column):
                    already.append(f"smpp_users.{column}")
                    continue
                db.query(sql)
                applied.append(f"smpp_users.{column}")
            db.query("UPDATE smpp_users SET system_id = username "
                     "WHERE system_id IS NULL OR system_id = ''")
    except Exception as exc:
        logger.warning("Admin DB upgrade failed: %s", exc)
        return json_response(
            {"error": str(exc) if config.APP_DEBUG
             else "Database upgrade failed. Check the server log."}, 500)

    from core.helpers import clear_schema_cache
    clear_schema_cache()

    log_activity(admin_id, "admin_db_upgrade",
                 f"Applied: {', '.join(applied) if applied else 'nothing new'}; "
                 f"already present: {', '.join(already) if already else 'none'}")
    message = (f"Database upgraded. Added: {', '.join(applied)}" if applied
               else "Nothing to upgrade — all columns/tables already exist.")
    return json_response({"success": True, "message": message,
                          "applied": applied, "already_present": already})


# ═══════════════════════════════ ROUTER ═════════════════════════════════════
GET_ACTIONS = {
    "summary": admin_summary,
    "users": admin_users,
    "ranges": admin_ranges,
    "numbers": admin_numbers,
    "reports": admin_reports,
    "payments": admin_payments,
    "smpp-control": admin_smpp_control,
    "smpp-config": admin_get_smpp_config,
    "smpp-accounts": admin_smpp_accounts,
    "smpp-sessions": admin_smpp_sessions,
    "smpp-dlr": admin_smpp_dlr,
    "smpp-throughput": admin_smpp_throughput,
    "smpp-security": admin_smpp_security,
    "smpp-logs": admin_smpp_logs,
    "integration-settings": admin_get_integration_settings,
    "agent-news": admin_agent_news,
    "settings": admin_get_settings,
    "activity": admin_activity,
}

POST_ACTIONS = {
    "user-create": admin_create_user,
    "user-status": admin_user_status,
    "user-delete": admin_delete_user,
    "range-save": admin_save_range,
    "range-delete": admin_delete_range,
    "number-unassign": admin_unassign_number,
    "range-return-numbers": admin_return_range_numbers,
    "payment-status": admin_payment_status,
    "test-sms-send": admin_test_sms_send,
    "smpp-config": admin_save_smpp_config,
    "smpp-account-save": admin_smpp_account_save,
    "integration-settings": admin_save_integration_settings,
    "integration-token": admin_generate_integration_token,
    "agent-news-save": admin_save_agent_news,
    "agent-news-delete": admin_delete_agent_news,
    "settings": admin_save_settings,
    "db-upgrade": admin_db_upgrade,
}


@router.api_route("/api/admin.php", methods=["GET", "POST"])
@router.api_route("/api/admin", methods=["GET", "POST"])
async def admin_endpoint(request: Request, ctx: Ctx = Depends(get_ctx)):
    if not ctx.session.logged_in or ctx.role != "admin":
        return json_response({"error": "Admin access required"}, 403)
    ctx.session.touch()

    action = re.sub(r"[^a-z0-9_-]", "", ctx.q("action") or "summary", flags=re.IGNORECASE)

    if ctx.method == "POST" and action in POST_ACTIONS:
        return await POST_ACTIONS[action](ctx)
    if ctx.method == "GET" and action in GET_ACTIONS:
        return GET_ACTIONS[action](ctx)
    # Some actions exist on both verbs (integration-settings, smpp-config, settings)
    if action in GET_ACTIONS and ctx.method == "GET":
        return GET_ACTIONS[action](ctx)

    return json_response({"error": "Invalid admin action"}, 404)
