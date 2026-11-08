from fastapi import APIRouter, BackgroundTasks, Depends, Request, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional
import json
import logging
import threading
import time

from app.routers.auth import limiter
from app.core.database import get_jobs_db
from app.core.security import get_current_user
from app.ingestion.normalize import COUNTRY_NAMES, SUPPORTED_COUNTRIES
from app.ingestion.pipeline import as_utc, ingest_now
from app.matching.ranker import rank_jobs
from app.models.job_posting import IngestionRun, JobPosting
from app.models.user import User
from app.sources.job_apis import AdzunaSource, JoobleSource

logger = logging.getLogger(__name__)

router = APIRouter()

ALLOWED_COUNTRIES = set(SUPPORTED_COUNTRIES)
MAX_SKILLS = 50
MIN_STRONG_MATCHES = 10
TOP_UP_COUNTRIES = 3
TOP_UP_COOLDOWN_SECONDS = 6 * 3600

_top_up_lock = threading.Lock()
_recent_top_ups: dict[tuple[str, str], float] = {}


class JobSearchRequest(BaseModel):
    cv_text: str = ""
    skills: Optional[List[str]] = None
    location: Optional[str] = None 
    seniority: Optional[str] = "All"
    country: Optional[str] = "pl"
    query: Optional[str] = "Software Engineer"
    remote_only: bool = False
    limit: int = Field(default=30, ge=1, le=100)


def _parse_countries(value: Optional[str]) -> list[str]:
    countries = list(dict.fromkeys(c.strip().lower() for c in (value or "").split(",") if c.strip())) or ["pl"]

    invalid = set(countries) - ALLOWED_COUNTRIES
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported countries: {', '.join(sorted(invalid))}"
        )
    return countries


def _top_up_sources(query: str, countries: list[str]) -> list:
    if not (AdzunaSource.is_configured() or JoobleSource.is_configured()):
        return []

    now = time.time()
    due = []
    with _top_up_lock:
        for key in [k for k, at in _recent_top_ups.items() if now - at > TOP_UP_COOLDOWN_SECONDS]:
            del _recent_top_ups[key]
        for country in countries[:TOP_UP_COUNTRIES]:
            key = (query.lower(), country)
            if key not in _recent_top_ups:
                _recent_top_ups[key] = now
                due.append(country)

    sources = []
    for country in due:
        if AdzunaSource.is_configured():
            sources.append(AdzunaSource(country, pages=1, category=None, what=query))
        if JoobleSource.is_configured():
            sources.append(JoobleSource(query, COUNTRY_NAMES[country], country))
    return sources


@router.post("/recommend")
@limiter.limit("20/minute")
def recommend_jobs(
    request: Request,
    payload: JobSearchRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_jobs_db),
    current_user: User = Depends(get_current_user)
):
    countries = _parse_countries(payload.country)
    query = (payload.query or "").strip()[:200]
    skills = list(dict.fromkeys(s.strip() for s in payload.skills or [] if s and s.strip()))[:MAX_SKILLS]

    result = rank_jobs(
        db,
        query=query,
        skills=skills,
        countries=countries,
        seniority=payload.seniority,
        remote_only=payload.remote_only,
        limit=payload.limit,
    )

    messages = []
    if result.pool_size == 0 and db.query(JobPosting.id).first() is None:
        messages.append("The job index is still being built. Please try again in a few minutes.")
    elif not result.jobs:
        messages.append("No jobs matched this search. Try a broader title, more countries, or 'All Levels'.")

    if query and result.strong_title_matches < MIN_STRONG_MATCHES:
        top_up = _top_up_sources(query, countries)
        if top_up:
            background_tasks.add_task(ingest_now, top_up)
            messages.append(
                f"Looking for more \"{query}\" jobs from live job search APIs. "
                "Search again in a minute or two to see them."
            )

    if skills and not result.used_skills:
        messages.append("Skill matching is unavailable right now, so jobs are ranked by title and description only.")

    response = {
        "jobs": result.jobs,
        "stats": {
            "pool_size": result.pool_size,
            "candidates": result.candidates,
            "semantic": result.used_semantic,
            "skills": result.used_skills,
        },
    }
    if messages:
        response["message"] = " ".join(messages)
    return response


@router.get("/index-status")
def index_status(db: Session = Depends(get_jobs_db), current_user: User = Depends(get_current_user)):
    by_source = dict(db.query(JobPosting.source, func.count(JobPosting.id)).group_by(JobPosting.source).all())
    last_run = (
        db.query(IngestionRun)
        .filter(IngestionRun.finished_at.isnot(None))
        .order_by(IngestionRun.finished_at.desc())
        .first()
    )
    running = db.query(IngestionRun.id).filter(IngestionRun.status == "running").first() is not None
    return {
        "total_jobs": sum(by_source.values()),
        "by_source": by_source,
        "with_skills": db.query(JobPosting.id).filter(JobPosting.skills.isnot(None)).count(),
        "with_embeddings": db.query(JobPosting.id).filter(JobPosting.embedding.isnot(None)).count(),
        "ingestion_running": running,
        "last_run": {
            "finished_at": as_utc(last_run.finished_at).isoformat(),
            "status": last_run.status,
            "summary": json.loads(last_run.stats or "{}").get("enrichment"),
        } if last_run else None,
    }
