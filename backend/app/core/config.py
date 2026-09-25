import os
from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # App info
    PROJECT_NAME: str = "SevaSangam API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Cooperative-owned digital service marketplace backend API (SIH 26089)"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # PostgreSQL + PostGIS credentials
    POSTGRES_USER: str = "sevasangam"
    POSTGRES_PASSWORD: str = "sevasangam_dev"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_DB: str = "sevasangam"

    # Database URLs (optional overrides, else constructed from the above variables)
    DATABASE_URL: str | None = None
    SYNC_DATABASE_URL: str | None = None

    # Auth & Security
    SECRET_KEY: str = "sevasangam_dev_secret_key_change_in_production_123456789"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days for standard sessions
    ADMIN_TOKEN_EXPIRE_MINUTES: int = 15  # 15 minutes for admin sessions

    # Mock OTP Toggle (for local dev and testing)
    MOCK_OTP_ENABLED: bool = True
    MOCK_OTP_CODE: str = "123456"

    # CORS Allowed Origins
    # Defaults allow Metro, Expo Go, web frontend, and emulator host
    CORS_ORIGINS: List[str] = [
        "http://localhost:8081",
        "http://localhost:19000",
        "http://localhost:19006",
        "http://localhost:3000",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:3000",
        "http://10.0.2.2:8000",
        "http://10.0.2.2:8081",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    @property
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url_resolved(self) -> str:
        if self.SYNC_DATABASE_URL:
            return self.SYNC_DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
