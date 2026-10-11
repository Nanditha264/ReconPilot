from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "dev_secret_key_change_in_production_min_32_bytes_long_12345"
    JWT_SECRET_KEY: str = "dev_jwt_secret_key_change_in_production_min_32_bytes_long_12345"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    CORS_ORIGINS: str | list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Database: PostgreSQL only
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/reconpilot_dev"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_PRE_PING: bool = True

    # Razorpay Integration credentials (optional in dev)
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # LLM & AI Investigation configuration (mock by default)
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gemini-1.5-pro"
    AI_PROVIDER: str = "mock"
    AMOUNT_TOLERANCE: float = 1.00
    AI_AUTO_CLASSIFY_THRESHOLD: float = Field(default=0.90, ge=0.0, le=1.0)
    AI_REVIEW_THRESHOLD: float = Field(default=0.75, ge=0.0, le=1.0)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: object) -> list[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, (list, tuple)):
            return list(v)
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def has_razorpay_credentials(self) -> bool:
        return bool(self.RAZORPAY_KEY_ID and self.RAZORPAY_KEY_SECRET)

    @property
    def has_llm_credentials(self) -> bool:
        return bool(self.LLM_API_KEY)


@lru_cache
def get_settings() -> Settings:
    return Settings()
