from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str = "sqlite:///./crowd_monitor.db"
    api_token: str = "change-me"
    model_path: str = str(ROOT_DIR / "model" / "crowd_prediction_model.pkl")
    weather_api_url: str = "https://api.open-meteo.com/v1/forecast"
    weather_api_key: str = ""
    weather_latitude: float = 19.076
    weather_longitude: float = 72.8777
    cors_origins: str = "*"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
