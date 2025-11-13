"""
Configuration settings for R2 pipeline.
"""
import os
from pathlib import Path

# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"

# Input paths - actual file locations
R1_PDF_DIR = Path("/Users/ben/app/slrapp/78 SLR V2 R2 F/78 SLR V2 R1")
SPREADSHEET_PATH = Path("/Users/ben/app/slrapp/78 SLR V2 R2 F/References/V78.4 Bersh Master Sheet.xlsx")
WORD_DOC_PATH = Path("/Users/ben/app/slrapp/78 SLR V2 R2 F/References/Bersh_PreR2.docx")
BLUEBOOK_JSON_PATH = Path("/Users/ben/app/slrapp/Bluebook.json")

# Output paths
R2_PDF_DIR = OUTPUT_DIR / "r2_pdfs"
LOG_DIR = OUTPUT_DIR / "logs"
REPORT_DIR = OUTPUT_DIR / "reports"
VECTOR_STORE_CACHE = PROJECT_ROOT / "config" / "vector_store_cache.json"

# Create directories if they don't exist
for dir_path in [R2_PDF_DIR, LOG_DIR, REPORT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# GPT Configuration
# Load API key from file
API_KEY_PATH = Path("/Users/ben/app/slrapp/openaikey.txt")
try:
    with open(API_KEY_PATH, 'r') as f:
        OPENAI_API_KEY = f.read().strip()
except FileNotFoundError:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Fallback to environment variable

# Use GPT-4o family with Chat Completions by default
GPT_MODEL = "gpt-4o-mini"  # Cost-effective, reliable; vector assistant also uses 4o-mini
GPT_TEMPERATURE = 0.1  # Low temperature for consistency
GPT_MAX_TOKENS = 4000

# Processing options
CONFIDENCE_THRESHOLD = 0.85  # Below this, flag for human review
AUTO_APPROVE_HIGH_CONFIDENCE = True  # Auto-approve if > 0.95 confidence
ENABLE_QUOTE_FUZZY_MATCH = True  # Allow minor whitespace differences
ENABLE_PARALLEL_PROCESSING = False  # Set True if you have API quota

# Logging
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
SAVE_DETAILED_LOGS = True
