"""Freeze the job index for evaluation: `python -m eval.snapshot [--from PATH] [--no-enrich]`.

The live index changes every collection run, which would move the metrics for reasons that
have nothing to do with the ranking code. Evaluation always runs against this frozen copy.
Enrichment fills in skills and embeddings the live index hasn't processed yet, so the
skills and semantic variants are measured on complete data (needs the recommender running).
"""
import argparse
import sqlite3
import sys
import time
from pathlib import Path

from eval.common import SNAPSHOT_PATH, open_snapshot

from app.core.database import jobs_engine  # noqa: E402
from app.ingestion.pipeline import enrich_pending  # noqa: E402
from app.models.job_posting import JobPosting  # noqa: E402

PROGRESS_EVERY_BATCHES = 10


def copy_database(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    with sqlite3.connect(f"file:{source}?mode=ro", uri=True) as src, sqlite3.connect(target) as dst:
        src.backup(dst)


def coverage(db) -> tuple[int, int, int]:
    total = db.query(JobPosting).count()
    skills = db.query(JobPosting).filter(JobPosting.skills.isnot(None)).count()
    embeddings = db.query(JobPosting).filter(JobPosting.embedding.isnot(None)).count()
    return total, skills, embeddings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--from", dest="source", type=Path, default=Path(jobs_engine.url.database),
                        help="jobs database to copy (default: JOBS_DATABASE_URL)")
    parser.add_argument("--no-enrich", action="store_true", help="copy only; skip filling skills/embeddings")
    args = parser.parse_args()

    if not args.source.exists():
        sys.exit(f"Jobs database not found: {args.source}")
    print(f"Copying {args.source} -> {SNAPSHOT_PATH}")
    copy_database(args.source, SNAPSHOT_PATH)

    db = open_snapshot()
    total, skills, embeddings = coverage(db)
    print(f"Snapshot: {total} jobs, {skills} with skills, {embeddings} with embeddings")

    if not args.no_enrich and (skills < total or embeddings < total):
        print("Enriching the remaining jobs (this can take a while on CPU)...")
        started = time.monotonic()
        batches = 0

        def progress():
            nonlocal batches
            batches += 1
            if batches % PROGRESS_EVERY_BATCHES:
                return
            done_total, done_skills, done_embeddings = coverage(db)
            print(f"  {done_skills}/{done_total} skills, {done_embeddings}/{done_total} embeddings "
                  f"({time.monotonic() - started:.0f}s)", flush=True)

        stats = enrich_pending(db, limit=total, on_batch=progress)
        if stats["skills_unavailable"] or stats["embeddings_unavailable"]:
            print("Warning: the recommender couldn't provide",
                  "skills" if stats["skills_unavailable"] else "",
                  "embeddings" if stats["embeddings_unavailable"] else "",
                  "- check RECOMMENDER_URL and that sentence-transformers is installed there.")
        total, skills, embeddings = coverage(db)
        print(f"Snapshot ready: {total} jobs, {skills} with skills, {embeddings} with embeddings")


if __name__ == "__main__":
    main()
