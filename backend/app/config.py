from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    adapter_mode: str = "demo"  # "demo" | "real"
    demo_delay_seconds: float = 1.5
    model_size: str = "small"
    language: str = "es"
    huggingface_token: str = ""
    gemini_api_key: str = ""
    job_ttl_seconds: int = 3600


@lru_cache
def get_settings() -> Settings:
    return Settings()
