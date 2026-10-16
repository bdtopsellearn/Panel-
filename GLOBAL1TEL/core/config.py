"""
GLOBAL1TEL - Main Configuration  (Python port of public/api/config.php)

Loads config/.env exactly like the PHP version did (same keys, same
fallbacks) so an existing installation keeps working with no edits.
"""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── Load environment variables from config/.env ──────────────────────────────
_ENV_PATHS = [
    ROOT / "config" / ".env",
    ROOT / ".env",
]


def _load_env() -> None:
    for env_file in _ENV_PATHS:
        if env_file.is_file():
            for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # Real environment always wins over the file, same as putenv() order
                if key and key not in os.environ:
                    os.environ[key] = value
            break


_load_env()


def env(key: str, default=None):
    value = os.environ.get(key)
    if value is None or value == "":
        return default
    return value


# ── Database ────────────────────────────────────────────────────────────────
DB_HOST = env("DB_HOST", "localhost")
DB_PORT = int(env("DB_PORT", "3306"))
DB_NAME = env("DB_NAME", "global1tel")
DB_USER = env("DB_USER", "global1tel_user")
DB_PASS = env("DB_PASS", "your_secure_password_here")

# ── Application ─────────────────────────────────────────────────────────────
APP_NAME = env("APP_NAME", "GLOBAL1TEL")
APP_URL = env("APP_URL", "http://localhost")
APP_ENV = env("APP_ENV", "production")
APP_DEBUG = str(env("APP_DEBUG", "false")).lower() == "true"

# ── Security ────────────────────────────────────────────────────────────────
HASH_ALGO = env("HASH_ALGO", "sha256")
SALT = env("SALT", "mbc_sms_secure_salt_2024")
SESSION_NAME = env("SESSION_NAME", "global1tel_session")
SESSION_LIFETIME = int(env("SESSION_LIFETIME", "7200"))

# Signing key for the session cookie. Set G1T_SECRET on the VPS so sessions
# survive a restart; otherwise it is derived from SALT (stable, but shared
# with anyone who can read .env — same trust level the PHP build had).
SESSION_SECRET = env("G1T_SECRET", "g1t-session::" + str(SALT))

# ── Jasmin SMS Gateway ──────────────────────────────────────────────────────
JASMIN_API_URL = env("JASMIN_API_URL", "http://localhost")
JASMIN_API_PORT = env("JASMIN_API_PORT", "1401")
JASMIN_PANEL_PORT = env("JASMIN_PANEL_PORT", "8080")

# ── SMPP ────────────────────────────────────────────────────────────────────
SMPP_WEBHOOK_KEY = env("SMPP_WEBHOOK_KEY", "")
SMPP_SERVER_ENABLED = str(env("SMPP_SERVER_ENABLED", "true")).lower() in ("1", "true", "yes", "on")
SMPP_SERVER_HOST = env("SMPP_SERVER_HOST", "0.0.0.0")
SMPP_SERVER_PORT = int(env("SMPP_SERVER_PORT", "2775"))

# ── Rate limiting (DDoS protection), same numbers as config.php ─────────────
RATE_LIMIT = {
    "enabled": True,
    "max_requests": 100,          # per minute, per IP
    "ban_duration": 600,          # 10 minutes
    "whitelist": {"127.0.0.1", "::1"},
    # Static assets are excluded: one page load pulls dozens of css/js/img
    # files and would otherwise ban a real user on their first visit.
    "static_max_requests": 900,
}

LOGIN_RATE_LIMIT = {
    "enabled": True,
    "max_attempts": 5,
    "window": 900,                # 15 minutes
    "ban_duration": 1800,         # 30 minutes
}

# ── CORS ────────────────────────────────────────────────────────────────────
# The PHP build sent `Access-Control-Allow-Origin: *`. Set G1T_ORIGINS to a
# comma-separated list to restrict it.
CORS_ORIGINS = [o.strip() for o in str(env("G1T_ORIGINS", "*")).split(",") if o.strip()]

TIMEZONE = "UTC"
