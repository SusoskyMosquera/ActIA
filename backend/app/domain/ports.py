from __future__ import annotations
from typing import Protocol
from app.domain.models import (
    AttributedSegment,
    Job,
    JobStage,
    Minutes,
    SpeakerTurn,
    TranscriptSegment,
    TranscriptionResult,
)


class AudioTranscriber(Protocol):
    def transcribe(self, audio_path: str) -> list[TranscriptSegment]: ...


class SpeakerDiarizer(Protocol):
    def diarize(self, audio_path: str) -> list[SpeakerTurn]: ...


class AudioAnalyzer(Protocol):
    """Higher-level port: returns attributed segments directly.

    Implementations can combine transcription + diarization locally (LocalAudioAnalyzer)
    or delegate both to a hosted service that returns speaker-attributed output in one call
    (AssemblyAIAudioAnalyzer).
    """

    def analyze(self, audio_path: str) -> list[AttributedSegment]: ...


class MinutesGenerator(Protocol):
    def generate(self, transcript: list[AttributedSegment]) -> Minutes: ...


class JobStore(Protocol):
    def create(self) -> Job: ...

    def get(self, job_id: str) -> Job | None: ...

    def set_stage(self, job_id: str, stage: JobStage) -> None: ...

    def mark_done(self, job_id: str, result: TranscriptionResult) -> None: ...

    def mark_error(self, job_id: str, message: str) -> None: ...

    def request_cancel(self, job_id: str) -> bool: ...

    def is_cancelled(self, job_id: str) -> bool: ...

    def mark_cancelled(self, job_id: str) -> None: ...
