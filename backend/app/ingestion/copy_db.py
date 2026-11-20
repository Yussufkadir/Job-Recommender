"""Copy the job index into another database: `python -m app.ingestion.copy_db [--source URL] [--replace]`.

Used once to move the SQLite job index into Postgres (Neon). Only the jobs tables are copied;
the users database is never opened. The target URL is read from the environment
(COPY_TARGET_DATABASE_URL, e.g. in backend/.env), not from the command line, so it stays out
of shell history.

The default source is the evaluation snapshot: the same jobs as jobs.db, with skills and
embeddings already filled in, so the first collector run only enriches jobs that are new.
"""
import argparse
import os

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import create_engine, func, select, text  # noqa: E402

from app.core.database import JobsBase  # noqa: E402
from app.models import job_posting  # noqa: E402,F401  (registers the jobs tables)

TABLES = ["job_postings", "ingestion_runs"]
BATCH_SIZE = 500


def main() -> None:
    parser = argparse.ArgumentParser(description="Copy the job index into another database.")
    parser.add_argument("--source", default="sqlite:///eval/snapshots/jobs.db", help="database to copy from")
    parser.add_argument("--target-env", default="COPY_TARGET_DATABASE_URL",
                        help="environment variable holding the target database URL")
    parser.add_argument("--replace", action="store_true", help="delete the target's jobs first")
    args = parser.parse_args()

    target_url = os.getenv(args.target_env)
    if not target_url:
        raise SystemExit(f"Set {args.target_env} to the target database URL (in backend/.env or the shell).")
    source = create_engine(args.source)
    target = create_engine(target_url, pool_pre_ping=True)
    tables = [JobsBase.metadata.tables[name] for name in TABLES]

    JobsBase.metadata.create_all(target, tables=tables)
    with target.begin() as connection:
        existing = connection.execute(select(func.count()).select_from(tables[0])).scalar()
        if existing and not args.replace:
            raise SystemExit(f"The target already has {existing} jobs; use --replace to overwrite them.")
        for table in reversed(tables):
            connection.execute(table.delete())

    for table in tables:
        copied = 0
        with source.connect() as reader:
            result = reader.execution_options(stream_results=True).execute(select(table).order_by(table.c.id))
            while rows := result.fetchmany(BATCH_SIZE):
                with target.begin() as writer:
                    writer.execute(table.insert(), [dict(row._mapping) for row in rows])
                copied += len(rows)
                print(f"{table.name}: {copied} rows", end="\r", flush=True)
        print(f"{table.name}: {copied} rows copied")
        if target.dialect.name == "postgresql":
            # Rows keep their ids, so move the id counter past them for new inserts.
            with target.begin() as writer:
                writer.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table.name}), 0) + 1, false)"
                ))


if __name__ == "__main__":
    main()
