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

    # Analysis provider — selectable ("local" uses faster-whisper + pyannote in parallel;
    # "assemblyai" delegates transcription + diarization to AssemblyAI in one hosted call,
    # which is better suited for long recordings of several hours;
    # "speechmatics" delegates to the Speechmatics batch API which auto-detects speaker
    # count and offers a recurring free tier of ~480 min/month).
    analysis_provider: str = "local"  # "local" | "assemblyai" | "speechmatics"
    assemblyai_api_key: str = ""
    assemblyai_speakers_expected: int = 0  # 0 = auto; set the known count to help diarization
    speechmatics_api_key: str = ""

    # Minutes generation — selectable provider
    minutes_provider: str = "gemini"  # "gemini" | "ollama"
    gemini_model: str = "gemini-1.5-flash"
    gemini_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"

    job_ttl_seconds: int = 3600
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    max_upload_size_bytes: int = 104857600  # 100 MB default
    allowed_audio_extensions: str = "wav,mp3,m4a,webm,ogg,mp4,flac,aac"



@lru_cache
def get_settings() -> Settings:
    return Settings()
