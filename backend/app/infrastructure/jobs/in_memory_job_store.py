from __future__ import annotations
import threading
import time
from uuid import uuid4

from app.domain.models import Job, JobStage, JobStatus, TranscriptionResult


class InMemoryJobStore:
    """Thread-safe in-memory implementation of the JobStore port."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._created_at: dict[str, float] = {}
        self._lock = threading.Lock()
        self._cancel_requested: set[str] = set()

    def create(self) -> Job:
        job = Job(id=str(uuid4()), status=JobStatus.PENDING)
        with self._lock:
            self._jobs[job.id] = job
            self._created_at[job.id] = time.time()
        return Job(id=job.id, status=job.status)  # return copy

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            return Job(
                id=job.id,
                status=job.status,
                stage=job.stage,
                result=job.result,
                error=job.error,
            )

    def set_stage(self, job_id: str, stage: JobStage) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.PROCESSING
            job.stage = stage

    def mark_done(self, job_id: str, result: TranscriptionResult) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.DONE
            job.stage = None
            job.result = result
            job.error = None

    def mark_error(self, job_id: str, message: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.ERROR
            job.error = message

    def request_cancel(self, job_id: str) -> bool:
        """Flag a job for cancellation. Returns True if the flag was set, False otherwise.

        Returns False when the job does not exist or is already in a terminal state
        (DONE, ERROR, or CANCELLED).
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return False
            if job.status not in (JobStatus.PENDING, JobStatus.PROCESSING):
                return False
            self._cancel_requested.add(job_id)
            return True

    def is_cancelled(self, job_id: str) -> bool:
        """Return True if a cancellation has been requested for this job."""
        with self._lock:
            return job_id in self._cancel_requested

    def mark_cancelled(self, job_id: str) -> None:
        """Mark a job as CANCELLED and clear its stage (mirrors mark_error)."""
        with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.CANCELLED
            job.stage = None

    def cleanup_expired(self, ttl_seconds: float) -> int:
        """Remove terminal jobs (DONE, ERROR, CANCELLED) older than ttl_seconds. Returns count removed."""
        now = time.time()
        to_remove: list[str] = []
        _terminal = (JobStatus.DONE, JobStatus.ERROR, JobStatus.CANCELLED)
        with self._lock:
            for job_id, job in self._jobs.items():
                if job.status not in _terminal:
                    continue
                age = now - self._created_at.get(job_id, now)
                if age >= ttl_seconds:
                    to_remove.append(job_id)
            for job_id in to_remove:
                del self._jobs[job_id]
                self._created_at.pop(job_id, None)
                self._cancel_requested.discard(job_id)
        return len(to_remove)
