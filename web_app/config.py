"""Configuration settings for the Flask application."""

import os
from datetime import timedelta


class Config:
    """Base configuration."""

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        os.getenv("POSTGRES_URL", "postgresql://localhost:5432/slr_db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Session
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False") == "True"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(
        seconds=int(os.getenv("PERMANENT_SESSION_LIFETIME", "3600"))
    )

    # Google OAuth
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5000/auth/callback")
    GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

    # Google APIs
    GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")
    GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
    GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    # LLM APIs
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

    # Application
    ALLOWED_DOMAIN = os.getenv("ALLOWED_DOMAIN", "stanford.edu")
    MAX_CONCURRENT_TASKS = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Pipeline
    SP_MACHINE_OUTPUT_DIR = os.getenv("SP_MACHINE_OUTPUT_DIR", "./sp_machine/output")
    R1_MACHINE_OUTPUT_DIR = os.getenv("R1_MACHINE_OUTPUT_DIR", "./r1_machine/output")
    R2_MACHINE_OUTPUT_DIR = os.getenv("R2_MACHINE_OUTPUT_DIR", "./r2_machine/output")

    # Rate Limiting
    API_RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60"))
    LLM_RATE_LIMIT_PER_MINUTE = int(os.getenv("LLM_RATE_LIMIT_PER_MINUTE", "20"))


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    SQLALCHEMY_ECHO = False
    SESSION_COOKIE_SECURE = True

    # Override database URL for Vercel Postgres if needed
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        # Vercel uses POSTGRES_URL, standard is DATABASE_URL
        url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
        if url and url.startswith("postgres://"):
            # SQLAlchemy requires postgresql:// not postgres://
            url = url.replace("postgres://", "postgresql://", 1)
        return url


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "postgresql://localhost:5432/slr_test_db"
    WTF_CSRF_ENABLED = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config(config_name="development"):
    """Get configuration object by name."""
    return config_map.get(config_name, DevelopmentConfig)
