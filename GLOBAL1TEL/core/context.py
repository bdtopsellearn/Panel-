"""
Shared request context for every ported endpoint.

Each PHP api file opened with the same four lines:

    session_name(SESSION_NAME); session_start();
    if (!$_SESSION['logged_in']) jsonResponse(['error'=>'Unauthorized'], 401);
    $userId = $_SESSION['user_id']; $role = $_SESSION['role'];
    $db = Database::getInstance();

`Ctx` is that preamble, resolved once by FastAPI and handed to the handler.
"""
from __future__ import annotations

import json
from urllib.parse import parse_qs

from fastapi import Request

from core.db import Database
from core.helpers import ApiError, to_int
from core.session import Session


class Ctx:
    """Everything a ported handler used to read out of globals."""

    __slots__ = ("request", "session", "db", "user_id", "role", "parent_id",
                 "username", "_json_cache", "_form_cache")

    def __init__(self, request: Request):
        self.request = request
        self.session: Session = request.state.session
        self.db: Database = Database.get_instance()
        self.user_id = to_int(self.session.get("user_id"))
        self.role = str(self.session.get("role") or "")
        self.parent_id = self.session.get("parent_id")
        self.username = str(self.session.get("username") or "")
        self._json_cache = None
        self._form_cache = None

    # ── request data ───────────────────────────────────────────────────────
    @property
    def method(self) -> str:
        return self.request.method.upper()

    def q(self, key: str, default=None):
        """$_GET['key']"""
        value = self.request.query_params.get(key)
        return default if value is None else value

    def q_int(self, key: str, default: int = 0) -> int:
        return to_int(self.q(key), default)

    async def body(self) -> dict:
        """getJsonInput() with a form-post fallback, exactly like the PHP:
            $input = getJsonInput(); if (empty($input)) $input = $_POST;"""
        if self._json_cache is not None:
            return self._json_cache
        raw = await self.request.body()
        data: dict = {}
        if raw:
            content_type = (self.request.headers.get("content-type") or "").lower()
            if "application/json" in content_type or raw.lstrip()[:1] in (b"{", b"["):
                try:
                    parsed = json.loads(raw.decode("utf-8", errors="replace"))
                    if isinstance(parsed, dict):
                        data = parsed
                except Exception:
                    data = {}
            if not data:
                try:
                    text = raw.decode("utf-8", errors="replace")
                    data = {k: v[0] for k, v in parse_qs(text, keep_blank_values=True).items()}
                except Exception:
                    data = {}
        self._json_cache = data
        return data

    async def value(self, key: str, default=None):
        """One field from the JSON/form body."""
        body = await self.body()
        value = body.get(key)
        return default if value is None else value

    def all_params(self) -> dict:
        """Every query param flattened, for DataTables-style requests."""
        return dict(self.request.query_params)

    # ── guards (ports the inline role checks) ──────────────────────────────
    def require_login(self):
        if not self.session.logged_in:
            raise ApiError("Unauthorized", 401)
        if self.session.expired():
            self.session.destroy()
            raise ApiError({"error": "Session expired", "authenticated": False}, 401)
        return self

    def require_role(self, *roles):
        self.require_login()
        if self.role not in roles:
            raise ApiError("Access denied", 403)
        return self

    def is_admin(self) -> bool:
        return self.role == "admin"


async def get_ctx(request: Request) -> Ctx:
    """FastAPI dependency: an unauthenticated context (login/captcha use it)."""
    return Ctx(request)


async def get_auth_ctx(request: Request) -> Ctx:
    """FastAPI dependency: rejects anonymous callers with 401, like every
    protected PHP endpoint did on its first three lines."""
    ctx = Ctx(request)
    ctx.require_login()
    ctx.session.touch()
    return ctx
