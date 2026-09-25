"""
GLOBAL1TEL - Database layer (Python port of the PHP `Database` class).

Same shape as the PHP original so the ported API code reads the same:
    db = Database.get_instance()
    rows = db.query("SELECT ... WHERE id=?", [id]).fetchall()

Uses PyMySQL (pure Python — installs on Termux and any VPS with no compiler)
with a small thread-safe connection pool, autocommit on, and `?` placeholders
translated to `%s` so every SQL string from the PHP build works unchanged.
"""
from __future__ import annotations

import logging
import threading
from queue import Queue, Empty

import pymysql
from pymysql.cursors import DictCursor

from core import config

logger = logging.getLogger("g1t.db")


class DatabaseError(Exception):
    """Raised when the database is unreachable — mapped to HTTP 503 upstream."""


class _Result:
    """Mimics the PDOStatement surface the PHP code used: fetch/fetchAll/key_pair."""

    __slots__ = ("rows", "rowcount", "lastrowid")

    def __init__(self, rows, rowcount, lastrowid):
        self.rows = rows
        self.rowcount = rowcount
        self.lastrowid = lastrowid

    def fetch(self):
        """PDO::fetch() -> first row as dict, or None."""
        return self.rows[0] if self.rows else None

    def fetchall(self):
        """PDO::fetchAll() -> list of dicts."""
        return self.rows

    def fetch_key_pair(self):
        """PDO::FETCH_KEY_PAIR -> {first_column: second_column}."""
        out = {}
        for row in self.rows:
            values = list(row.values())
            if len(values) >= 2:
                out[values[0]] = values[1]
        return out

    def fetch_column(self, index: int = 0):
        """PDO::FETCH_COLUMN -> flat list of one column."""
        out = []
        for row in self.rows:
            values = list(row.values())
            if len(values) > index:
                out.append(values[index])
        return out

    def scalar(self, default=None):
        row = self.fetch()
        if not row:
            return default
        values = list(row.values())
        return values[0] if values else default


def _to_pymysql(sql: str) -> str:
    """Translate PDO-style `?` placeholders to PyMySQL's `%s`.

    Literal `%` in the SQL (DATE_FORMAT masks, LIKE patterns) must be escaped
    to `%%` first, otherwise PyMySQL treats it as a format specifier and the
    query dies with "unsupported format character" — this bit every
    DATE_FORMAT(...,'%Y-%m') query in the reports code.
    """
    return sql.replace("%", "%%").replace("?", "%s")


class Database:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._pool: Queue = Queue(maxsize=16)
        self._created = 0
        self._pool_lock = threading.Lock()

    # ── singleton, same as Database::getInstance() ──────────────────────────
    @classmethod
    def get_instance(cls) -> "Database":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ── connections ────────────────────────────────────────────────────────
    def _new_connection(self):
        try:
            conn = pymysql.connect(
                host=config.DB_HOST,
                port=config.DB_PORT,
                user=config.DB_USER,
                password=config.DB_PASS,
                database=config.DB_NAME,
                charset="utf8mb4",
                cursorclass=DictCursor,
                autocommit=True,
                connect_timeout=10,
                read_timeout=60,
                write_timeout=60,
                init_command="SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci",
            )
        except pymysql.Error as exc:
            logger.error("Database connection failed: %s", exc)
            raise DatabaseError("Service temporarily unavailable") from exc
        with conn.cursor() as cur:
            cur.execute("SET time_zone = '+00:00'")
        return conn

    def _acquire(self):
        try:
            conn = self._pool.get_nowait()
        except Empty:
            return self._new_connection()
        try:
            conn.ping(reconnect=True)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass
            return self._new_connection()
        return conn

    def _release(self, conn) -> None:
        try:
            self._pool.put_nowait(conn)
        except Exception:
            try:
                conn.close()
            except Exception:
                pass

    # ── query, same signature as the PHP helper ────────────────────────────
    def query(self, sql: str, params=None) -> _Result:
        params = list(params or [])
        conn = self._acquire()
        try:
            with conn.cursor() as cur:
                cur.execute(_to_pymysql(sql), params)
                rows = cur.fetchall() if cur.description else []
                return _Result(list(rows), cur.rowcount, cur.lastrowid)
        except pymysql.Error as exc:
            logger.error("Query error: %s SQL: %s", exc, sql)
            raise
        finally:
            self._release(conn)

    def execute_many(self, sql: str, seq_of_params) -> int:
        conn = self._acquire()
        try:
            with conn.cursor() as cur:
                cur.executemany(_to_pymysql(sql), list(seq_of_params))
                return cur.rowcount
        finally:
            self._release(conn)

    def transaction(self):
        """`with db.transaction() as tx:` — commits on exit, rolls back on error."""
        return _Transaction(self)

    def ping(self) -> bool:
        try:
            self.query("SELECT 1")
            return True
        except Exception:
            return False


class _Transaction:
    def __init__(self, database: Database):
        self._database = database
        self._conn = None

    def __enter__(self):
        self._conn = self._database._acquire()
        self._conn.begin()
        return self

    def query(self, sql: str, params=None) -> _Result:
        params = list(params or [])
        with self._conn.cursor() as cur:
            cur.execute(_to_pymysql(sql), params)
            rows = cur.fetchall() if cur.description else []
            return _Result(list(rows), cur.rowcount, cur.lastrowid)

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
        finally:
            self._database._release(self._conn)
        return False


def get_db() -> Database:
    return Database.get_instance()
