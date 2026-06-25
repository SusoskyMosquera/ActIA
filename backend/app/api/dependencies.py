from __future__ import annotations
from functools import lru_cache

from app.application.generate_meeting_minutes import GenerateMeetingMinutes
from app.config import get_settings
from app.domain.ports import (
    AudioAnalyzer,
    AudioTranscriber,
    MinutesGenerator,
    SpeakerDiarizer,
)
from app.infrastructure.analysis.assemblyai_analyzer import AssemblyAIAudioAnalyzer
from app.infrastructure.analysis.local_audio_analyzer import LocalAudioAnalyzer
from app.infrastructure.analysis.speechmatics_analyzer import SpeechmaticsAudioAnalyzer
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
def get_analyzer() -> AudioAnalyzer:
    settings = get_settings()
    if settings.adapter_mode == "demo":
        # Demo mode: wrap demo transcriber/diarizer in the local analyzer (no real models).
        return LocalAudioAnalyzer(get_transcriber(), get_diarizer())
    if settings.analysis_provider == "assemblyai":
        # AssemblyAI path: transcription + diarization happen server-side; do NOT
        # construct the local transcriber/diarizer (avoids loading torch/whisper).
        return AssemblyAIAudioAnalyzer(
            api_key=settings.assemblyai_api_key,
            language=settings.language,
            speakers_expected=settings.assemblyai_speakers_expected,
        )
    if settings.analysis_provider == "speechmatics":
        # Speechmatics path: batch API handles transcription + diarization server-side;
        # speaker count is auto-detected. Do NOT construct local transcriber/diarizer.
        return SpeechmaticsAudioAnalyzer(
            api_key=settings.speechmatics_api_key,
            language=settings.language,
        )
    # Default local path: faster-whisper + pyannote run in parallel.
    return LocalAudioAnalyzer(get_transcriber(), get_diarizer())


@lru_cache(maxsize=1)
def get_use_case() -> GenerateMeetingMinutes:
    settings = get_settings()
    if settings.adapter_mode == "real" and settings.analysis_provider == "assemblyai":
        model_name = "assemblyai"
    elif (
        settings.adapter_mode == "real" and settings.analysis_provider == "speechmatics"
    ):
        model_name = "speechmatics"
    elif settings.adapter_mode == "real":
        model_name = f"faster-whisper:{settings.model_size}"
    else:
        model_name = "demo"
    return GenerateMeetingMinutes(
        analyzer=get_analyzer(),
        generator=get_minutes_generator(),
        store=get_job_store(),
        language=settings.language,
        model_name=model_name,
    )
