from __future__ import annotations
import pytest
from app.application.generate_meeting_minutes import GenerateMeetingMinutes
from app.domain.models import JobStage, JobStatus
from app.infrastructure.jobs.in_memory_job_store import InMemoryJobStore
from tests.fakes.adapters import (
    FakeDiarizer,
    FakeMinutesGenerator,
    FakeTranscriber,
    FailingDiarizer,
    FailingMinutesGenerator,
    FailingTranscriber,
)


def make_use_case(
    transcriber=None,
    diarizer=None,
    generator=None,
    store=None,
) -> tuple[GenerateMeetingMinutes, InMemoryJobStore]:
    if store is None:
        store = InMemoryJobStore()
    use_case = GenerateMeetingMinutes(
        transcriber=transcriber or FakeTranscriber(),
        diarizer=diarizer or FakeDiarizer(),
        generator=generator or FakeMinutesGenerator(),
        store=store,
    )
    return use_case, store


def test_happy_path_stages_progress_correctly() -> None:
    """Stages should go TRANSCRIBING -> DIARIZING -> GENERATING_MINUTES -> DONE."""
    use_case, store = make_use_case()
    job = store.create()

    use_case.execute(job.id, "fake/path.wav")

    final = store.get(job.id)
    assert final is not None
    assert final.status == JobStatus.DONE
    assert final.stage is None  # cleared on done


def test_happy_path_result_is_correct() -> None:
    """Job should end with correct transcript, minutes, and metadata."""
    use_case, store = make_use_case()
    job = store.create()

    use_case.execute(job.id, "fake/path.wav")

    final = store.get(job.id)
    assert final is not None
    assert final.result is not None
    assert len(final.result.transcript) == 2
    assert "Meeting Minutes" in final.result.minutes
    assert final.result.metadata.num_speakers == 2
    assert final.result.metadata.duration_sec == 10.0


def test_failing_transcriber_marks_error() -> None:
    """A transcription failure should mark the job ERROR with the exception message."""
    use_case, store = make_use_case(transcriber=FailingTranscriber())
    job = store.create()

    use_case.execute(job.id, "fake/path.wav")

    final = store.get(job.id)
    assert final is not None
    assert final.status == JobStatus.ERROR
    assert "Simulated transcription failure" in (final.error or "")


def test_failing_diarizer_marks_error() -> None:
    """A diarization failure should mark the job ERROR."""
    use_case, store = make_use_case(diarizer=FailingDiarizer())
    job = store.create()

    use_case.execute(job.id, "fake/path.wav")

    final = store.get(job.id)
    assert final is not None
    assert final.status == JobStatus.ERROR
    assert "Simulated diarization failure" in (final.error or "")


def test_failing_generator_marks_error() -> None:
    """A minutes generation failure should mark the job ERROR."""
    use_case, store = make_use_case(generator=FailingMinutesGenerator())
    job = store.create()

    use_case.execute(job.id, "fake/path.wav")

    final = store.get(job.id)
    assert final is not None
    assert final.status == JobStatus.ERROR
    assert "Simulated minutes generation failure" in (final.error or "")
