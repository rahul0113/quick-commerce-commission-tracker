from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/commission_tracker"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Auth (SuperAuth)
    JWT_SECRET: str  # FIX #12: Required — no default, must be set in .env
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # Scraping
    SCRAPE_INTERVAL_HOURS: int = 6
    SCRAPE_MAX_CONCURRENT: int = 2
    HEADLESS_BROWSER: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
