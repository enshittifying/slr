"""Configuration management for the SLR system."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration settings for the SLR system."""

    # Google API
    google_sheets_id: str
    google_calendar_id: str
    google_drive_folder_id: str
    google_service_account_file: Optional[str] = None

    # LLM API Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

    # Database Access
    westlaw_api_key: Optional[str] = None
    lexis_api_key: Optional[str] = None
    jstor_api_key: Optional[str] = None

    # Application Configuration
    environment: str = "development"
    log_level: str = "INFO"
    max_concurrent_tasks: int = 5

    # Pipeline Configuration
    sp_machine_output_dir: str = "./sp_machine/output"
    r1_machine_output_dir: str = "./r1_machine/output"
    r2_machine_output_dir: str = "./r2_machine/output"

    # Security
    allowed_domain: str = "stanford.edu"
    session_secret: Optional[str] = None

    # Rate Limiting
    api_rate_limit_per_minute: int = 60
    llm_rate_limit_per_minute: int = 20

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            google_sheets_id=os.getenv("GOOGLE_SHEETS_ID", ""),
            google_calendar_id=os.getenv("GOOGLE_CALENDAR_ID", ""),
            google_drive_folder_id=os.getenv("GOOGLE_DRIVE_FOLDER_ID", ""),
            google_service_account_file=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"),
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            westlaw_api_key=os.getenv("WESTLAW_API_KEY"),
            lexis_api_key=os.getenv("LEXIS_API_KEY"),
            jstor_api_key=os.getenv("JSTOR_API_KEY"),
            environment=os.getenv("ENVIRONMENT", "development"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            max_concurrent_tasks=int(os.getenv("MAX_CONCURRENT_TASKS", "5")),
            sp_machine_output_dir=os.getenv(
                "SP_MACHINE_OUTPUT_DIR", "./sp_machine/output"
            ),
            r1_machine_output_dir=os.getenv(
                "R1_MACHINE_OUTPUT_DIR", "./r1_machine/output"
            ),
            r2_machine_output_dir=os.getenv(
                "R2_MACHINE_OUTPUT_DIR", "./r2_machine/output"
            ),
            allowed_domain=os.getenv("ALLOWED_DOMAIN", "stanford.edu"),
            session_secret=os.getenv("SESSION_SECRET"),
            api_rate_limit_per_minute=int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60")),
            llm_rate_limit_per_minute=int(os.getenv("LLM_RATE_LIMIT_PER_MINUTE", "20")),
        )

    def validate(self) -> None:
        """Validate required configuration values."""
        required_fields = ["google_sheets_id", "google_calendar_id", "google_drive_folder_id"]
        missing = [field for field in required_fields if not getattr(self, field)]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

    def create_output_directories(self) -> None:
        """Create output directories if they don't exist."""
        for dir_path in [
            self.sp_machine_output_dir,
            self.r1_machine_output_dir,
            self.r2_machine_output_dir,
        ]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)


def load_config(env_file: Optional[str] = None) -> Config:
    """
    Load configuration from environment variables.

    Args:
        env_file: Optional path to .env file

    Returns:
        Config object with loaded settings
    """
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    config = Config.from_env()
    config.validate()
    config.create_output_directories()

    return config
