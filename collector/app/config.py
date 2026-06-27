from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Ищем .env сначала рядом с collector/, потом в корне монорепо
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = "postgresql+asyncpg://airseek:airseek@localhost:5432/airseek"

    # Scheduler intervals (seconds)
    collect_interval_seconds: int = 900  # 15 minutes

    # Sources toggle
    enable_openaq: bool = True
    enable_iqair: bool = False
    enable_http_sensors: bool = False

    # OpenAQ
    openaq_api_key: str = ""
    openaq_city: str = "Bishkek"
    openaq_country: str = "KG"

    # IQAir / AirVisual
    iqair_api_key: str = ""
    iqair_city: str = "Bishkek"
    iqair_state: str = "Bishkek"
    iqair_country: str = "Kyrgyzstan"

    # HTTP Sensors (comma-separated list of base URLs)
    # e.g. "http://192.168.1.10,http://192.168.1.11"
    http_sensor_urls: str = ""

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @field_validator("database_url")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError("Only PostgreSQL is supported")
        return v

    @property
    def http_sensor_url_list(self) -> list[str]:
        if not self.http_sensor_urls:
            return []
        return [u.strip() for u in self.http_sensor_urls.split(",") if u.strip()]


settings = Settings()
