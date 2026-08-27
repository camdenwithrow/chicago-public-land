from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class PipelineSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = (
        "postgresql+psycopg://land_to_homes:land_to_homes@localhost:5432/land_to_homes"
    )
    socrata_app_token: SecretStr | None = None
    raw_data_dir: Path = Path("data/raw")
    processed_data_dir: Path = Path("data/processed")
    pipeline_version: str = "v1.0.0"
    major_count_change_threshold: float = 0.2
