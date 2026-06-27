"""Application configuration management"""
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "LPanda Platform"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str
    API_VERSION: str = "v1"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 10
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 50
    MAX_SUBMISSION_SIZE_MB: int = 200
    ALLOWED_FILE_TYPES: str = "pdf,docx,xlsx,png,jpg,jpeg,gif"

    # Site
    SITE_BASE_URL: str = "http://localhost:3000"

    # Email (Resend)
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "onboarding@resend.dev"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE_PATH: str = ""  # Optional: path to log file for rotation (e.g., "logs/app.log")
    
    # Sentry Error Tracking
    SENTRY_DSN: str = ""  # Optional: Sentry DSN for error tracking
    SENTRY_TRACES_SAMPLE_RATE: float = 1.0  # 100% of transactions for performance monitoring
    SENTRY_PROFILES_SAMPLE_RATE: float = 1.0  # 100% of transactions for profiling
    SENTRY_ENVIRONMENT: str = ""  # Optional: Override environment (defaults to APP_ENV)
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # Admin bootstrap — if set, this user is created/promoted to Overall_Admin
    # on app startup (idempotent). Lets you mint the first admin on deploy
    # without shell/DB access. Clear the env var once the admin exists.
    BOOTSTRAP_ADMIN_EMAIL: str = ""
    BOOTSTRAP_ADMIN_PASSWORD: str = ""
    BOOTSTRAP_ADMIN_USERNAME: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        """Fix database URL to use asyncpg driver if missing"""
        if v and v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip().rstrip('/') for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        """Get allowed file types as a list"""
        return [ft.strip() for ft in self.ALLOWED_FILE_TYPES.split(",")]
    
    @property
    def max_file_size_bytes(self) -> int:
        """Get max file size in bytes"""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    @property
    def max_submission_size_bytes(self) -> int:
        """Get max submission size in bytes"""
        return self.MAX_SUBMISSION_SIZE_MB * 1024 * 1024


settings = Settings()
