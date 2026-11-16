"""Run one ingestion pass: `python -m app.ingestion [--only greenhouse,arbeitnow] [--no-enrich]`.

Use this from a cron job (e.g. a Render Cron Job) when the in-process scheduler is disabled.
"""
import argparse
import json
import logging

from dotenv import load_dotenv

load_dotenv()

from app.core.database import JobsBase, jobs_engine  
from app.ingestion.pipeline import run_ingestion 
from app.models import job_posting  
from app.sources.registry import build_sources 


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect jobs into the job index.")
    parser.add_argument("--only", help="Comma-separated source name prefixes, e.g. 'greenhouse,lever:qonto'")
    parser.add_argument("--no-enrich", action="store_true", help="Skip skill extraction and embeddings")
    parser.add_argument("--no-prune", action="store_true", help="Keep jobs that weren't seen recently")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    JobsBase.metadata.create_all(bind=jobs_engine)

    sources = build_sources()
    if args.only:
        prefixes = tuple(p.strip() for p in args.only.split(",") if p.strip())
        sources = [s for s in sources if s.name.startswith(prefixes)]

    summary = run_ingestion(sources, enrich=not args.no_enrich, prune=not args.no_prune)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
