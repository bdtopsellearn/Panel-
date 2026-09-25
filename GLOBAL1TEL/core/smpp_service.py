"""
Runs the SMPP engine inside the web app and connects it to the database.

Responsibilities:
  * load carrier accounts from smpp_users so the server can authenticate binds,
  * start the listener on SMPP_SERVER_PORT (carriers connect to us),
  * start outbound binds for accounts marked smpp-client (we connect to them),
  * push every received message into ingest_sms(),
  * keep smpp_users.status / last_connected_at truthful, so "Live Sessions"
    reflects reality instead of always showing nothing.
"""
from __future__ import annotations

import asyncio
import logging

from core import config
from core.db import Database
from core.helpers import db_column_exists, db_table_exists, log_activity
from core import sms_spool
from core.sms_ingest import ingest_sms
from core.smpp_client import SmppConnectionManager, SmppServer

logger = logging.getLogger("g1t.smpp")


class SmppService:
    def __init__(self):
        self.server = SmppServer(self._on_message, self._on_status_change, self._load_accounts)
        self.manager = SmppConnectionManager(self._on_message, self._on_status_change)
        self._started = False

    # ── account loading ────────────────────────────────────────────────────
    def _load_accounts(self) -> list:
        """Carrier accounts the SMPP server will accept binds from.

        Called on every bind attempt so a newly added account works instantly,
        with no restart.

        Column mapping matters here. The panel's `smpp_users` table stores
        `username` / `password_hash` / `supplier_name`, and `password_hash` is a
        one-way PBKDF2 digest. An SMPP bind PDU carries the password in
        plaintext, so a one-way digest can never be compared against it. The
        reversible copy lives in `bind_password` (added by
        migrations/smpp_bind_credentials_upgrade.sql); the engine's
        _decode_password() reads it. Without this mapping every bind is
        rejected and every inbound OTP is lost.
        """
        db = Database.get_instance()
        if not db_table_exists(db, "smpp_users"):
            return []
        try:
            rows = db.query(
                "SELECT * FROM smpp_users WHERE status <> 'disabled' OR status IS NULL"
            ).fetchall()
        except Exception as exc:
            logger.warning("Could not load SMPP accounts: %s", exc)
            return []

        accounts = []
        for row in rows:
            # system_id falls back to username so accounts created before the
            # migration (and via the plain admin form) still bind.
            system_id = (row.get("system_id") or row.get("username") or "").strip()
            if not system_id:
                continue
            secret = (row.get("bind_password")
                      or row.get("smpp_password")
                      or row.get("password")
                      or "")
            if not secret:
                logger.warning(
                    "SMPP account '%s' has no bind password stored - it cannot "
                    "authenticate a bind. Re-save it in Admin > SMPP Accounts.",
                    system_id)
            port = row.get("port")
            accounts.append({
                "id": row.get("id"),
                "company": (row.get("supplier_name") or row.get("company")
                            or system_id),
                "system_id": system_id,
                "password": secret,
                "host": row.get("host") or "",
                "port": int(port) if port else 0,
                "interconnect_type": (row.get("interconnect_type")
                                      or "smpp-server"),
                "bind_type": row.get("bind_type") or "TR",
            })
        return accounts

    # ── callbacks from the engine ──────────────────────────────────────────
    async def _on_message(self, source, destination, message, sms_id, company):
        """A carrier delivered a message. ingest_sms touches the database, so
        it runs in a worker thread and never blocks the event loop."""
        try:
            result = await asyncio.to_thread(
                ingest_sms, source, destination, message, sms_id, str(company or "")
            )
            if result.get("assigned"):
                logger.info("OTP stored: %s <- %s (cdr %s)",
                            result.get("number"), source, result.get("cdr_id"))
            else:
                logger.info("SMS logged but not billed: %s (%s)",
                            destination, result.get("message") or result.get("error"))
        except Exception as exc:
            # The carrier has already had its deliver_sm_resp and will never
            # resend, so the message goes to disk and is replayed until it
            # reaches the database. This is what stops an OTP being lost when
            # MySQL blips.
            logger.exception("ingest_sms failed for %s: %s", destination, exc)
            await asyncio.to_thread(
                sms_spool.spool, source, destination, message, sms_id,
                str(company or ""), None, f"{type(exc).__name__}: {exc}")

    async def _on_status_change(self, account_id, status):
        try:
            await asyncio.to_thread(self._write_status, account_id, status)
        except Exception as exc:
            logger.warning("Could not persist SMPP status: %s", exc)

    def _write_status(self, account_id, status):
        """Record that a carrier is (or was) connected.

        Deliberately does NOT touch `smpp_users.status`. That column is the
        admin's own setting - active / suspended / disabled - and writing
        transport state into it did two bad things: it silently reactivated an
        account an admin had suspended, and values like 'disconnected' are not
        in the ENUM, so MySQL rejected the write with "Data truncated for
        column 'status'". Liveness comes from last_connected_at plus the
        engine's in-memory bound set instead.
        """
        db = Database.get_instance()
        if not db_table_exists(db, "smpp_users"):
            return
        if status != "active":
            return
        if not db_column_exists(db, "smpp_users", "last_connected_at"):
            return
        try:
            # last_connected_at was never written by the PHP build, which is why
            # the Live Sessions page was permanently empty.
            db.query("UPDATE smpp_users SET last_connected_at = NOW() WHERE id = ?",
                     [account_id])
        except Exception as exc:
            logger.warning("SMPP status update failed: %s", exc)

    # ── lifecycle ──────────────────────────────────────────────────────────
    async def start(self):
        if self._started or not config.SMPP_SERVER_ENABLED:
            return
        try:
            await self.server.start(config.SMPP_SERVER_HOST, config.SMPP_SERVER_PORT)
            self._started = True
            logger.info("SMPP server ready on %s:%s",
                        config.SMPP_SERVER_HOST, config.SMPP_SERVER_PORT)
        except OSError as exc:
            # A busy port must not stop the web panel from booting.
            logger.error("Could not bind SMPP port %s: %s", config.SMPP_SERVER_PORT, exc)
            return
        await self.sync_outbound()

    async def sync_outbound(self):
        """(Re)build outbound binds after accounts change."""
        try:
            accounts = await asyncio.to_thread(self._load_accounts)
            await self.manager.sync_with_accounts(accounts)
        except Exception as exc:
            logger.warning("Outbound SMPP sync failed: %s", exc)

    async def stop(self):
        await self.manager.stop_all()
        await self.server.stop()
        self._started = False

    # ── status for the admin panel ─────────────────────────────────────────
    def status(self) -> dict:
        return {
            "server_running": self.server.running,
            "listen_host": config.SMPP_SERVER_HOST,
            "listen_port": config.SMPP_SERVER_PORT,
            "bound_accounts": self.server.bound_accounts,
            "outbound_connections": list(self.manager.connections.keys()),
        }


service = SmppService()
