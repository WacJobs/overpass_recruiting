from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Overpass Recruiting API"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    frontend_origin: str = "http://localhost:5173"
    database_url: str = "sqlite:///./overpass_recruiting.db"
    overpass_api_url: str = "https://overpass-api.de/api/interpreter"
    default_top_k: int = 10
    vector_dim: int = 1024
    user_agent: str = "OverpassRecruiting/0.1 (local-dev)"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
