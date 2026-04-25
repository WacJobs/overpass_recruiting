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
    tfidf_max_features: int = 5000
    vectorizer_artifact_path: str = "./artifacts/tfidf_vectorizer.joblib"
    user_agent: str = "OverpassRecruiting/0.1 (local-dev)"

    admin_api_key: str = ""
    openai_api_key: str = ""
    openai_label_model: str = "gpt-5.2"
    naics_version: str = "2022"
    industry_artifact_dir: str = "./artifacts/industry"
    industry_prompt_version: str = "naics_company_v1"
    industry_training_min_confidence: float = 0.70
    industry_semantic_weight: float = 0.80
    industry_alignment_weight: float = 0.20

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
