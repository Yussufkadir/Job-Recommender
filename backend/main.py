from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.core.database import engine, Base
from app.models import user, job_application
import os
from app.routers import auth, cv_tailor, jobs, analytics, applications
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

load_dotenv()

Base.metadata.create_all(bind=engine)

from app.models.user import PasswordResetToken
from app.models.user import User

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title = "Job Recommendation Platform",
    description = "Backend part of the job recommendation system",
    version = "0.1.0",
    lifespan=lifespan
)

from app.routers.auth import limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

frontend_url = os.getenv(
    "FRONTEND_URL",
    "https://job-recommender-phi.vercel.app"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        frontend_url
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"]
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(cv_tailor.router, prefix="/api", tags=["CV Tailoring"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(analytics.router, prefix="/graph", tags=["Knowledge Graph"])
app.include_router(applications.router, prefix="/api/applications", tags=["Application"])

@app.get("/")
async def root():
    return {"message": "Job Recommendation Platform"}