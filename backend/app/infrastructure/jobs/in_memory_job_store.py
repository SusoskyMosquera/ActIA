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

    def cleanup_expired(self, ttl_seconds: float) -> int:
        """Remove DONE or ERROR jobs older than ttl_seconds. Returns count removed."""
        now = time.time()
        to_remove: list[str] = []
        with self._lock:
            for job_id, job in self._jobs.items():
                if job.status not in (JobStatus.DONE, JobStatus.ERROR):
                    continue
                age = now - self._created_at.get(job_id, now)
                if age >= ttl_seconds:
                    to_remove.append(job_id)
            for job_id in to_remove:
                del self._jobs[job_id]
                self._created_at.pop(job_id, None)
        return len(to_remove)
