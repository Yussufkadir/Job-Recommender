from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Job recommendation platform"

    DATABASE_URL: str = "sqlite:///./job_recommender.db"

    SECRET_KEY: str = "to be changed"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class config:
        env_file = ".env"

settings = Settings()