from fastapi.testclient import TestClient

import main
from app.core.security import get_current_user
from app.ingestion.normalize import SUPPORTED_COUNTRIES

main.app.dependency_overrides[get_current_user] = lambda: object()
client = TestClient(main.app)


def search(country: str):
    return client.post("/api/jobs/recommend", json={"query": "Software Engineer", "country": country})


def test_search_accepts_every_supported_country_at_once():
    response = search(",".join(SUPPORTED_COUNTRIES))
    assert response.status_code == 200, response.json()


def test_job_tables_live_apart_from_user_data():
    from sqlalchemy import inspect
    from app.core.database import engine, jobs_engine

    user_tables = set(inspect(engine).get_table_names())
    job_tables = set(inspect(jobs_engine).get_table_names())
    assert {"job_postings", "ingestion_runs"} <= job_tables
    assert not {"job_postings", "ingestion_runs"} & user_tables
    assert "users" in user_tables and "users" not in job_tables


def test_search_rejects_unsupported_country():
    response = search("pl,xx")
    assert response.status_code == 400
    assert "xx" in response.json()["detail"]
