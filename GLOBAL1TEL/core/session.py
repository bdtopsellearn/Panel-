"""
GLOBAL1TEL - Session + rate limiting.

PHP kept $_SESSION in server-side files keyed by a cookie. Here the same data
travels in one signed cookie (name unchanged: global1tel_session), which means:
  - no session directory to keep writable,
  - sessions survive a restart / multiple workers,
  - the cookie is signed, so its contents cannot be forged.

The dict keys are exactly the ones the PHP build set — user_id, username,
role, parent_id, full_name, timezone, logged_in, login_time — so every ported
handler reads them the same way.
"""
from __future__ import annotations

import json
import logging
import secrets
import threading
import time

from itsdangerous import BadSignature, URLSafeSerializer

from core import config

logger = logging.getLogger("g1t.session")

_serializer = URLSafeSerializer(config.SESSION_SECRET, salt="global1tel-session")


class Session(dict):
    """$_SESSION replacement. `dirty` tells the middleware to re-issue the cookie."""

    def __init__(self, data=None):
        super().__init__(data or {})
        self.dirty = False
        self.destroyed = False
        if not self.get("sid"):
            self["sid"] = secrets.token_hex(16)
            self.dirty = True

    # ── PHP-ish accessors ──────────────────────────────────────────────────
    @property
    def sid(self) -> str:
        """session_id() equivalent — the captcha table is keyed on this."""
        return str(self.get("sid", ""))

    @property
    def logged_in(self) -> bool:
        return bool(self.get("logged_in"))

    @property
    def user_id(self):
        return self.get("user_id")

    @property
    def role(self) -> str:
        return str(self.get("role") or "")

    def set(self, key, value):
        self[key] = value
        self.dirty = True

    def update_many(self, data: dict):
        super().update(data)
        self.dirty = True

    def expired(self) -> bool:
        if not self.logged_in:
            return False
        return (time.time() - float(self.get("login_time") or 0)) > config.SESSION_LIFETIME

    def touch(self):
        """Extend the sliding window, same as $_SESSION['login_time'] = time()."""
        self["login_time"] = int(time.time())
        self.dirty = True

    def destroy(self):
        """session_destroy() — keeps a fresh sid so the login page still has one."""
        sid = secrets.token_hex(16)
        self.clear()
        self["sid"] = sid
        self.dirty = True
        self.destroyed = True


def load_session(raw_cookie: str | None) -> Session:
    if not raw_cookie:
        return Session()
    try:
        data = _serializer.loads(raw_cookie)
        if not isinstance(data, dict):
            return Session()
        return Session(data)
    except BadSignature:
        # Tampered or signed with a different key — start clean rather than trust it.
        return Session()
    except Exception:
        return Session()


def dump_session(session: Session) -> str:
    return _serializer.dumps(dict(session))


def apply_session_cookie(response, session: Session, secure: bool = False) -> None:
    if not session.dirty:
        return
    response.set_cookie(
        key=config.SESSION_NAME,
        value=dump_session(session),
        max_age=config.SESSION_LIFETIME,
        path="/",
        httponly=True,
        samesite="lax",
        secure=secure,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Rate limiting — ports checkRateLimit() and the login brute-force helpers.
# PHP stored counters in temp files; here they live in memory (faster, and
# there is one long-lived process instead of one per request).
# ─────────────────────────────────────────────────────────────────────────────
class _Guard:
    def __init__(self):
        self._lock = threading.Lock()
        self._requests: dict[str, list] = {}
        self._bans: dict[str, float] = {}
        self._login_attempts: dict[str, list] = {}
        self._login_bans: dict[str, float] = {}

    # ── general flood protection ───────────────────────────────────────────
    def check_request(self, ip: str, is_static: bool = False):
        """Returns None if allowed, else the number of seconds still banned."""
        cfg = config.RATE_LIMIT
        if not cfg["enabled"] or ip in cfg["whitelist"]:
            return None
        limit = cfg["static_max_requests"] if is_static else cfg["max_requests"]
        now = time.time()
        with self._lock:
            banned_until = self._bans.get(ip)
            if banned_until and banned_until > now:
                return int(banned_until - now)
            if banned_until:
                self._bans.pop(ip, None)

            bucket = [t for t in self._requests.get(ip, []) if t > now - 60]
            if len(bucket) >= limit:
                self._bans[ip] = now + cfg["ban_duration"]
                self._requests[ip] = []
                return cfg["ban_duration"]
            bucket.append(now)
            self._requests[ip] = bucket

            if len(self._requests) > 20000:
                self._prune(now)
        return None

    def _prune(self, now: float):
        for key in [k for k, v in self._requests.items() if not v or v[-1] < now - 120]:
            self._requests.pop(key, None)
        for key in [k for k, v in self._bans.items() if v < now]:
            self._bans.pop(key, None)

    # ── login brute force ──────────────────────────────────────────────────
    def _login_key(self, ip: str, username) -> str:
        return f"{ip}|{username or ''}"

    def check_login(self, ip: str, username=None) -> dict:
        cfg = config.LOGIN_RATE_LIMIT
        if not cfg["enabled"]:
            return {"allowed": True, "attempts": 0, "remaining": cfg["max_attempts"]}
        key = self._login_key(ip, username)
        now = time.time()
        with self._lock:
            banned_until = self._login_bans.get(key)
            if banned_until and banned_until > now:
                return {"allowed": False, "remaining": int(banned_until - now)}
            if banned_until:
                self._login_bans.pop(key, None)
            attempts = [t for t in self._login_attempts.get(key, []) if t > now - cfg["window"]]
            self._login_attempts[key] = attempts
            return {
                "allowed": True,
                "attempts": len(attempts),
                "remaining": cfg["max_attempts"] - len(attempts),
            }

    def record_failed_login(self, ip: str, username=None) -> None:
        cfg = config.LOGIN_RATE_LIMIT
        key = self._login_key(ip, username)
        now = time.time()
        with self._lock:
            attempts = [t for t in self._login_attempts.get(key, []) if t > now - cfg["window"]]
            attempts.append(now)
            self._login_attempts[key] = attempts
            if len(attempts) >= cfg["max_attempts"]:
                self._login_bans[key] = now + cfg["ban_duration"]

    def clear_login(self, ip: str, username=None) -> None:
        key = self._login_key(ip, username)
        with self._lock:
            self._login_attempts.pop(key, None)
            self._login_bans.pop(key, None)

    # ── admin visibility ───────────────────────────────────────────────────
    def status(self) -> dict:
        now = time.time()
        with self._lock:
            return {
                "tracked_ips": len(self._requests),
                "banned_ips": [
                    {"ip": ip, "seconds_left": int(until - now)}
                    for ip, until in self._bans.items()
                    if until > now
                ],
                "login_locked": [
                    {"key": key, "seconds_left": int(until - now)}
                    for key, until in self._login_bans.items()
                    if until > now
                ],
                "limits": {
                    "requests_per_minute": config.RATE_LIMIT["max_requests"],
                    "static_per_minute": config.RATE_LIMIT["static_max_requests"],
                    "ban_seconds": config.RATE_LIMIT["ban_duration"],
                    "login_attempts": config.LOGIN_RATE_LIMIT["max_attempts"],
                },
            }

    def unban(self, ip: str) -> None:
        with self._lock:
            self._bans.pop(ip, None)
            self._requests.pop(ip, None)
            for key in [k for k in self._login_bans if k.startswith(ip + "|")]:
                self._login_bans.pop(key, None)
                self._login_attempts.pop(key, None)


guard = _Guard()


def client_ip(request) -> str:
    """Real client IP behind Cloudflare / nginx, falling back to the socket peer."""
    for header in ("cf-connecting-ip", "x-forwarded-for", "x-real-ip"):
        value = request.headers.get(header)
        if value:
            return value.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"
