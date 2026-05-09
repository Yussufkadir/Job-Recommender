from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import List, Optional

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
    query: Optional[str] = "Software Engineer"

@router.post("/recommend")
@limiter.limit("10/minute")
async def recommend_jobs(
    request: Request,
    payload: JobSearchRequest,
    current_user: User = Depends(get_current_user)
):
    query = payload.query
    
    aggregator = JobAggregator()
    jobs_df = aggregator.get_all_jobs(
        query=query,
        user_skills=payload.skills,
        seniority=payload.seniority
        )

    if jobs_df.empty:
        return {"message": "No jobs found", "jobs": []}
    
    rec_client = RecommenderClient()
    scored_jobs = []

    jobs_list = jobs_df.to_dict('records')

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
