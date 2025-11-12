"""Application configuration."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # App
    app_name: str = "Stanford Law Review Citation System"
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Google OAuth
    google_client_id: str = ""

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.1

    # CORS
    allowed_origins: List[str] = ["http://localhost:3000"]

    # Google Cloud
    gcp_project_id: str = ""
    gcp_region: str = "us-west1"
    storage_bucket: str = "slr-pdfs"

    # Pagination
    default_page_size: int = 50
    max_page_size: int = 100

    # Rate limiting
    rate_limit_per_minute: int = 100

    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins as list."""
        if isinstance(self.allowed_origins, str):
            return [origin.strip() for origin in self.allowed_origins.split(",")]
        return self.allowed_origins


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
