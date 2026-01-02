from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.scrapers.job_aggregator import JobAggregator
from app.services.recommender_client import RecommenderClient

router = APIRouter()

class JobSearchRequest(BaseModel):
    cv_text: str
    skills: Optional[List[str]] = None
    location: Optional[str] = "Poland"
    seniority: Optional[str] = "All"
    query: Optional[str] = "Software Engineer"

@router.post("/recommend")
async def recommend_jobs(request: JobSearchRequest):

    print(f"Recieved search request for skills {request.skills}")

    query = request.query
    
    aggregator = JobAggregator()
    jobs_df = aggregator.get_all_jobs(
        query=query,
        user_skills=request.skills,
        seniority=request.seniority
        )

    if jobs_df.empty:
        return {"message": "No jobs found", "jobs": []}
    
    rec_client = RecommenderClient()
    scored_jobs = []

    jobs_list = jobs_df.to_dict('records')

    print(f"Scoring {len(jobs_list)} jobs")
    for job in jobs_list:
        score = rec_client.get_score(
            user_skills=request.skills,
            job_description=job.get('description', '')
        )
        if score > 70:
            job['match_score'] = score
            scored_jobs.append(job)

    scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
    
    return {"jobs": scored_jobs}