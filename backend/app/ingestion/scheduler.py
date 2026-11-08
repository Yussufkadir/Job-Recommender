import logging
import os
import threading
from datetime import timedelta

from app.core.database import JobsSessionLocal
from app.ingestion.pipeline import as_utc, run_ingestion, utcnow
from app.models.job_posting import IngestionRun

logger = logging.getLogger(__name__)

INTERVAL_HOURS = float(os.getenv("JOB_INGEST_INTERVAL_HOURS", "6"))
STARTUP_DELAY_SECONDS = float(os.getenv("JOB_INGEST_STARTUP_DELAY_SECONDS", "30"))
LOCK_RETRY_SECONDS = 300

_stop = threading.Event()
_thread: threading.Thread | None = None


def is_enabled() -> bool:
    return os.getenv("JOB_INGEST_ENABLED", "true").lower() == "true"


def _seconds_until_due() -> float:
    db = JobsSessionLocal()
    try:
        last = (
            db.query(IngestionRun)
            .filter(IngestionRun.status == "success")
            .order_by(IngestionRun.finished_at.desc())
            .first()
        )
        if last is None or last.finished_at is None:
            return 0
        due_at = as_utc(last.finished_at) + timedelta(hours=INTERVAL_HOURS)
        return max((due_at - utcnow()).total_seconds(), 0)
    finally:
        db.close()


def _loop() -> None:
    if _stop.wait(STARTUP_DELAY_SECONDS):
        return
    while not _stop.is_set():
        try:
            wait = _seconds_until_due()
            if wait > 0:
                logger.info("Next job ingestion in %.0f minutes", wait / 60)
                if _stop.wait(wait):
                    return
            if run_ingestion() is None:
                if _stop.wait(LOCK_RETRY_SECONDS):
                    return
        except Exception:
            logger.exception("Scheduled ingestion failed")
            if _stop.wait(600):
                return


def start() -> None:
    global _thread
    if not is_enabled() or (_thread and _thread.is_alive()):
        return
    _stop.clear()
    _thread = threading.Thread(target=_loop, name="job-ingestion", daemon=True)
    _thread.start()
    logger.info("Job ingestion scheduler started (every %.1f hours)", INTERVAL_HOURS)


def stop() -> None:
    _stop.set()
