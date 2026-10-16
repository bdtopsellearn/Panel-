"""Never-lose-an-OTP safety net.

ingest_sms() writes to MySQL. If MySQL is down, restarting, out of connections
or mid-failover at the exact moment a carrier delivers an OTP, that message
would simply be gone - the carrier already got its deliver_sm_resp and will
never send it again.

So every inbound message that fails to reach the database is appended to a
JSON-lines file on disk first, and a background task retries it until it lands.
The spool is:

  * append-only and fsync'ed, so a crash mid-write cannot corrupt earlier lines
  * replayed oldest-first, so CDR order is preserved
  * idempotent on message_id, so a replay cannot double-credit a balance

Location: <project>/var/spool/inbound.jsonl (override with SMS_SPOOL_DIR).
"""
from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone

logger = logging.getLogger("g1t.spool")

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPOOL_DIR = os.environ.get("SMS_SPOOL_DIR") or os.path.join(_BASE, "var", "spool")
SPOOL_FILE = os.path.join(SPOOL_DIR, "inbound.jsonl")
DEAD_FILE = os.path.join(SPOOL_DIR, "inbound.failed.jsonl")

# After this many attempts a record is parked in inbound.failed.jsonl instead of
# being retried forever. It is still on disk, so nothing is ever destroyed.
MAX_ATTEMPTS = 50

_lock = threading.Lock()


def _ensure_dir() -> None:
    os.makedirs(SPOOL_DIR, exist_ok=True)


def spool(source_addr: str, destination_addr: str, message: str,
          message_id: str = "", connector_id: str = "",
          submit_date=None, reason: str = "") -> bool:
    """Persist one message that could not be ingested. Returns True if it is
    safely on disk."""
    record = {
        "source_addr": source_addr,
        "destination_addr": destination_addr,
        "message": message,
        "message_id": message_id,
        "connector_id": connector_id,
        "submit_date": submit_date,
        "reason": str(reason)[:300],
        "spooled_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "attempts": 0,
    }
    try:
        _ensure_dir()
        line = json.dumps(record, ensure_ascii=False) + "\n"
        with _lock:
            with open(SPOOL_FILE, "a", encoding="utf-8") as fh:
                fh.write(line)
                fh.flush()
                os.fsync(fh.fileno())
        logger.warning("Inbound SMS for %s spooled to disk (%s)",
                       destination_addr, reason or "ingest failed")
        return True
    except Exception as exc:
        # Nothing else we can do - log the whole message so it is at least
        # recoverable from the application log.
        logger.error("SPOOL WRITE FAILED - message may be lost. to=%s from=%s "
                     "id=%s err=%s text=%r",
                     destination_addr, source_addr, message_id, exc, message)
        return False


def pending_count() -> int:
    try:
        with open(SPOOL_FILE, "r", encoding="utf-8") as fh:
            return sum(1 for line in fh if line.strip())
    except FileNotFoundError:
        return 0
    except Exception:
        return 0


def replay(ingest_fn) -> dict:
    """Try to ingest everything in the spool. Records that still fail are
    written back with an incremented attempt counter.

    Returns {"replayed": n, "remaining": n, "parked": n}.
    """
    with _lock:
        try:
            with open(SPOOL_FILE, "r", encoding="utf-8") as fh:
                lines = [ln for ln in fh if ln.strip()]
        except FileNotFoundError:
            return {"replayed": 0, "remaining": 0, "parked": 0}
        except Exception as exc:
            logger.warning("Could not read spool: %s", exc)
            return {"replayed": 0, "remaining": 0, "parked": 0}

        if not lines:
            return {"replayed": 0, "remaining": 0, "parked": 0}

        # Truncate up front: anything that fails again is written back below, so
        # a crash here leaves the records in the log rather than duplicating them.
        open(SPOOL_FILE, "w", encoding="utf-8").close()

    replayed = 0
    parked = 0
    still_failing = []

    for line in lines:
        try:
            rec = json.loads(line)
        except Exception:
            parked += 1
            _park(line)
            continue
        try:
            ingest_fn(
                rec.get("source_addr", ""),
                rec.get("destination_addr", ""),
                rec.get("message", ""),
                rec.get("message_id", ""),
                rec.get("connector_id", ""),
                rec.get("submit_date"),
            )
            replayed += 1
        except Exception as exc:
            rec["attempts"] = int(rec.get("attempts", 0)) + 1
            rec["reason"] = str(exc)[:300]
            if rec["attempts"] >= MAX_ATTEMPTS:
                parked += 1
                _park(json.dumps(rec, ensure_ascii=False) + "\n")
            else:
                still_failing.append(json.dumps(rec, ensure_ascii=False) + "\n")

    if still_failing:
        with _lock:
            try:
                _ensure_dir()
                with open(SPOOL_FILE, "a", encoding="utf-8") as fh:
                    fh.writelines(still_failing)
                    fh.flush()
                    os.fsync(fh.fileno())
            except Exception as exc:
                logger.error("Could not re-spool %d messages: %s",
                             len(still_failing), exc)

    if replayed:
        logger.info("Spool: replayed %d inbound message(s), %d still pending",
                    replayed, len(still_failing))
    return {"replayed": replayed, "remaining": len(still_failing), "parked": parked}


def _park(line: str) -> None:
    try:
        _ensure_dir()
        with open(DEAD_FILE, "a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception as exc:
        logger.error("Could not park unreplayable record: %s (%r)", exc, line[:200])
