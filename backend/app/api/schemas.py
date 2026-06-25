from __future__ import annotations
from pydantic import BaseModel


class JobCreatedResponse(BaseModel):
    job_id: str
    status: str  # always "PENDING" on creation


class AttributedSegmentResponse(BaseModel):
    speaker: str
    start: float
    end: float
    text: str


class TranscriptionMetadataResponse(BaseModel):
    duration_sec: float
    language: str
    num_speakers: int
    model: str


class TranscriptionResultResponse(BaseModel):
    transcript: list[AttributedSegmentResponse]
    minutes: str
    metadata: TranscriptionMetadataResponse


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    stage: str | None
    result: TranscriptionResultResponse | None
    error: str | None


class CancelResponse(BaseModel):
    job_id: str
    status: str


class HealthResponse(BaseModel):
    status: str
