"""
GLOBAL1TEL - Helper functions (Python port of the helper block in api/config.php).

Names mirror the PHP originals so the ported endpoints stay recognisable:
    generateHash   -> generate_hash
    logActivity    -> log_activity
    managerOwnerSql-> manager_owner_sql
    ...
"""
from __future__ import annotations

import hashlib
import html
import json
import logging
import secrets
from decimal import Decimal
from datetime import date, datetime, timezone

from fastapi.responses import JSONResponse

from core import config
from core.db import Database

logger = logging.getLogger("g1t.helpers")

CANONICAL_TERMS = ["1/1", "7/1", "7/7", "30/45"]


# ── JSON output ─────────────────────────────────────────────────────────────
def _json_default(value):
    if isinstance(value, Decimal):
        # PHP/PDO returned decimals as strings; keeping that shape means the
        # existing frontend number formatting behaves identically.
        return format(value, "f")
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d %H:%M:%S" if isinstance(value, datetime) else "%Y-%m-%d")
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8", errors="replace")
    return str(value)


def json_response(data, status_code: int = 200) -> JSONResponse:
    """Equivalent of the PHP jsonResponse(): JSON body + status, ends the request."""
    return JSONResponse(
        content=json.loads(json.dumps(data, default=_json_default, ensure_ascii=False)),
        status_code=status_code,
    )


class ApiError(Exception):
    """Raised anywhere in a handler to return a JSON error, like jsonResponse(...,code)."""

    def __init__(self, message, status_code: int = 400, **extra):
        super().__init__(message if isinstance(message, str) else "Error")
        self.payload = {"error": message} if isinstance(message, str) else dict(message)
        self.payload.update(extra)
        self.status_code = status_code


def fail(message, status_code: int = 400, **extra):
    raise ApiError(message, status_code, **extra)


# ── Security / hashing ──────────────────────────────────────────────────────
def generate_hash(password: str) -> str:
    """hash(HASH_ALGO, SALT . $password) — byte-for-byte the PHP scheme, so
    every existing password in the database still validates after the port."""
    algo = (config.HASH_ALGO or "sha256").lower().replace("-", "_")
    data = (str(config.SALT) + str(password)).encode("utf-8")
    try:
        return hashlib.new(algo, data).hexdigest()
    except ValueError:
        return hashlib.sha256(data).hexdigest()


def generate_token(length: int = 64) -> str:
    return secrets.token_hex(length // 2)


def sanitize(value):
    """htmlspecialchars(trim($v), ENT_QUOTES, 'UTF-8') on strings; maps over lists/dicts."""
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    if value is None:
        return ""
    if not isinstance(value, str):
        return value
    return html.escape(value.strip(), quote=True).replace("'", "&#039;")


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True).replace("'", "&#039;")


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def now_string() -> str:
    return utc_now().strftime("%Y-%m-%d %H:%M:%S")


# ── Casting helpers (PHP's loose (int)/(float) casts) ───────────────────────
def to_int(value, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def to_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_string(value, max_len: int = 255) -> str:
    return str("" if value is None else value).strip()[:max_len]


def to_bool_int(value) -> int:
    return 1 if str(value).lower() in ("1", "true", "yes", "on") else 0


def limit_value(value, default: int = 100, maximum: int = 500) -> int:
    n = to_int(value, 0)
    if n < 1:
        return default
    return min(n, maximum)


def offset_value(value) -> int:
    return max(0, to_int(value, 0))


# ── Activity / notifications / balances ─────────────────────────────────────
def log_activity(user_id, action: str, description=None, ip=None, user_agent=None) -> None:
    try:
        Database.get_instance().query(
            "INSERT INTO user_activity (user_id, action, description, ip_address, user_agent) "
            "VALUES (?, ?, ?, ?, ?)",
            [user_id, action, description, ip, user_agent],
        )
    except Exception as exc:  # activity logging must never break a request
        logger.warning("log_activity failed: %s", exc)


def create_notification(user_id, title: str, message: str, ntype: str = "info") -> None:
    try:
        Database.get_instance().query(
            "INSERT INTO notifications (user_id, title, message, type) VALUES (?, ?, ?, ?)",
            [user_id, title, message, ntype],
        )
    except Exception as exc:
        logger.warning("create_notification failed: %s", exc)


def update_balance(user_id, currency: str, amount, kind: str = "credit") -> None:
    db = Database.get_instance()
    if kind == "credit":
        db.query(
            "INSERT INTO user_balances (user_id, currency, balance) VALUES (?, ?, ?) "
            "ON DUPLICATE KEY UPDATE balance = balance + ?",
            [user_id, currency, amount, amount],
        )
    else:
        db.query(
            "UPDATE user_balances SET balance = balance - ? "
            "WHERE user_id = ? AND currency = ? AND balance >= ?",
            [amount, user_id, currency, amount],
        )


def get_balance(user_id, currency: str = "USD") -> float:
    row = Database.get_instance().query(
        "SELECT balance FROM user_balances WHERE user_id = ? AND currency = ?",
        [user_id, currency],
    ).fetch()
    return to_float(row["balance"]) if row else 0.0


def format_currency(amount, currency: str = "USD") -> str:
    symbols = {"USD": "$", "EUR": "\u20ac", "GBP": "\u00a3"}
    return f"{symbols.get(currency, '$')}{to_float(amount):,.4f}"


# ── Hierarchy resolution (ports resolveManagerIdForUser / managerOwnerSql) ──
def resolve_manager_id_for_user(user_id):
    """Ranges are Admin-owned/global, so Manager attribution follows the
    account hierarchy rather than sms_ranges.manager_id."""
    user_id = to_int(user_id)
    if user_id <= 0:
        return None
    row = Database.get_instance().query(
        "SELECT u.id,u.role,u.parent_id,p.role parent_role,p.parent_id parent_parent_id "
        "FROM users u LEFT JOIN users p ON p.id=u.parent_id WHERE u.id=? LIMIT 1",
        [user_id],
    ).fetch()
    if not row:
        return None
    if row["role"] == "manager":
        return to_int(row["id"])
    if row["role"] == "agent" and row.get("parent_id"):
        return to_int(row["parent_id"])
    if row["role"] == "client" and (row.get("parent_role") or "") == "agent" and row.get("parent_parent_id"):
        return to_int(row["parent_parent_id"])
    return None


def manager_owner_sql(user_id_expr: str) -> str:
    """SQL expression returning the Manager id that owns a user in the hierarchy.
    `user_id_expr` must be a trusted SQL expression such as c.user_id."""
    return f"""(SELECT CASE
                WHEN scope_u.role='manager' THEN scope_u.id
                WHEN scope_u.role='agent' THEN scope_u.parent_id
                WHEN scope_u.role='client' THEN scope_parent.parent_id
                ELSE NULL END
             FROM users scope_u
             LEFT JOIN users scope_parent ON scope_parent.id=scope_u.parent_id
             WHERE scope_u.id={user_id_expr} LIMIT 1)"""


# ── Schema introspection (dbColumnExists / dbTableExists) ───────────────────
_column_cache: dict = {}
_table_cache: dict = {}


def db_column_exists(db: Database, table: str, column: str) -> bool:
    key = f"{table}.{column}"
    if key in _column_cache:
        return _column_cache[key]
    try:
        row = db.query(
            "SELECT COUNT(*) c FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=? AND COLUMN_NAME=?",
            [table, column],
        ).fetch()
        _column_cache[key] = to_int(row.get("c") if row else 0) > 0
    except Exception as exc:
        logger.warning("Column check failed for %s: %s", key, exc)
        _column_cache[key] = False
    return _column_cache[key]


def db_table_exists(db: Database, table: str) -> bool:
    if table in _table_cache:
        return _table_cache[table]
    try:
        row = db.query(
            "SELECT COUNT(*) c FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME=?",
            [table],
        ).fetch()
        _table_cache[table] = to_int(row.get("c") if row else 0) > 0
    except Exception as exc:
        logger.warning("Table check failed for %s: %s", table, exc)
        _table_cache[table] = False
    return _table_cache[table]


def clear_schema_cache() -> None:
    _column_cache.clear()
    _table_cache.clear()


# ── Payout terms ────────────────────────────────────────────────────────────
def pay_term_columns(term: str):
    return {
        "1/1": {"rate": "payout_1_1", "enabled": "payout_1_1_enabled"},
        "7/1": {"rate": "payout_7_1", "enabled": "payout_7_1_enabled"},
        "7/7": {"rate": "payout_7_7", "enabled": "payout_7_7_enabled"},
        "30/45": {"rate": "payout_30_45", "enabled": "payout_30_45_enabled"},
    }.get(term)


def pay_term_enabled(range_row, term: str) -> bool:
    cols = pay_term_columns(term)
    if not cols or not isinstance(range_row, dict):
        return False
    col = cols["enabled"]
    # Toggle column not present yet (migration not applied) -> behave as before.
    if col not in range_row:
        return True
    return range_row[col] is None or to_int(range_row[col]) == 1


def active_pay_terms(range_row) -> dict:
    """Terms that are both priced (non-null rate) and switched on, in canonical order."""
    out = {}
    if not isinstance(range_row, dict):
        return out
    for term in CANONICAL_TERMS:
        rate_col = pay_term_columns(term)["rate"]
        if rate_col not in range_row:
            continue
        if range_row[rate_col] is None or range_row[rate_col] == "":
            continue
        if not pay_term_enabled(range_row, term):
            continue
        out[term] = range_row[rate_col]
    return out


def calculate_payout(range_id, pay_term: str) -> float:
    row = Database.get_instance().query("SELECT * FROM sms_ranges WHERE id = ?", [range_id]).fetch()
    if not row:
        return 0.0
    field = "payout_" + str(pay_term).replace("/", "_")
    if field in row and row[field] is not None:
        return to_float(row[field])
    return to_float(row.get("payout_1_1"))


def range_request_limit(range_row):
    """Admin's cap on how many separate requests one Agent may submit for a range."""
    if not isinstance(range_row, dict) or "max_requests_per_agent" not in range_row:
        return None
    value = range_row["max_requests_per_agent"]
    if value is None or value == "" or to_int(value) <= 0:
        return None
    return to_int(value)


def agent_range_request_count(db: Database, agent_id: int, range_id: int) -> int:
    if not db_table_exists(db, "sms_range_agent_requests"):
        return 0
    row = db.query(
        "SELECT request_count FROM sms_range_agent_requests WHERE range_id=? AND agent_id=? LIMIT 1",
        [range_id, agent_id],
    ).fetch()
    return to_int(row.get("request_count") if row else 0)


# ── Number helpers ──────────────────────────────────────────────────────────
def is_test_number(number: str, range_id=None) -> bool:
    db = Database.get_instance()
    if range_id:
        row = db.query(
            "SELECT is_test FROM sms_numbers WHERE number = ? AND range_id = ?", [number, range_id]
        ).fetch()
    else:
        row = db.query("SELECT is_test FROM sms_numbers WHERE number = ?", [number]).fetch()
    return bool(row and to_int(row["is_test"]) == 1)


def get_number_type(number: str) -> str:
    return "test" if is_test_number(number) else "general"


def validate_api_token(token: str):
    if not token:
        return None
    return Database.get_instance().query(
        "SELECT * FROM users WHERE api_token = ? AND status = 'active'", [token]
    ).fetch()
