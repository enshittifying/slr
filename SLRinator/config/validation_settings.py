"""
R1 Validation Configuration Settings
"""
import os
from pathlib import Path

# Base paths
SLRINATOR_ROOT = Path(__file__).parent.parent
CONFIG_DIR = SLRINATOR_ROOT / "config"
PROMPTS_DIR = SLRINATOR_ROOT / "prompts" / "r1"
OUTPUT_DIR = SLRINATOR_ROOT / "output"

# Rules
BLUEBOOK_JSON_PATH = CONFIG_DIR / "rules" / "Bluebook.json"

# API Configuration
API_KEYS_PATH = CONFIG_DIR / "api_keys.json"
VECTOR_STORE_CACHE = CONFIG_DIR / "vector_store_cache.json"

# Load API key from config
try:
    import json
    with open(API_KEYS_PATH, 'r') as f:
        api_config = json.load(f)
        OPENAI_API_KEY = api_config.get('openai', {}).get('api_key', '')
except (FileNotFoundError, json.JSONDecodeError):
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# GPT Configuration for R1 Validation
GPT_MODEL = "gpt-4o-mini"  # Cost-effective for validation
GPT_TEMPERATURE = 0.1      # Low temperature for consistency
GPT_MAX_TOKENS = 4000

# Validation Options
ENABLE_CITATION_VALIDATION = True
ENABLE_QUOTE_VERIFICATION = True
ENABLE_SUPPORT_CHECKING = False  # Optional, requires proposition extraction
VALIDATION_MODE = "strict"  # "strict" or "lenient"
USE_VECTOR_SEARCH = True    # Use vector assistant with File Search
DETERMINISTIC_CHECKS_ONLY = False

# Confidence Thresholds
CONFIDENCE_THRESHOLD = 0.85
AUTO_APPROVE_HIGH_CONFIDENCE = True  # Auto-approve if > 0.95 confidence

# Processing
ENABLE_PARALLEL_PROCESSING = False
MAX_RETRIES = 5

# Logging
LOG_LEVEL = "INFO"
SAVE_DETAILED_LOGS = True

# Create directories
for dir_path in [CONFIG_DIR / "rules", PROMPTS_DIR, OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
