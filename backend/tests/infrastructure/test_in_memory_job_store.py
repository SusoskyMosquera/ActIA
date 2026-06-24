from __future__ import annotations
import time
import pytest
from app.domain.models import (
    AttributedSegment,
    JobStatus,
    JobStage,
    TranscriptionMetadata,
    TranscriptionResult,
)
from app.infrastructure.jobs.in_memory_job_store import InMemoryJobStore


def make_result() -> TranscriptionResult:
    return TranscriptionResult(
        transcript=[
            AttributedSegment(start=0.0, end=5.0, text="hello", speaker="SPEAKER_00")
        ],
        minutes="# Minutes",
        metadata=TranscriptionMetadata(
            duration_sec=5.0, language="es", num_speakers=1, model="test"
        ),
    )


def test_create_returns_pending_job_with_id() -> None:
    store = InMemoryJobStore()
    job = store.create()
    assert job.status == JobStatus.PENDING
    assert job.id != ""


def test_get_returns_same_job() -> None:
    store = InMemoryJobStore()
    job = store.create()
    fetched = store.get(job.id)
    assert fetched is not None
    assert fetched.id == job.id
    assert fetched.status == JobStatus.PENDING


def test_get_unknown_returns_none() -> None:
    store = InMemoryJobStore()
    assert store.get("nonexistent-id") is None


def test_set_stage_marks_processing() -> None:
    store = InMemoryJobStore()
    job = store.create()
    store.set_stage(job.id, JobStage.TRANSCRIBING)
    updated = store.get(job.id)
    assert updated is not None
    assert updated.status == JobStatus.PROCESSING
    assert updated.stage == JobStage.TRANSCRIBING


def test_mark_done_sets_result() -> None:
    store = InMemoryJobStore()
    job = store.create()
    result = make_result()
    store.mark_done(job.id, result)
    updated = store.get(job.id)
    assert updated is not None
    assert updated.status == JobStatus.DONE
    assert updated.result == result
    assert updated.stage is None


def test_mark_error_sets_error_message() -> None:
    store = InMemoryJobStore()
    job = store.create()
    store.mark_error(job.id, "something went wrong")
    updated = store.get(job.id)
    assert updated is not None
    assert updated.status == JobStatus.ERROR
    assert updated.error == "something went wrong"


def test_cleanup_expired_removes_done_error_jobs() -> None:
    store = InMemoryJobStore()
    done_job = store.create()
    error_job = store.create()
    pending_job = store.create()

    result = make_result()
    store.mark_done(done_job.id, result)
    store.mark_error(error_job.id, "err")
    # pending_job stays PENDING

    # Force old timestamps
    store._created_at[done_job.id] = time.time() - 7200  # 2 hours ago
    store._created_at[error_job.id] = time.time() - 7200

    removed = store.cleanup_expired(ttl_seconds=3600)

    assert removed == 2
    assert store.get(done_job.id) is None
    assert store.get(error_job.id) is None
    assert store.get(pending_job.id) is not None


def test_cleanup_does_not_remove_pending_processing_jobs() -> None:
    store = InMemoryJobStore()
    job = store.create()
    store._created_at[job.id] = time.time() - 7200  # old but PENDING

    removed = store.cleanup_expired(ttl_seconds=3600)

    assert removed == 0
    assert store.get(job.id) is not None
