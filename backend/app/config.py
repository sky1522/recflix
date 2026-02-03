"""
RecFlix Configuration Management
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application Settings"""

    # App
    APP_NAME: str = "RecFlix"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://recflix:recflix123@localhost:5432/recflix"

    # Redis - supports both REDIS_URL (Railway) and individual settings
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "recflix123"

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # External APIs
    WEATHER_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # CORS - supports comma-separated string from environment
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Server
    PORT: int = 8000

    # Data Paths
    DATA_RAW_PATH: str = "./data/raw"
    DATA_PROCESSED_PATH: str = "./data/processed"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Parse CORS_ORIGINS from comma-separated string if needed
        cors_env = os.getenv("CORS_ORIGINS")
        if cors_env and isinstance(cors_env, str):
            self.CORS_ORIGINS = [origin.strip() for origin in cors_env.split(",")]

        # Set DEBUG based on environment
        if self.APP_ENV == "production":
            self.DEBUG = False

    @property
    def redis_connection_url(self) -> str:
        """Get Redis connection URL"""
        if self.REDIS_URL:
            return self.REDIS_URL
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.APP_ENV == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
