"""OpenCord Configuration — loaded from env."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # General
    NODE_ENV: str = "development"
    OPENCORD_VERSION: str = "0.1.0"
    OPENCORD_INSTANCE_NAME: str = "OpenCord"
    OPENCORD_BASE_URL: str = "http://localhost:3000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://opencord:opencord@localhost:5432/opencord"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 10080  # 7 days

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Features
    FEATURE_AI_SUMMARY: bool = True
    FEATURE_API_TOKENS: bool = True
    FEATURE_DATA_EXPORT: bool = True
    FEATURE_REGISTRATION: bool = True

    # Initial admin
    INITIAL_ADMIN_EMAIL: str = "admin@opencord.local"
    INITIAL_ADMIN_USERNAME: str = "admin"
    INITIAL_ADMIN_PASSWORD: str = "change-me"

    # Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Logging
    LOG_LEVEL: str = "INFO"


settings = Settings()
