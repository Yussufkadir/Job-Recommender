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
