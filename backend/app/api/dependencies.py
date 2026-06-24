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
from app.infrastructure.transcription.demo_transcriber import DemoTranscriber
from app.infrastructure.transcription.faster_whisper_transcriber import (
    FasterWhisperTranscriber,
)

# Providers are process-wide singletons (ADR-0001: "load models once").
# ADAPTER_MODE selects between the demo adapters (canned data, no ML stack)
# and the real adapters. Demo is the default so the app runs end-to-end out of
# the box; switch to "real" once the ML dependencies and credentials are set.


@lru_cache(maxsize=1)
def get_job_store() -> InMemoryJobStore:
    return InMemoryJobStore()


@lru_cache(maxsize=1)
def get_transcriber() -> AudioTranscriber:
    settings = get_settings()
    if settings.adapter_mode == "demo":
        return DemoTranscriber(delay_seconds=settings.demo_delay_seconds)
    return FasterWhisperTranscriber()


@lru_cache(maxsize=1)
def get_diarizer() -> SpeakerDiarizer:
    settings = get_settings()
    if settings.adapter_mode == "demo":
        return DemoDiarizer(delay_seconds=settings.demo_delay_seconds)
    return PyannoteDiarizer()


@lru_cache(maxsize=1)
def get_minutes_generator() -> MinutesGenerator:
    settings = get_settings()
    if settings.adapter_mode == "demo":
        return DemoMinutesGenerator(delay_seconds=settings.demo_delay_seconds)
    return GeminiMinutesGenerator()


@lru_cache(maxsize=1)
def get_use_case() -> GenerateMeetingMinutes:
    return GenerateMeetingMinutes(
        transcriber=get_transcriber(),
        diarizer=get_diarizer(),
        generator=get_minutes_generator(),
        store=get_job_store(),
    )
