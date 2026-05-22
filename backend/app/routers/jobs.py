from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd

from app.routers.auth import limiter
from app.scrapers.job_aggregator import JobAggregator
from app.services.recommender_client import RecommenderClient
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

class JobSearchRequest(BaseModel):
    cv_text: str
    skills: Optional[List[str]] = None
    location: Optional[str] = "Poland"
    seniority: Optional[str] = "All"
    country: Optional[str] = "pl"
    query: Optional[str] = "Software Engineer"

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
            print(f"Search failed for {country_code}: {e}")
            continue

    if not all_jobs_dfs:
        return {"message": "No jobs found", "jobs": []}

    combined_df = pd.concat(all_jobs_dfs, ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=["link"])

    jobs_list = combined_df.to_dict('records')

    rec_client = RecommenderClient()
    scored_jobs = []
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