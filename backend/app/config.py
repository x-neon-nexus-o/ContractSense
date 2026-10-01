"""Environment-backed application settings with a zero-config local mode."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent

# Load project-root .env when python-dotenv is installed. Environment variables
# already provided by the process/container take precedence.
try:
    from dotenv import load_dotenv

    load_dotenv(REPO_DIR / ".env", override=False)
except ImportError:
    pass


def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "ContractSense")
    app_env: str = os.getenv("APP_ENV", "development")
    secret_key: str = os.getenv("SECRET_KEY", "local-development-only-change-me")
    token_ttl_hours: int = int(os.getenv("TOKEN_TTL_HOURS", "12"))
    database_backend: str = os.getenv("DB_BACKEND", "sqlite").lower()
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
    mongodb_db: str = os.getenv("MONGODB_DB", "lexintel")
    data_dir: Path = Path(os.getenv("DATA_DIR", str(REPO_DIR / "storage"))).resolve()
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "25"))
    llm_provider: str = os.getenv("LLM_PROVIDER", "mock").lower()
    llm_model: str = os.getenv("LLM_MODEL", "")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    legalbert_model_path: str = os.getenv("LEGALBERT_MODEL_PATH", "")
    enable_chroma: bool = _bool("ENABLE_CHROMA", True)
    # Same-origin clients do not need CORS. Require explicit opt-in for cross-origin access.
    cors_origins: str = os.getenv("CORS_ORIGINS", "")
    pdf_ocr_language: str = os.getenv("OCR_LANGUAGE", "eng")

    @property
    def upload_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def sqlite_path(self) -> Path:
        return self.data_dir / "lexintel.sqlite3"

    @property
    def chroma_path(self) -> Path:
        return self.data_dir / "chroma"


settings = Settings()

if settings.app_env.lower() in {"prod", "production"}:
    if len(settings.secret_key) < 32 or settings.secret_key in {
        "local-development-only-change-me",
        "replace-with-a-long-random-secret",
        "change_me",
    }:
        raise RuntimeError("Production requires a private SECRET_KEY with at least 32 characters.")
    production_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    if not production_origins or "*" in production_origins:
        raise RuntimeError("Production requires explicit CORS_ORIGINS; empty and wildcard origins are not allowed.")
