import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
FIXTURES_DIR = BASE_DIR / "fixtures"

# Ensure runtime directories exist
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

DB_PATH = str(DATA_DIR / "market_intel.db")
SAMPLE_FIXTURE_PATH = str(FIXTURES_DIR / "sample_competitors.json")

# LLM Configurations
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "demo")  # demo | openai | anthropic | gemini
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Scraper Settings
REQUEST_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "15"))
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
