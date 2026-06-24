from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchor the .env to the backend/ directory (this file is backend/app/config.py)
# so it loads regardless of the process's working directory.
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=_ENV_FILE, extra="ignore")

    adapter_mode: str = "demo"  # "demo" | "real"
    demo_delay_seconds: float = 1.5

    # Transcription (faster-whisper) — used when adapter_mode == "real"
    model_size: str = "small"
    language: str = "es"  # "es", "en", ... or "auto"
    device: str = "cpu"  # "cpu" | "cuda"
    compute_type: str = "int8"  # e.g. "int8" (CPU) | "float16" (GPU)

    # Diarization (pyannote.audio)
    diarization_model: str = "pyannote/speaker-diarization-community-1"
    huggingface_token: str = ""

    # Minutes generation — selectable provider
    minutes_provider: str = "gemini"  # "gemini" | "ollama"
    gemini_model: str = "gemini-1.5-flash"
    gemini_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"

    job_ttl_seconds: int = 3600


@lru_cache
def get_settings() -> Settings:
    return Settings()
