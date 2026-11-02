"""Central configuration read from environment variables (.env at the project root)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


class Config:
    ROOT = ROOT
    ENV = os.getenv("FLASK_ENV", "development")
    PORT = int(os.getenv("FLASK_PORT", "5000"))
    CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "truthlens")

    SEARCH_PROVIDER = os.getenv("SEARCH_PROVIDER", "none").strip().lower()
    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "").strip()
    SERPAPI_KEY = os.getenv("SERPAPI_KEY", "").strip()

    USE_SENTENCE_TRANSFORMERS = _bool("USE_SENTENCE_TRANSFORMERS", False)
    SENTENCE_MODEL = os.getenv("SENTENCE_MODEL", "all-MiniLM-L6-v2")

    URL_FETCH_TIMEOUT = float(os.getenv("URL_FETCH_TIMEOUT", "8"))
    URL_MAX_BYTES = int(os.getenv("URL_MAX_BYTES", "2000000"))

    MIN_ARTICLE_CHARS = 100
    MIN_HEADLINE_CHARS = 10
    MAX_TEXT_CHARS = 50000
    EXCERPT_CHARS = 500

    ML_DIR = ROOT / "ml"
    METRICS_PATH = ROOT / "ml" / "saved_models" / "metrics.json"
    SOURCES_PATH = Path(__file__).resolve().parent / "data" / "sources.json"
