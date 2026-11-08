import shutil
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

BASE_DIR = Path(__file__).resolve().parents[2]


def _prepare_sqlite_database(database_url: str) -> None:
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite":
        return

    database_path = url.database
    if not database_path or database_path == ":memory:":
        return

    resolved_path = Path(database_path)
    if not resolved_path.is_absolute():
        resolved_path = (BASE_DIR / resolved_path).resolve()

    resolved_path.parent.mkdir(parents=True, exist_ok=True)

    legacy_database_path = (BASE_DIR / "job_recommender.db").resolve()
    if resolved_path != legacy_database_path and not resolved_path.exists() and legacy_database_path.exists():
        shutil.copy2(legacy_database_path, resolved_path)


def _run_startup_migrations(engine) -> None:
    inspector = inspect(engine)

    if "job_applications" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("job_applications")}
    if "notes" in columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE job_applications ADD COLUMN notes TEXT"))


_prepare_sqlite_database(settings.DATABASE_URL)

engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)

_run_startup_migrations(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _resolve_sqlite_url(database_url: str) -> str:
    """Anchor relative SQLite paths to backend/, so the server and the collector CLI
    use the same file whichever directory they're started from."""
    url = make_url(database_url)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        return database_url
    path = Path(url.database)
    if not path.is_absolute():
        path = (BASE_DIR / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return str(url.set(database=str(path)))


_jobs_url = _resolve_sqlite_url(settings.JOBS_DATABASE_URL)
jobs_engine = create_engine(
    _jobs_url,
    connect_args={"check_same_thread": False} if _jobs_url.startswith("sqlite") else {},
    pool_pre_ping=True,
)

JobsSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=jobs_engine)

JobsBase = declarative_base()

def get_jobs_db():
    db = JobsSessionLocal()
    try:
        yield db
    finally:
        db.close()
