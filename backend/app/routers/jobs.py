from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import logging

from app.routers.auth import limiter

logger = logging.getLogger(__name__)
from app.scrapers.job_aggregator import JobAggregator
from app.services.recommender_client import RecommenderClient
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

ALLOWED_COUNTRIES = {"pl", "de", "fr", "gb", "us", "nl", "se", "ca", "it"}
MAX_COUNTRIES_PER_REQUEST = 5

class JobSearchRequest(BaseModel):
    cv_text: str
    skills: Optional[List[str]] = None
    location: Optional[str] = "Poland"
    seniority: Optional[str] = "All"
    country: Optional[str] = "pl"
    query: Optional[str] = "Software Engineer"

@router.get("/test-recommender")
async def test_recommender():
    import httpx
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            "https://syurmen-recommender-service.hf.space/extract",
            json={"text": "Python FastAPI Machine Learning"}
        )
        return {"status": r.status_code, "skills": r.json()}

@router.post("/recommend")
@limiter.limit("10/minute")
async def recommend_jobs(
    request: Request,
    payload: JobSearchRequest,
    current_user: User = Depends(get_current_user)
):
    countries = [c.strip() for c in payload.country.split(",") if c.strip()]
    if not countries:
        countries = ["pl"]

    invalid = set(countries) - ALLOWED_COUNTRIES
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported countries: {', '.join(invalid)}"
        )

    if len(countries) > MAX_COUNTRIES_PER_REQUEST:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_COUNTRIES_PER_REQUEST} countries per request"
        )

    all_jobs_dfs = []
    for country_code in countries:
        aggregator = JobAggregator()
        try:
            jobs_df = aggregator.get_all_jobs(
                query=payload.query,
                user_skills=payload.skills,
                seniority=payload.seniority,
                country=country_code
            )
            if not jobs_df.empty:
                all_jobs_dfs.append(jobs_df)
        except Exception as e:
            logger.warning("Search failed for %s: %s", country_code, e)
            continue

    if not all_jobs_dfs:
        return {"message": "No jobs found", "jobs": []}

    combined_df = pd.concat(all_jobs_dfs, ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=["link"])

    jobs_list = combined_df.to_dict('records')

    rec_client = RecommenderClient()
    scored_jobs = []
    logger.warning(f"Jobs from Adzuna: {len(jobs_list)}")
    logger.warning(f"First job: {jobs_list[0] if jobs_list else 'EMPTY'}")

    rec_client = RecommenderClient()
    scored_jobs = []
    for i, job in enumerate(jobs_list):
        logger.warning(f"Scoring job {i+1}/{len(jobs_list)}: {job.get('title', 'N/A')}")
        try:
            score = rec_client.get_score(
                user_skills=payload.skills,
                job_description=job.get('description', '')
            )
            logger.warning(f"Score for job {i+1}: {score}")
            if score > 70:
                job['match_score'] = score
                scored_jobs.append(job)
        except Exception as e:
            logger.error(f"Scoring failed for job {i+1}: {e}")
    for job in jobs_list:
        score = rec_client.get_score(
            user_skills=payload.skills,
            job_description=job.get('description', '')
        )
        if score > 70:
            job['match_score'] = score
            scored_jobs.append(job)

    scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
    return {"jobs": scored_jobs}