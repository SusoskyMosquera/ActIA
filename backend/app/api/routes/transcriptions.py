from __future__ import annotations
import os
import shutil
import tempfile
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile

from app.api.dependencies import get_job_store, get_use_case
from app.api.schemas import (
    AttributedSegmentResponse,
    CancelResponse,
    JobCreatedResponse,
    JobStatusResponse,
    TranscriptionMetadataResponse,
    TranscriptionResultResponse,
)
from app.application.generate_meeting_minutes import GenerateMeetingMinutes
from app.infrastructure.jobs.in_memory_job_store import InMemoryJobStore
from app.workers.job_worker import run_job

router = APIRouter()


@router.post("/", status_code=202, response_model=JobCreatedResponse)
async def create_transcription(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    language: str = Form("es"),
    model_size: str = Form("small"),
    num_speakers: int | None = Form(None),
    store: InMemoryJobStore = Depends(get_job_store),
    use_case: GenerateMeetingMinutes = Depends(get_use_case),
) -> JobCreatedResponse:
    """Upload an audio file and start a transcription job."""
    job = store.create()

    fd, tmp_path = tempfile.mkstemp(
        suffix=os.path.splitext(file.filename or ".audio")[1]
    )
    # Stream the upload to disk instead of buffering the whole file in memory —
    # meeting recordings can be large.
    with os.fdopen(fd, "wb") as f:
        shutil.copyfileobj(file.file, f)

    background_tasks.add_task(run_job, job.id, tmp_path, use_case)

    return JobCreatedResponse(job_id=job.id, status=job.status.value)


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_transcription(
    job_id: str,
    store: InMemoryJobStore = Depends(get_job_store),
) -> JobStatusResponse:
    """Get the current status of a transcription job."""
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    result_response = None
    if job.result is not None:
        result_response = TranscriptionResultResponse(
            transcript=[
                AttributedSegmentResponse(
                    speaker=seg.speaker,
                    start=seg.start,
                    end=seg.end,
                    text=seg.text,
                )
                for seg in job.result.transcript
            ],
            minutes=job.result.minutes,
            metadata=TranscriptionMetadataResponse(
                duration_sec=job.result.metadata.duration_sec,
                language=job.result.metadata.language,
                num_speakers=job.result.metadata.num_speakers,
                model=job.result.metadata.model,
            ),
        )

    return JobStatusResponse(
        job_id=job.id,
        status=job.status.value,
        stage=job.stage.value if job.stage is not None else None,
        result=result_response,
        error=job.error,
    )


@router.post("/{job_id}/cancel", response_model=CancelResponse)
async def cancel_transcription(
    job_id: str,
    store: InMemoryJobStore = Depends(get_job_store),
) -> CancelResponse:
    """Request cancellation of an active transcription job.

    Returns 404 if the job does not exist.
    Returns 409 if the job is already in a terminal state (DONE, ERROR, or CANCELLED).
    """
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if not store.request_cancel(job_id):
        raise HTTPException(status_code=409, detail="Job is not cancellable (already finished)")
    updated = store.get(job_id)
    return CancelResponse(job_id=job_id, status=updated.status.value if updated else job.status.value)
