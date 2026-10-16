"""
GLOBAL1TEL — main application.

Replaces router.php: same URL map, same gating rules, same static layout, so
every existing HTML/CSS/JS file in public/ keeps working untouched.

    /                       -> /ints/login
    /adminlogin             -> login page (admin entry point)
    /ints/login             -> login page
    /ints/signin            -> login backend
    /ints/<role>/<Page>     -> role-gated panel HTML
    /ints/<role>/res/<x>    -> legacy DataTables endpoints
    /api/<name>[.php]       -> JSON APIs
    everything else         -> static files under public/

Run with:  python run.py        (or: uvicorn main:app --host 0.0.0.0 --port 80)
"""
from __future__ import annotations

import asyncio
import logging
import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse,
)
from fastapi.staticfiles import StaticFiles

from api import admin, auth, cdr, dashboard, legacy, misc, numbers, ranges, smpp, test_sms, users
from core import config
from core.db import DatabaseError
from core import sms_spool
from core.sms_ingest import ingest_sms
from core.helpers import ApiError, json_response, log_activity
from core.session import apply_session_cookie, client_ip, guard, load_session
from core.smpp_service import service as smpp_service

logging.basicConfig(
    level=logging.DEBUG if config.APP_DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("g1t")

# How often the disk spool is drained back into the database.
SPOOL_REPLAY_SECONDS = 60

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"

ROLES = ("admin", "manager", "agent", "client", "test")
PAGE_RE = re.compile(r"^[A-Za-z0-9_-]+$")

NO_STORE = {"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("%s starting (env=%s)", config.APP_NAME, config.APP_ENV)
    try:
        await smpp_service.start()
    except Exception as exc:
        # The SMPP listener must never prevent the web panel from booting.
        logger.error("SMPP engine did not start: %s", exc)

    # Drain anything that could not reach the database last time (e.g. MySQL was
    # restarting while a carrier was delivering). Runs on boot and every minute.
    async def spool_drain():
        while True:
            try:
                if sms_spool.pending_count():
                    await asyncio.to_thread(sms_spool.replay, ingest_sms)
            except Exception as exc:
                logger.warning("Spool replay failed: %s", exc)
            await asyncio.sleep(SPOOL_REPLAY_SECONDS)

    drain_task = asyncio.create_task(spool_drain())

    yield

    drain_task.cancel()
    try:
        await drain_task
    except (asyncio.CancelledError, Exception):
        pass
    try:
        await smpp_service.stop()
    except Exception:
        pass


app = FastAPI(title=config.APP_NAME, docs_url=None, redoc_url=None,
              openapi_url=None, lifespan=lifespan)

# The PHP build sent Access-Control-Allow-Origin: * with credentials, which any
# site could abuse. Credentials are only allowed for explicitly listed origins.
if config.CORS_ORIGINS == ["*"]:
    app.add_middleware(CORSMiddleware, allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
                       allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
else:
    app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS,
                       allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def session_and_guard(request: Request, call_next):
    """Loads the session, applies flood protection and security headers."""
    path = request.url.path
    ip = client_ip(request)
    request.state.client_ip = ip

    is_static = path.startswith("/ints/assets") or path.startswith("/assets") or bool(
        re.search(r"\.(css|js|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|eot|map)$", path, re.I))
    banned_for = guard.check_request(ip, is_static)
    if banned_for is not None:
        return JSONResponse({"error": "Too many requests. Please slow down.",
                             "retry_after": banned_for},
                            status_code=429, headers={"Retry-After": str(banned_for)})

    # 2 MB body cap — a giant POST should be rejected before it is parsed.
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > 2 * 1024 * 1024 and not path.startswith(
            "/api/admin"):
        return JSONResponse({"error": "Request body too large"}, status_code=413)

    request.state.session = load_session(request.cookies.get(config.SESSION_NAME))

    try:
        response = await call_next(request)
    except ApiError as exc:
        response = JSONResponse(exc.payload, status_code=exc.status_code)
    except DatabaseError:
        logger.error("Database unavailable for %s", path)
        response = JSONResponse({"error": "Service temporarily unavailable"}, status_code=503)
    except Exception:
        logger.error(
            "\n"
            "\U0001F534 ================ SERVER ERROR ================\n"
            "  Path : %s %s\n"
            "  (full traceback below)",
            request.method, path, exc_info=True,
        )
        response = JSONResponse({"error": "Internal server error"}, status_code=500)

    apply_session_cookie(response, request.state.session,
                         secure=request.url.scheme == "https")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-XSS-Protection", "1; mode=block")
    return response


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(exc.payload, status_code=exc.status_code)


# ── API routers ─────────────────────────────────────────────────────────────
for module in (auth, dashboard, users, numbers, ranges, cdr, misc, test_sms, smpp, admin):
    app.include_router(module.router)
app.include_router(legacy.router)


# ── login pages ─────────────────────────────────────────────────────────────
def _login_page() -> HTMLResponse:
    path = PUBLIC / "ints" / "login.html"
    if not path.is_file():
        return HTMLResponse("<h1>login.html is missing</h1>", status_code=500)
    return HTMLResponse(path.read_text(encoding="utf-8", errors="replace"), headers=NO_STORE)


@app.get("/")
async def home():
    return RedirectResponse("/ints/login", status_code=302)


@app.get("/adminlogin")
@app.get("/adminlogin/")
async def admin_login():
    """Dedicated Admin login gate. Uses the same hardened login backend."""
    return _login_page()


@app.get("/ints/login")
@app.get("/ints/login.html")
async def ints_login():
    return _login_page()


@app.get("/ints/logout")
@app.get("/ints/logout.php")
async def ints_logout(request: Request):
    session = request.state.session
    if session.get("user_id"):
        log_activity(session.get("user_id"), "logout", "User logged out",
                     request.state.client_ip)
    session.destroy()
    return RedirectResponse("/ints/login", status_code=302)


# ── role-gated panel pages ──────────────────────────────────────────────────
def _serve_panel_page(request: Request, role: str, page: str):
    session = request.state.session
    if not session.logged_in or session.role != role:
        return RedirectResponse("/adminlogin" if role == "admin" else "/ints/login",
                                status_code=302)
    if not PAGE_RE.match(page):
        return PlainTextResponse("404 Not Found", status_code=404)

    path = PUBLIC / "ints" / role / f"{page}.html"
    if not path.is_file():
        return PlainTextResponse("404 Not Found", status_code=404)
    return HTMLResponse(path.read_text(encoding="utf-8", errors="replace"), headers=NO_STORE)


@app.get("/ints/{role}/{page}")
async def panel_page(role: str, page: str, request: Request):
    if role not in ROLES:
        return PlainTextResponse("404 Not Found", status_code=404)
    if page.endswith(".html"):
        page = page[:-5]
    return _serve_panel_page(request, role, page)


@app.get("/ints/panel-gate.php")
async def panel_gate(request: Request):
    """Server-side HTML gate used by the Apache/Nginx rewrites."""
    role = str(request.query_params.get("role") or "").lower()
    page = str(request.query_params.get("page") or "")
    if role not in ROLES or not PAGE_RE.match(page):
        return PlainTextResponse("404 Not Found", status_code=404)
    return _serve_panel_page(request, role, page)


# ── static files ────────────────────────────────────────────────────────────
if (PUBLIC / "ints" / "assets").is_dir():
    app.mount("/ints/assets", StaticFiles(directory=PUBLIC / "ints" / "assets"),
              name="ints-assets")
if (PUBLIC / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=PUBLIC / "assets"), name="assets")


@app.get("/health")
async def health():
    from core.db import Database
    return json_response({
        "app": config.APP_NAME,
        "database": Database.get_instance().ping(),
        "smpp": smpp_service.status(),
    })


@app.get("/{full_path:path}")
async def static_fallback(full_path: str, request: Request):
    """Serve any other file under public/, plus clean .html URLs — the tail of
    router.php."""
    if ".." in full_path:
        return PlainTextResponse("404 Not Found", status_code=404)

    candidate = (PUBLIC / full_path).resolve()
    try:
        candidate.relative_to(PUBLIC.resolve())
    except ValueError:
        return PlainTextResponse("404 Not Found", status_code=404)

    if candidate.is_file():
        return FileResponse(candidate)

    html = candidate.with_suffix(candidate.suffix + ".html") if candidate.suffix else Path(
        str(candidate) + ".html")
    if html.is_file():
        return HTMLResponse(html.read_text(encoding="utf-8", errors="replace"))

    return PlainTextResponse("404 Not Found", status_code=404)


