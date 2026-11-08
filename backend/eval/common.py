"""Shared setup for the ranking evaluation: snapshot database, variants, judgments file."""
import csv
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
from dotenv import load_dotenv  

load_dotenv(BACKEND_DIR / ".env") 
os.environ.setdefault("SECRET_KEY", "offline-evaluation-only-not-a-real-secret-key")

from sqlalchemy import create_engine, func  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.ingestion.pipeline import as_utc  # noqa: E402
from app.matching.index import JobIndex  # noqa: E402
from app.matching.ranker import WEIGHTS, rank_jobs  # noqa: E402
from app.models.job_posting import JobPosting  # noqa: E402
from app.services.recommender_client import RecommenderClient  # noqa: E402

EVAL_DIR = Path(__file__).resolve().parent
SNAPSHOT_PATH = Path(os.getenv("EVAL_SNAPSHOT", EVAL_DIR / "snapshots" / "jobs.db"))
QUERIES_PATH = EVAL_DIR / "queries.json"
JUDGMENTS_PATH = EVAL_DIR / "judgments.csv"
RESULTS_DIR = EVAL_DIR / "results"
K = 10

VARIANTS: dict[str, dict[str, float]] = {
    "title_only": {"title": 1.0},
    "keywords_only": {"keywords": 1.0},
    "skills_only": {"skills": 1.0},
    "semantic_only": {"semantic": 1.0},
    "title+keywords": {"title": WEIGHTS["title"], "keywords": WEIGHTS["keywords"]},
    "hybrid_no_semantic": {name: w for name, w in WEIGHTS.items() if name != "semantic"},
    "hybrid": dict(WEIGHTS),
}

JUDGMENT_FIELDS = ["query_id", "job_key", "relevance", "title", "company", "location", "link"]


@dataclass
class Query:
    id: str
    query: str
    skills: list[str]
    countries: list[str]
    seniority: str = "All"


@dataclass
class VariantRun:
    job_keys: list[str]
    jobs: list[dict]
    available: bool  


def load_queries() -> list[Query]:
    return [Query(**item) for item in json.loads(QUERIES_PATH.read_text())]


def open_snapshot(path: Path = SNAPSHOT_PATH) -> Session:
    if not path.exists():
        sys.exit(f"No snapshot at {path}. Create one first: python -m eval.snapshot")
    engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})
    return sessionmaker(bind=engine)()


def snapshot_time(db: Session) -> float:
    """The moment the snapshot was taken, used as 'now' so job ages never drift."""
    latest = db.query(func.max(JobPosting.last_seen_at)).scalar()
    return as_utc(latest).timestamp()


def job_key(job: JobPosting) -> str:
    """Stable across databases, unlike row ids: source plus the source's own id."""
    return f"{job.source}:{job.external_id}"


class Runner:
    """Runs golden queries against the snapshot with any variant's weights."""

    def __init__(self, db: Session, client: Optional[RecommenderClient] = None):
        self.db = db
        self.client = client or RecommenderClient()
        self.index = JobIndex()
        self.now = snapshot_time(db)
        self._keys: dict[int, str] = {}

    def _key_for(self, job_id: int) -> str:
        if job_id not in self._keys:
            job = self.db.get(JobPosting, job_id)
            self._keys[job_id] = job_key(job)
        return self._keys[job_id]

    def run(self, query: Query, variant: str, limit: int = K) -> VariantRun:
        weights = VARIANTS[variant]
        result = rank_jobs(
            self.db,
            query=query.query,
            skills=query.skills,
            countries=query.countries,
            seniority=query.seniority,
            limit=limit,
            client=self.client,
            weights=weights,
            index=self.index,
            now=self.now,
        )
        available = (
            ("skills" not in weights or result.used_skills)
            and ("semantic" not in weights or result.used_semantic)
        )
        return VariantRun([self._key_for(job["id"]) for job in result.jobs], result.jobs, available)


def read_judgment_rows() -> list[dict]:
    if not JUDGMENTS_PATH.exists():
        return []
    with JUDGMENTS_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_judgment_rows(rows: list[dict]) -> None:
    rows = sorted(rows, key=lambda row: (row["query_id"], row["job_key"]))
    tmp = JUDGMENTS_PATH.with_suffix(".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=JUDGMENT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    tmp.replace(JUDGMENTS_PATH)  


def grades_by_query(rows: list[dict]) -> dict[str, dict[str, int]]:
    """Only rows with a 0/1/2 relevance count as judged."""
    grades: dict[str, dict[str, int]] = {}
    for row in rows:
        value = (row.get("relevance") or "").strip()
        if value in {"0", "1", "2"}:
            grades.setdefault(row["query_id"], {})[row["job_key"]] = int(value)
    return grades
