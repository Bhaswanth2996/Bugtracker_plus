from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Bug Tracker+ API"
    app_env: str = "development"
    jwt_secret_key: str = Field(default="change-me-in-prod", min_length=16)
    jwt_algorithm: str = "HS256"
    jwt_exp_minutes: int = 60 * 12
    api_prefix: str = ""
    mongodb_uri: str | None = None
    mongodb_db_name: str = "bugtrackerplus"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"])
    local_upload_dir: str = "uploads"
    enable_demo_seed: bool = False
    azure_blob_connection_string: str | None = None
    azure_blob_container_name: str = "issue-attachments"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="BUGTRACKER_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
