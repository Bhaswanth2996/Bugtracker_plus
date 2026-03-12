from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Bug Tracker+ API"
    app_env: str = "development"
    jwt_secret_key: str = Field(default="change-me-in-prod", min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60 * 12
    mongodb_uri: str | None = None
    mongodb_db_name: str = "bugtrackerplus"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BUGTRACKER_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
