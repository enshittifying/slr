"""
Configuration module for R1 Machine citation validator.

This module provides centralized configuration management for the R1 Machine,
including paths, validation thresholds, API settings, and performance parameters.
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class R1Config:
    """Configuration settings for R1 Machine citation validator."""

    # ========== Paths ==========
    # Word document to validate
    word_doc_path: Path

    # Output directory for reports
    output_dir: Path

    # Rules directory (contains Bluebook JSON files)
    rules_dir: Path

    # Log directory
    log_dir: Path

    # ========== Validation Thresholds ==========
    # Confidence threshold to skip rule validation (Stage 1 -> Output)
    regex_confidence_threshold: float = 0.9

    # Confidence threshold to skip GPT validation (Stage 2 -> Output)
    rule_confidence_threshold: float = 0.8

    # Minimum confidence to auto-accept GPT results
    gpt_confidence_threshold: float = 0.6

    # ========== Performance Settings ==========
    # Enable parallel processing
    enable_parallel: bool = True

    # Maximum number of parallel workers
    max_workers: int = 5

    # Enable result caching
    enable_caching: bool = True

    # Enable batch GPT processing (multiple citations per API call)
    enable_batch_gpt: bool = False

    # Batch size for GPT calls
    gpt_batch_size: int = 5

    # ========== GPT Settings ==========
    # OpenAI API key
    openai_api_key: Optional[str] = None

    # GPT model to use
    gpt_model: str = "gpt-4o"

    # Temperature for GPT responses (lower = more deterministic)
    gpt_temperature: float = 0.1

    # Max tokens for GPT response
    gpt_max_tokens: int = 1000

    # Max retries for failed API calls
    gpt_max_retries: int = 3

    # Base retry delay in seconds (exponential backoff)
    gpt_retry_delay: float = 1.0

    # ========== Output Settings ==========
    # Output formats to generate
    output_formats: list = None  # Default: ["json", "html", "excel"]

    # Include detailed rule references in reports
    include_rule_references: bool = True

    # Include GPT explanations in reports
    include_gpt_explanations: bool = True

    # ========== Logging Settings ==========
    # Log level (DEBUG, INFO, WARNING, ERROR)
    log_level: str = "INFO"

    # Enable performance profiling
    enable_profiling: bool = False

    # ========== Processing Options ==========
    # Specific footnote numbers to process (None = all)
    target_footnotes: Optional[list] = None

    # Skip specific validation stages
    skip_regex: bool = False
    skip_rules: bool = False
    skip_gpt: bool = False

    # ========== Advanced Options ==========
    # Minimum citation length to validate (characters)
    min_citation_length: int = 10

    # Maximum citation length to validate (characters)
    max_citation_length: int = 2000

    # Enable strict mode (fail on warnings)
    strict_mode: bool = False

    def __post_init__(self):
        """Post-initialization processing."""
        # Set default output formats
        if self.output_formats is None:
            self.output_formats = ["json", "html", "excel"]

        # Create directories if they don't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Load OpenAI API key from environment if not provided
        if self.openai_api_key is None:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Validate paths
        if not self.rules_dir.exists():
            raise ValueError(f"Rules directory does not exist: {self.rules_dir}")

        # Validate thresholds
        if not 0.0 <= self.regex_confidence_threshold <= 1.0:
            raise ValueError("regex_confidence_threshold must be between 0.0 and 1.0")
        if not 0.0 <= self.rule_confidence_threshold <= 1.0:
            raise ValueError("rule_confidence_threshold must be between 0.0 and 1.0")
        if not 0.0 <= self.gpt_confidence_threshold <= 1.0:
            raise ValueError("gpt_confidence_threshold must be between 0.0 and 1.0")


# Default configuration factory
def create_default_config(
    word_doc_path: str,
    output_dir: Optional[str] = None,
    rules_dir: Optional[str] = None,
    **kwargs
) -> R1Config:
    """
    Create a default R1Config instance.

    Args:
        word_doc_path: Path to Word document to validate
        output_dir: Output directory (default: ./r1_output)
        rules_dir: Rules directory (default: /home/user/slr/SLRinator)
        **kwargs: Additional configuration overrides

    Returns:
        R1Config instance with default settings

    Example:
        >>> config = create_default_config(
        ...     word_doc_path="/path/to/document.docx",
        ...     max_workers=10,
        ...     enable_parallel=True
        ... )
    """
    # Set defaults
    if output_dir is None:
        output_dir = "./r1_output"
    if rules_dir is None:
        rules_dir = "/home/user/slr/SLRinator"

    # Create config
    config = R1Config(
        word_doc_path=Path(word_doc_path),
        output_dir=Path(output_dir),
        rules_dir=Path(rules_dir),
        log_dir=Path(output_dir) / "logs",
        **kwargs
    )

    return config


# Environment-based configuration
def load_config_from_env() -> R1Config:
    """
    Load configuration from environment variables.

    Environment variables:
        R1_WORD_DOC_PATH: Path to Word document
        R1_OUTPUT_DIR: Output directory
        R1_RULES_DIR: Rules directory
        R1_MAX_WORKERS: Number of parallel workers
        R1_ENABLE_PARALLEL: Enable parallel processing (true/false)
        OPENAI_API_KEY: OpenAI API key
        R1_GPT_MODEL: GPT model name
        R1_LOG_LEVEL: Logging level

    Returns:
        R1Config instance loaded from environment

    Raises:
        ValueError: If required environment variables are missing
    """
    word_doc_path = os.getenv("R1_WORD_DOC_PATH")
    if not word_doc_path:
        raise ValueError("R1_WORD_DOC_PATH environment variable is required")

    config = R1Config(
        word_doc_path=Path(word_doc_path),
        output_dir=Path(os.getenv("R1_OUTPUT_DIR", "./r1_output")),
        rules_dir=Path(os.getenv("R1_RULES_DIR", "/home/user/slr/SLRinator")),
        log_dir=Path(os.getenv("R1_LOG_DIR", "./r1_output/logs")),
        max_workers=int(os.getenv("R1_MAX_WORKERS", "5")),
        enable_parallel=os.getenv("R1_ENABLE_PARALLEL", "true").lower() == "true",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        gpt_model=os.getenv("R1_GPT_MODEL", "gpt-4o"),
        log_level=os.getenv("R1_LOG_LEVEL", "INFO"),
    )

    return config


# Configuration validation
def validate_config(config: R1Config) -> tuple[bool, list[str]]:
    """
    Validate a configuration instance.

    Args:
        config: Configuration to validate

    Returns:
        Tuple of (is_valid, error_messages)

    Example:
        >>> config = create_default_config("/path/to/doc.docx")
        >>> is_valid, errors = validate_config(config)
        >>> if not is_valid:
        ...     print("Config errors:", errors)
    """
    errors = []

    # Check paths
    if not config.word_doc_path.exists():
        errors.append(f"Word document does not exist: {config.word_doc_path}")

    if not config.rules_dir.exists():
        errors.append(f"Rules directory does not exist: {config.rules_dir}")

    # Check API key if GPT is enabled
    if not config.skip_gpt and not config.openai_api_key:
        errors.append("OpenAI API key is required for GPT validation")

    # Check thresholds
    if config.regex_confidence_threshold < config.rule_confidence_threshold:
        errors.append("regex_confidence_threshold should be >= rule_confidence_threshold")

    if config.rule_confidence_threshold < config.gpt_confidence_threshold:
        errors.append("rule_confidence_threshold should be >= gpt_confidence_threshold")

    # Check performance settings
    if config.max_workers < 1:
        errors.append("max_workers must be >= 1")

    if config.max_workers > 20:
        errors.append("max_workers > 20 may cause performance issues")

    return (len(errors) == 0, errors)


if __name__ == "__main__":
    # Example usage
    print("Creating default configuration...")
    config = create_default_config(
        word_doc_path="/home/user/slr/test_document.docx",
        max_workers=10
    )

    print(f"Word doc: {config.word_doc_path}")
    print(f"Output dir: {config.output_dir}")
    print(f"Rules dir: {config.rules_dir}")
    print(f"Max workers: {config.max_workers}")
    print(f"Regex threshold: {config.regex_confidence_threshold}")
    print(f"Rule threshold: {config.rule_confidence_threshold}")

    # Validate
    is_valid, errors = validate_config(config)
    if is_valid:
        print("\nConfiguration is valid!")
    else:
        print("\nConfiguration errors:")
        for error in errors:
            print(f"  - {error}")
