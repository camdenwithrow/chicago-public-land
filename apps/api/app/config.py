from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Land to Homes API"
    environment: str = "development"
    database_url: str = (
        "postgresql+psycopg://land_to_homes:land_to_homes@localhost:5432/land_to_homes"
    )
    cors_origins: list[str] = ["http://localhost:5173"]
    socrata_app_token: SecretStr | None = None
    provenance_runs_dir: Path = Path("data/processed/provenance/runs")


@lru_cache
def get_settings() -> Settings:
    return Settings()
