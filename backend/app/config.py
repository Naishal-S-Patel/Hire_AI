"""
Application configuration — reads from environment variables via pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration sourced from env vars / .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Database ──────────────────────────────────────────
    # Default to a local PostgreSQL instance instead of the Docker service name.
    # You can override this in your .env file if your local credentials are different.
    DATABASE_URL: str = "postgresql+asyncpg://postgres:change-me@localhost:5432/recruit_db"

    # ── JWT / Security ────────────────────────────────────
    SECRET_KEY: str = "change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── OpenAI ────────────────────────────────────────────
    OPENAI_API_KEY: str = ""

    # ── ML Services ───────────────────────────────────────
    # Base URL for the external ML service that performs resume parsing.
    # The backend must never parse resumes directly; it always forwards the
    # raw file to this service and consumes its structured JSON response.
    ML_SERVICE_URL: str = "http://localhost:9000"
    RESUME_ML_ENDPOINT: str = "http://localhost:9000/parse_resume"

    # ── Google OAuth2 ─────────────────────────────────────
    GOOGLE_CLIENT_ID: str = "your-google-client-id"
    GOOGLE_CLIENT_SECRET: str = "your-google-client-secret"
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    # ── ChromaDB ──────────────────────────────────────────
    CHROMA_PATH: str = "/data/chroma"

    # ── File Storage ─────────────────────────────────────
    UPLOADS_DIR: str = "uploads"   # relative to backend working directory

    # ── Email Ingestion ───────────────────────────────────
    EMAIL_IMAP_SERVER: str = "imap.gmail.com"
    EMAIL_ADDRESS: str = ""
    EMAIL_PASSWORD: str = ""

    # ── OrangeHRM ─────────────────────────────────────────
    ORANGEHRM_BASE_URL: str = "https://opensource-demo.orangehrmlive.com"
    ORANGEHRM_USERNAME: str = "your-orangehrm-username"
    ORANGEHRM_PASSWORD: str = "your-orangehrm-password"

    # ── Application ───────────────────────────────────────
    APP_ENV: str = "development"


settings = Settings()
