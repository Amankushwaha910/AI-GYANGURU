"""
Application configuration using Pydantic Settings.
All secrets are loaded from environment variables — never hardcoded.
"""
from functools import lru_cache
from typing import List, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    app_name: str = "AI GyanGuru"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    app_secret_key: str
    frontend_url: str = "http://localhost:5173"
    api_v1_prefix: str = "/api/v1"

    # ── Database ─────────────────────────────────────────────
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # ── Supabase ─────────────────────────────────────────────
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_storage_bucket: str = "gyanguru-uploads"

    # ── JWT ──────────────────────────────────────────────────
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7

    # ── Google OAuth ─────────────────────────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ── AI Provider ──────────────────────────────────────────
    groq_api_key: str
    # Default model — must be available on the Developer plan.
    # llama-3.3-70b-versatile requires Enterprise; use openai/gpt-oss-120b instead.
    groq_default_model: str = "openai/gpt-oss-120b"
    ai_provider: str = "groq"
    ai_max_retries: int = 2
    ai_request_timeout: int = 60

    # Optional additional AI provider keys (empty string = provider not configured)
    openai_api_key: str = ""
    google_api_key: str = ""

    # Groq models available on the Developer plan (verified September 2026).
    # Enterprise-only models (llama-3.3-70b-versatile, llama-3.1-8b-instant)
    # are intentionally excluded to prevent 404 errors on standard accounts.
    groq_supported_models: List[str] = [
        "openai/gpt-oss-120b",   # 120B params, 500 t/s, $0.15/$0.60 per 1M
        "openai/gpt-oss-20b",    # 20B params,  1000 t/s, $0.075/$0.30 per 1M
        "qwen/qwen3.8-27b",      # Qwen 3.8 27B, 450 t/s, $0.80/$4.00 per 1M
    ]

    # Supported OpenAI models (only populated when OPENAI_API_KEY is set)
    openai_supported_models: List[str] = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-3.5-turbo",
    ]

    # Supported Google Gemini models (only populated when GOOGLE_API_KEY is set)
    google_supported_models: List[str] = [
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]

    # ── OCR ──────────────────────────────────────────────────
    ocr_engine: Literal["paddleocr", "tesseract"] = "paddleocr"
    tesseract_cmd: str = "/usr/bin/tesseract"

    # ── File Upload ──────────────────────────────────────────
    max_file_size_mb: int = 20
    allowed_extensions: str = "pdf,docx,txt,png,jpg,jpeg,webp"

    # ── Rate Limiting ─────────────────────────────────────────
    rate_limit_general: str = "60/minute"
    rate_limit_ai: str = "10/minute"

    # ── Redis ─────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Logging ───────────────────────────────────────────────
    log_level: str = "INFO"

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.allowed_extensions.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def cors_origins(self) -> List[str]:
        origins = [self.frontend_url]
        # In development, also allow IPv6 loopback variant
        if self.app_env == "development":
            port = self.frontend_url.split(":")[-1]
            origins += [
                f"http://localhost:{port}",
                f"http://127.0.0.1:{port}",
                f"http://[::1]:{port}",
            ]
        return list(dict.fromkeys(origins))  # deduplicate

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — loaded once at startup."""
    return Settings()


settings = get_settings()
