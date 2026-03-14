from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Job recommendation platform"

    DATABASE_URL: str = "sqlite:///./job_recommender.db"

    SECRET_KEY: str = "to be changed"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    RESET_TOKEN_EXPIRE_MINUTES: int = 15

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None

    RESEND_API_KEY: Optional[str] = None
    RESEND_FROM_EMAIL: Optional[str] = None

    FRONTEND_URL: Optional[str] = None
    BACKEND_URL: Optional[str] = None


    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()