import hashlib

import numpy as np
import pytest

from app.core.database import JobsBase, JobsSessionLocal, jobs_engine
from app.ingestion.pipeline import enrich_pending, upsert_jobs
from app.matching.index import job_index
from app.matching.ranker import rank_jobs
from app.models import job_posting  # noqa: F401
from app.models.job_posting import JobPosting
from app.sources.base import RawJob

KNOWN_SKILLS = {"python", "django", "react", "typescript", "sql", "kubernetes", "figma"}


class FakeRecommender:
    """Stands in for the recommender service: keyword skills, hashed bag-of-words embeddings."""

    def extract_skills_batch(self, texts):
        return [[s for s in KNOWN_SKILLS if s in text.lower()] for text in texts]

    def embed(self, texts):
        vectors = []
        for text in texts:
            vector = np.zeros(64, dtype=np.float32)
            for word in text.lower().split():
                vector[int(hashlib.md5(word.encode()).hexdigest(), 16) % 64] += 1
            vectors.append((vector / (np.linalg.norm(vector) or 1)).tolist())
        return vectors

    def score_batch(self, user_skills, jobs_skills):
        user = {s.lower() for s in user_skills}
        results = []
        for skills in jobs_skills:
            matched = [s for s in skills if s in user]
            results.append({
                "score": 100 * len(matched) / len(skills) if skills else 0,
                "matched": matched,
                "missing": [s for s in skills if s not in user],
            })
        return results


def raw(external_id, title, location, description, source="greenhouse", company="Acme", **kwargs):
    return RawJob(source=source, external_id=external_id, title=title, company=company,
                  description=description, url=f"https://jobs.example/{external_id}", location=location, **kwargs)


@pytest.fixture()
def db():
    JobsBase.metadata.create_all(bind=jobs_engine)
    session = JobsSessionLocal()
    yield session
    session.query(JobPosting).delete()
    session.commit()
    session.close()
    job_index.invalidate()


def test_upsert_maps_countries_dedupes_and_tracks_changes(db):
    jobs = [
        raw("1", "Backend Engineer", "Berlin, Germany", "Python and Django services."),
        raw("2", "Backend Engineer", "Singapore", "Python services."),  
        raw("3", "Designer", "Remote", "Figma."),  
        raw("4", "Data Analyst", "Remote", "SQL dashboards.", source="arbeitnow", default_country="de"),
    ]
    stats = upsert_jobs(db, jobs)
    assert stats["inserted"] == 2 and stats["skipped"] == 2

    stats = upsert_jobs(db, [raw("x", "Backend Engineer (m/w/d)", "Berlin", "Same job.", source="adzuna", company="Acme GmbH")])
    assert stats["duplicates"] == 1

    enrich_pending(db, client=FakeRecommender())
    assert upsert_jobs(db, [jobs[0]])["unchanged"] == 1
    changed = raw("1", "Backend Engineer", "Berlin, Germany", "Python, Django and Kubernetes.")
    assert upsert_jobs(db, [changed])["updated"] == 1
    row = db.query(JobPosting).filter_by(external_id="1").one()
    assert row.skills is None and row.embedding is None


def test_ranking_prefers_title_and_skills_and_applies_filters(db):
    upsert_jobs(db, [
        raw("a", "Senior Python Engineer", "Berlin, Germany", "Build APIs with Python, Django and SQL."),
        raw("b", "Python Engineer", "Warsaw, Poland", "Python, Django and SQL backend work."),
        raw("c", "Frontend Engineer", "Berlin, Germany", "React and TypeScript."),
        raw("d", "Account Executive", "Berlin, Germany", "Sell our product."),
        raw("e", "Python Developer", "Remote, Europe", "Python and SQL.", remote=True),
    ])
    enrich_pending(db, client=FakeRecommender())
    job_index.invalidate()

    result = rank_jobs(db, "Python Engineer", ["Python", "Django", "SQL"], ["de"], client=FakeRecommender())
    titles = [job["title"] for job in result.jobs]
    assert "Warsaw" not in " ".join(job["location"] for job in result.jobs) 
    assert titles[0] in {"Senior Python Engineer", "Python Developer"}
    assert "Account Executive" not in titles[:2]
    top = result.jobs[0]
    assert top["matched_skills"] and top["score_breakdown"]["skills"] > 0
    assert result.used_semantic and result.used_skills

    seniors = rank_jobs(db, "Python Engineer", [], ["de"], seniority="Senior", client=FakeRecommender())
    assert [job["title"] for job in seniors.jobs] == ["Senior Python Engineer"]

    remote = rank_jobs(db, "Python", [], ["de", "pl"], remote_only=True, client=FakeRecommender())
    assert [job["title"] for job in remote.jobs] == ["Python Developer"]


def test_same_job_in_several_cities_is_shown_once(db):
    upsert_jobs(db, [
        raw("berlin", "Graduate Java Developer", "Berlin, Germany", "Java and Spring.", company="Fioneer"),
        raw("munich", "Graduate Java Developer", "Munich, Germany", "Java and Spring.", company="Fioneer"),
        raw("paris", "Graduate Java Developer", "Paris, France", "Java and Spring.", company="Fioneer"),
        raw("other", "Java Developer", "Berlin, Germany", "Java.", company="Acme"),
    ])
    job_index.invalidate()

    result = rank_jobs(db, "Java Developer", [], ["de"], client=FakeRecommender())
    fioneer = [job for job in result.jobs if job["company"] == "Fioneer"]
    assert len(fioneer) == 1
    assert fioneer[0]["location"] in {"Berlin, Germany", "Munich, Germany"}
    assert fioneer[0]["other_locations"] == [
        {"Berlin, Germany", "Munich, Germany"}.difference({fioneer[0]["location"]}).pop()
    ]
    assert any(job["company"] == "Acme" for job in result.jobs)


def test_failed_translation_is_retried_on_next_run(db, monkeypatch):
    monkeypatch.setattr("app.ingestion.pipeline.TRANSLATE", True)
    german = raw("g", "Softwareentwickler", "Berlin",
                 "Wir suchen einen Entwickler für unser Team. Du arbeitest mit Python und bist für die "
                 "Entwicklung der Systeme und die Wartung der Plattform verantwortlich.", source="arbeitnow")

    class RateLimited:
        def job_to_english(self, title, description):
            return None

    class Working:
        def job_to_english(self, title, description):
            return "Software Engineer", "We are looking for an engineer."

    upsert_jobs(db, [german], translator=RateLimited())
    row = db.query(JobPosting).filter_by(external_id="g").one()
    assert not row.translated

    assert upsert_jobs(db, [german], translator=Working())["updated"] == 1
    db.refresh(row)
    assert row.translated and row.title == "Software Engineer"
    assert upsert_jobs(db, [german], translator=Working())["unchanged"] == 1


def test_run_lock_released_when_heartbeat_is_stale(db):
    from datetime import timedelta
    from app.ingestion.pipeline import _start_run, utcnow
    from app.models.job_posting import IngestionRun

    first = _start_run(db)
    assert first is not None and _start_run(db) is None  

    first.heartbeat_at = utcnow() - timedelta(minutes=30)
    db.commit()
    second = _start_run(db)
    assert second is not None
    db.refresh(first)
    assert first.status == "abandoned"
    db.query(IngestionRun).delete()
    db.commit()


def test_source_errors_never_contain_api_keys():
    import requests
    from app.ingestion.pipeline import _safe_error

    response = requests.Response()
    response.status_code, response.reason = 503, "Service Unavailable"
    http_error = requests.HTTPError("503 for url: https://api.adzuna.com/x?app_key=SECRET", response=response)
    connection_error = requests.ConnectionError(
        "HTTPSConnectionPool(host='jooble.org', port=443): Max retries exceeded with url: /api/SECRET (Caused by x)"
    )
    for error in (http_error, connection_error, ValueError("bad https://jooble.org/api/SECRET?x=1")):
        assert "SECRET" not in _safe_error(error)


def test_ranking_degrades_without_recommender(db):
    class Down:
        def embed(self, texts):
            return None

        def score_batch(self, user_skills, jobs_skills):
            return None

    upsert_jobs(db, [raw("a", "Python Engineer", "Berlin", "Python.")])
    job_index.invalidate()
    result = rank_jobs(db, "Python Engineer", ["Python"], ["de"], client=Down())
    assert [job["title"] for job in result.jobs] == ["Python Engineer"]
    assert not result.used_skills and not result.used_semantic
