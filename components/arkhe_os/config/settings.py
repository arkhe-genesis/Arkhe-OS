from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import secrets

class Settings(BaseSettings):
    # API Settings
    PROJECT_NAME: str = "Arkhe OS API"
    VERSION: str = "∞.4.2"
    API_V1_STR: str = "/v1"

    # Security
    # In production, this MUST be set via environment variable
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Database
    DATABASE_URL: str = "sqlite:///./arkhe.db"

    # Redis
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"

    # First Superuser
    FIRST_SUPERUSER: str = "architect@arkhe.io"
    FIRST_SUPERUSER_PASSWORD: str = "changethis"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

settings = Settings()
