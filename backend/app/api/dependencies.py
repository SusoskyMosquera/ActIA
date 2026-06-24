from __future__ import annotations
from functools import lru_cache

from app.application.generate_meeting_minutes import GenerateMeetingMinutes
from app.config import get_settings
from app.domain.ports import AudioTranscriber, MinutesGenerator, SpeakerDiarizer
from app.infrastructure.diarization.demo_diarizer import DemoDiarizer
from app.infrastructure.diarization.pyannote_diarizer import PyannoteDiarizer
from app.infrastructure.jobs.in_memory_job_store import InMemoryJobStore
from app.infrastructure.nlp.demo_minutes_generator import DemoMinutesGenerator
from app.infrastructure.nlp.gemini_minutes_generator import GeminiMinutesGenerator
from app.infrastructure.nlp.ollama_minutes_generator import OllamaMinutesGenerator
from app.infrastructure.transcription.demo_transcriber import DemoTranscriber
from app.infrastructure.transcription.faster_whisper_transcriber import (
    FasterWhisperTranscriber,
)

# Providers are process-wide singletons (ADR-0001: "load models once").
# ADAPTER_MODE selects between the demo adapters (canned data, no ML stack) and
# the real adapters. Demo is the default so the app runs out of the box; the
# real adapters read their configuration (model size, tokens, device) from
# Settings. Heavy models are loaded lazily inside each real adapter's __init__.


@lru_cache(maxsize=1)
def get_job_store() -> InMemoryJobStore:
    return InMemoryJobStore()


@lru_cache(maxsize=1)
def get_transcriber() -> AudioTranscriber:
    settings = get_settings()
    if settings.adapter_mode == "demo":
        return DemoTranscriber(delay_seconds=settings.demo_delay_seconds)
    return FasterWhisperTranscriber(
        model_size=settings.model_size,
        device=settings.device,
        compute_type=settings.compute_type,
        language=settings.language,
    )


@lru_cache(maxsize=1)
def get_diarizer() -> SpeakerDiarizer:
    settings = get_settings()
    if settings.adapter_mode == "demo":
        return DemoDiarizer(delay_seconds=settings.demo_delay_seconds)
    return PyannoteDiarizer(
        hf_token=settings.huggingface_token,
        model_name=settings.diarization_model,
        device=settings.device,
    )


@lru_cache(maxsize=1)
def get_minutes_generator() -> MinutesGenerator:
    settings = get_settings()
    if settings.adapter_mode == "demo":
        return DemoMinutesGenerator(delay_seconds=settings.demo_delay_seconds)
    if settings.minutes_provider == "ollama":
        return OllamaMinutesGenerator(
            base_url=settings.ollama_base_url,
            model_name=settings.ollama_model,
        )
    return GeminiMinutesGenerator(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_model,
    )


@lru_cache(maxsize=1)
def get_use_case() -> GenerateMeetingMinutes:
    settings = get_settings()
    model_name = (
        f"faster-whisper:{settings.model_size}"
        if settings.adapter_mode == "real"
        else "demo"
    )
    return GenerateMeetingMinutes(
        transcriber=get_transcriber(),
        diarizer=get_diarizer(),
        generator=get_minutes_generator(),
        store=get_job_store(),
        language=settings.language,
        model_name=model_name,
    )
