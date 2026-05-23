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
        logger.warning(f"Searching country: {country_code}")
        aggregator = JobAggregator()
        try:
            jobs_df = aggregator.get_all_jobs(
                query=payload.query,
                user_skills=payload.skills,
                seniority=payload.seniority,
                country=country_code
            )
            logger.warning(f"Country {country_code}: {len(jobs_df)} jobs found")
            if not jobs_df.empty:
                all_jobs_dfs.append(jobs_df)
        except Exception as e:
            logger.error(f"Search failed for {country_code}: {e}")
            continue

    logger.warning(f"Total DataFrames collected: {len(all_jobs_dfs)}")

    if not all_jobs_dfs:
        logger.warning("No jobs found at all")
        return {"message": "No jobs found", "jobs": []}

    logger.warning("Concatenating DataFrames...")
    combined_df = pd.concat(all_jobs_dfs, ignore_index=True)
    logger.warning(f"Combined shape: {combined_df.shape}")
    combined_df = combined_df.drop_duplicates(subset=["link"])

    jobs_list = combined_df.to_dict('records')

    logger.warning(f"Jobs from Adzuna: {len(jobs_list)}")
    if jobs_list:
        logger.warning(f"First job: {jobs_list[0].get('title', 'N/A')}")

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

    scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
    return {"jobs": scored_jobs}