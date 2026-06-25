from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class SpeakerTurn:
    start: float
    end: float
    speaker: str


@dataclass(frozen=True)
class AttributedSegment:
    start: float
    end: float
    text: str
    speaker: str


@dataclass(frozen=True)
class TranscriptionMetadata:
    duration_sec: float
    language: str
    num_speakers: int
    model: str


@dataclass(frozen=True)
class TranscriptionResult:
    transcript: list[AttributedSegment]
    minutes: str
    metadata: TranscriptionMetadata


@dataclass(frozen=True)
class Minutes:
    content: str


class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    ERROR = "ERROR"
    CANCELLED = "CANCELLED"


class JobStage(str, Enum):
    TRANSCRIBING = "TRANSCRIBING"
    DIARIZING = "DIARIZING"
    GENERATING_MINUTES = "GENERATING_MINUTES"


@dataclass
class Job:
    id: str
    status: JobStatus
    stage: JobStage | None = None
    result: TranscriptionResult | None = None
    error: str | None = None
