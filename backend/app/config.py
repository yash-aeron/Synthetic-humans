from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Synthetic Humans"
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./synthetic_humans.db"
    POSTGRES_DB: str = "synthetic_humans"
    POSTGRES_USER: str = "synthetic"
    POSTGRES_PASSWORD: str = "synthetic"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # LLM Providers
    DEFAULT_LLM_PROVIDER: str = "mock"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Browser & Simulation
    HEADLESS_BROWSER: bool = True
    MAX_CONCURRENT_BROWSERS: int = 5
    DEFAULT_MAX_STEPS: int = 30
    DEFAULT_MAX_DURATION_SECONDS: int = 180
    RECORD_SCREENSHOTS: bool = True
    STORAGE_DIR: str = "./data/screenshots"

    # Allowed Origins security whitelist (comma-separated or json)
    ENFORCE_ALLOWED_ORIGINS: bool = True

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()

# Ensure screenshot and data directory exists
Path(settings.STORAGE_DIR).mkdir(parents=True, exist_ok=True)
