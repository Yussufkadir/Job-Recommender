from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Job recommendation platform"

    DATABASE_URL: str = "sqlite:///./job_recommender.db"

    SECRET_KEY: str
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

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        normalized = value.strip()
        blocked_values = {
            "to be changed",
            "change-me",
            "changeme",
            "default",
            "secret",
        }
        if normalized.casefold() in blocked_values:
            raise ValueError("SECRET_KEY must not use a placeholder value.")
        if len(normalized) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long.")
        return normalized


    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
