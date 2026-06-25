from __future__ import annotations
import os
import shutil
import tempfile
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    UploadFile,
    Request,
)

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
from app.config import Settings, get_settings
from app.infrastructure.jobs.in_memory_job_store import InMemoryJobStore
from app.workers.job_worker import run_job
from app.api.rate_limit import limiter

router = APIRouter()


def copy_file_with_limit(src, dst, max_size: int, buffer_size: int = 8192) -> int:
    """Copy src to dst while enforcing a maximum size in bytes.

    Raises HTTPException(413) if max_size is exceeded.
    Returns total bytes written.
    """
    total_bytes = 0
    while True:
        chunk = src.read(buffer_size)
        if not chunk:
            break
        total_bytes += len(chunk)
        if total_bytes > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"Payload too large. Maximum allowed size is {max_size} bytes.",
            )
        dst.write(chunk)
    return total_bytes


@router.post("/", status_code=202, response_model=JobCreatedResponse)
@limiter.limit("5/minute")
async def create_transcription(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile,
    store: InMemoryJobStore = Depends(get_job_store),
    use_case: GenerateMeetingMinutes = Depends(get_use_case),
    settings: Settings = Depends(get_settings),
) -> JobCreatedResponse:
    """Upload an audio file and start a transcription job."""

    # 1. Fail fast on Content-Length header if present
    content_length_str = request.headers.get("content-length")
    if content_length_str:
        try:
            content_length = int(content_length_str)
            if content_length > settings.max_upload_size_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"Payload too large. Maximum allowed size is {settings.max_upload_size_bytes} bytes.",
                )
        except ValueError:
            pass

    # 2. Validate file extension
    filename = file.filename or ""
    extension = os.path.splitext(filename)[1].lower()
    allowed_exts = {
        f".{ext.strip().lower().lstrip('.')}"
        for ext in settings.allowed_audio_extensions.split(",")
        if ext.strip()
    }
    if not extension or extension not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension '{extension}'. Allowed: {', '.join(sorted(allowed_exts))}",
        )

    # 3. Create job and write file to disk with strict size limit and cleanup on failure
    job = store.create()

    fd, tmp_path = tempfile.mkstemp(suffix=extension)
    try:
        with os.fdopen(fd, "wb") as f:
            copy_file_with_limit(file.file, f, settings.max_upload_size_bytes)
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise

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
        raise HTTPException(
            status_code=409, detail="Job is not cancellable (already finished)"
        )
    updated = store.get(job_id)
    return CancelResponse(
        job_id=job_id, status=updated.status.value if updated else job.status.value
    )
