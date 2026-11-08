import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable, Optional

import numpy as np
from sqlalchemy.orm import Session

from app.core.database import JobsSessionLocal
from app.ingestion.normalize import (
    SUPPORTED_COUNTRIES, clean_skills, clean_title, dedupe_key, infer_countries, is_remote,
    looks_english, names_unsupported_place, same_company, seniority_from_title,
)
from app.models.job_posting import IngestionRun, JobPosting
from app.services.recommender_client import RecommenderClient
from app.sources.base import JobSource, RawJob

logger = logging.getLogger(__name__)

STALE_DAYS = int(os.getenv("JOB_STALE_DAYS", "4"))
ENRICH_LIMIT = int(os.getenv("JOB_ENRICH_LIMIT", "3000"))
TRANSLATE = os.getenv("JOB_TRANSLATE", "true").lower() == "true"
RUN_HEARTBEAT_TIMEOUT_MINUTES = 15
UNTRANSLATED_HASH = "untranslated"
ENRICH_BATCH_SIZE = 32
MAX_TRANSLATE_CHARS = 4999
MAX_SKILL_TEXT_CHARS = 4000
MAX_EMBED_TEXT_CHARS = 2000
COMMIT_EVERY = 200


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _content_hash(raw: RawJob) -> str:
    payload = "\x1f".join([raw.title, raw.company, raw.location or "", raw.description])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class _Translator:
    MIN_INTERVAL_SECONDS = 0.3
    MAX_ATTEMPTS = 3
    MAX_RATE_LIMITED_JOBS = 3

    def __init__(self):
        self._client = None
        self._last_call = 0.0
        self._rate_limited_jobs = 0

    @property
    def available(self) -> bool:
        return TRANSLATE and self._rate_limited_jobs < self.MAX_RATE_LIMITED_JOBS

    def to_english(self, text: str) -> Optional[str]:
        if not self.available or not text:
            return None
        from deep_translator import GoogleTranslator
        from deep_translator.exceptions import TooManyRequests

        if self._client is None:
            self._client = GoogleTranslator(source="auto", target="en")
        for attempt in range(self.MAX_ATTEMPTS):
            wait = self._last_call + self.MIN_INTERVAL_SECONDS - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._last_call = time.monotonic()
            try:
                return self._client.translate(text[:MAX_TRANSLATE_CHARS]) or None
            except TooManyRequests:
                time.sleep(2 ** attempt)
            except Exception as e:
                logger.debug("Translation failed: %s", e)
                return None
        self._rate_limited_jobs += 1
        if not self.available:
            logger.warning("Translation rate-limited repeatedly; skipping it for the rest of this run")
        return None

    def job_to_english(self, title: str, description: str) -> Optional[tuple[str, str]]:
        translated = self.to_english(f"{title}\n\n{description}")
        if not translated:
            return None
        new_title, _, new_description = translated.partition("\n")
        return (new_title.strip() or title), (new_description.strip() or description)


def _resolve_countries(raw: RawJob) -> tuple[list[str], bool]:
    remote = is_remote(raw.location, raw.remote)
    countries = [c for c in raw.countries if c in SUPPORTED_COUNTRIES] or infer_countries(raw.location)
    if not countries and raw.default_country and not names_unsupported_place(raw.location):
        countries = [raw.default_country]
    return countries, remote


def upsert_jobs(db: Session, raw_jobs: Iterable[RawJob], translator: Optional[_Translator] = None) -> dict:
    translator = translator or _Translator()
    stats = {"fetched": 0, "inserted": 0, "updated": 0, "unchanged": 0, "duplicates": 0, "skipped": 0}
    raw_jobs = list(raw_jobs)
    stats["fetched"] = len(raw_jobs)
    if not raw_jobs:
        return stats

    existing: dict[tuple[str, str], JobPosting] = {}
    keys = {(raw.source, raw.external_id) for raw in raw_jobs}
    for source in {key[0] for key in keys}:
        ids = [external_id for src, external_id in keys if src == source]
        for start in range(0, len(ids), 500):
            rows = db.query(JobPosting).filter(
                JobPosting.source == source, JobPosting.external_id.in_(ids[start:start + 500])
            )
            existing.update({(row.source, row.external_id): row for row in rows})

    now = utcnow()
    seen: set[tuple[str, str]] = set()
    pending_writes = 0
    for raw in raw_jobs:
        key = (raw.source, raw.external_id)
        if key in seen or not (raw.title and raw.url and raw.description):
            stats["skipped"] += 1
            continue
        seen.add(key)

        countries, remote = _resolve_countries(raw)
        if not countries:
            stats["skipped"] += 1  
            if key in existing:
                db.delete(existing.pop(key))
                pending_writes += 1
            continue

        content_hash = _content_hash(raw)
        row = existing.get(key)
        if row is not None and row.content_hash == content_hash:
            row.last_seen_at = now
            row.countries = ",".join(countries)
            row.remote = remote
            row.seniority = seniority_from_title(row.title)
            stats["unchanged"] += 1
            pending_writes += 1
        else:
            title, description, translated = clean_title(raw.title), raw.description, False
            stored_hash = content_hash
            if not looks_english(f"{raw.title}\n{raw.description}"):
                result = translator.job_to_english(raw.title, raw.description)
                if result:
                    title, description = clean_title(result[0]), result[1]
                    translated = True
                elif TRANSLATE:
                    stored_hash = UNTRANSLATED_HASH
                    stats["untranslated"] = stats.get("untranslated", 0) + 1

            job_dedupe_key = dedupe_key(title, raw.company)
            if row is None:
                title_part = job_dedupe_key.split("|", 1)[0]
                candidates = db.query(JobPosting).filter(
                    JobPosting.dedupe_key.like(f"{title_part}|%"), JobPosting.source != raw.source
                ).all()
                duplicate = next((
                    other for other in candidates
                    if same_company(other.company, raw.company)
                    and set(other.countries.split(",")) & set(countries)
                ), None)
                if duplicate:
                    duplicate.last_seen_at = now
                    stats["duplicates"] += 1
                    pending_writes += 1
                    continue
                row = JobPosting(source=raw.source, external_id=raw.external_id, first_seen_at=now)
                db.add(row)
                existing[key] = row
                stats["inserted"] += 1
            else:
                stats["updated"] += 1

            text_changed = row.title != title[:512] or row.description != description

            row.dedupe_key = job_dedupe_key
            row.content_hash = stored_hash
            row.title = title[:512]
            row.company = raw.company[:255]
            row.location = (raw.location or "")[:512] or None
            row.countries = ",".join(countries)
            row.remote = remote
            row.seniority = seniority_from_title(title)
            row.description = description
            row.url = raw.url
            row.translated = translated
            row.posted_at = raw.posted_at
            row.last_seen_at = now
            if text_changed:
                row.skills = None
                row.embedding = None
            pending_writes += 1

        if pending_writes >= COMMIT_EVERY:
            db.commit()
            pending_writes = 0

    db.commit()
    return stats


def enrich_pending(
    db: Session,
    client: Optional[RecommenderClient] = None,
    limit: int = ENRICH_LIMIT,
    on_batch: Optional[Callable[[], None]] = None,
) -> dict:
    """Extract skills and compute embeddings for jobs that don't have them yet, newest first."""
    client = client or RecommenderClient()
    stats = {"skills": 0, "embeddings": 0, "skills_unavailable": False, "embeddings_unavailable": False}

    rows = (
        db.query(JobPosting)
        .filter((JobPosting.skills.is_(None)) | (JobPosting.embedding.is_(None)))
        .order_by(JobPosting.posted_at.is_(None), JobPosting.posted_at.desc(), JobPosting.id.desc())
        .limit(limit)
        .all()
    )

    for start in range(0, len(rows), ENRICH_BATCH_SIZE):
        batch = rows[start:start + ENRICH_BATCH_SIZE]

        needs_skills = [row for row in batch if row.skills is None]
        if needs_skills and not stats["skills_unavailable"]:
            texts = [f"{row.title}\n{row.description[:MAX_SKILL_TEXT_CHARS]}" for row in needs_skills]
            skills = client.extract_skills_batch(texts)
            if skills is None or len(skills) != len(needs_skills):
                stats["skills_unavailable"] = True
            else:
                for row, job_skills in zip(needs_skills, skills):
                    row.skills = json.dumps(clean_skills(job_skills))
                stats["skills"] += len(needs_skills)

        needs_embedding = [row for row in batch if row.embedding is None]
        if needs_embedding and not stats["embeddings_unavailable"]:
            texts = [f"{row.title}. {row.description[:MAX_EMBED_TEXT_CHARS]}" for row in needs_embedding]
            vectors = client.embed(texts)
            if vectors is None or len(vectors) != len(needs_embedding):
                stats["embeddings_unavailable"] = True
            else:
                for row, vector in zip(needs_embedding, vectors):
                    row.embedding = np.asarray(vector, dtype=np.float32).tobytes()
                stats["embeddings"] += len(needs_embedding)

        db.commit()
        if on_batch:
            on_batch()
        if stats["skills_unavailable"] and stats["embeddings_unavailable"]:
            break

    stats["remaining"] = db.query(JobPosting).filter(
        (JobPosting.skills.is_(None)) | (JobPosting.embedding.is_(None))
    ).count()
    return stats


def prune_stale(db: Session, days: int = STALE_DAYS) -> int:
    cutoff = utcnow() - timedelta(days=days)
    deleted = db.query(JobPosting).filter(JobPosting.last_seen_at < cutoff).delete(synchronize_session=False)
    db.commit()
    return deleted


def _start_run(db: Session) -> Optional[IngestionRun]:
    """Create a run row, or return None if another run (another worker or a cron job) is in progress."""
    lock_cutoff = utcnow() - timedelta(minutes=RUN_HEARTBEAT_TIMEOUT_MINUTES)
    active = db.query(IngestionRun).filter(IngestionRun.status == "running").all()
    for run in active:
        if as_utc(run.heartbeat_at or run.started_at) > lock_cutoff:
            return None
        run.status = "abandoned"
    now = utcnow()
    run = IngestionRun(status="running", started_at=now, heartbeat_at=now)
    db.add(run)
    db.commit()
    return run


def _safe_error(error: Exception) -> str:
    """Error text without URL paths or queries: requests includes the full URL in its errors,
    and API keys travel in it (Adzuna in the query, Jooble in the path)."""
    response = getattr(error, "response", None)
    if response is not None and getattr(response, "status_code", None):
        return f"HTTP {response.status_code} {response.reason or ''}".strip()
    text = re.sub(r"(https?://[^/\s'\"]+)[^\s'\"]*", r"\1/<redacted>", str(error))
    text = re.sub(r"(url: )\S+", r"\1<redacted>", text) 
    return text[:300]


def _heartbeat(db: Session, run: IngestionRun) -> None:
    run.heartbeat_at = utcnow()
    db.commit()


def run_ingestion(sources: Optional[list[JobSource]] = None, enrich: bool = True, prune: bool = True) -> Optional[dict]:
    from app.matching.index import job_index
    from app.sources.registry import build_sources

    db = JobsSessionLocal()
    try:
        run = _start_run(db)
        if run is None:
            logger.info("Another ingestion run is in progress; skipping")
            return None

        sources = build_sources() if sources is None else sources
        logger.info("Ingestion started with %d sources", len(sources))
        translator = _Translator()
        summary: dict = {"sources": {}}
        try:
            for source in sources:
                try:
                    raw_jobs = list(source.fetch())
                except Exception as e:
                    db.rollback()
                    logger.warning("Source %s failed: %s", source.name, _safe_error(e))
                    summary["sources"][source.name] = {"error": _safe_error(e)}
                    continue
                summary["sources"][source.name] = upsert_jobs(db, raw_jobs, translator)
                logger.info("Source %s: %s", source.name, summary["sources"][source.name])
                _heartbeat(db, run)

            if prune:
                summary["pruned"] = prune_stale(db)
            if enrich:
                summary["enrichment"] = enrich_pending(db, on_batch=lambda: _heartbeat(db, run))
            summary["total_jobs"] = db.query(JobPosting).count()
            run.status = "success"
        except Exception:
            db.rollback()
            run.status = "failed"
            logger.exception("Ingestion run failed")
        finally:
            run.finished_at = utcnow()
            run.stats = json.dumps(summary)
            db.commit()
            job_index.invalidate()

        logger.info("Ingestion finished: %s jobs in index", summary.get("total_jobs"))
        return summary
    finally:
        db.close()


def ingest_now(sources: list[JobSource]) -> dict:
    """Small synchronous ingest (no run lock) used to top up the index for a specific search."""
    from app.matching.index import job_index

    db = JobsSessionLocal()
    try:
        stats = {}
        for source in sources:
            try:
                stats[source.name] = upsert_jobs(db, list(source.fetch()))
            except Exception as e:
                db.rollback()
                logger.warning("Top-up source %s failed: %s", source.name, _safe_error(e))
        stats["enrichment"] = enrich_pending(db, limit=200)
        job_index.invalidate()
        return stats
    finally:
        db.close()
