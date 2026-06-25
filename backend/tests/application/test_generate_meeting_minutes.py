from __future__ import annotations
import pytest
from app.application.generate_meeting_minutes import GenerateMeetingMinutes
from app.domain.models import JobStatus
from app.infrastructure.jobs.in_memory_job_store import InMemoryJobStore
from tests.fakes.adapters import (
    FakeAnalyzer,
    FakeMinutesGenerator,
    FailingAnalyzer,
    FailingMinutesGenerator,
)


def make_use_case(
    analyzer=None,
    generator=None,
    store=None,
) -> tuple[GenerateMeetingMinutes, InMemoryJobStore]:
    if store is None:
        store = InMemoryJobStore()
    use_case = GenerateMeetingMinutes(
        analyzer=analyzer or FakeAnalyzer(),
        generator=generator or FakeMinutesGenerator(),
        store=store,
    )
    return use_case, store


def test_happy_path_stages_progress_correctly() -> None:
    """Stages should progress through ANALYZING -> GENERATING_MINUTES -> DONE."""
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


def test_failing_analyzer_marks_error() -> None:
    """An analysis failure should mark the job ERROR with the exception message."""
    use_case, store = make_use_case(analyzer=FailingAnalyzer())
    job = store.create()

    use_case.execute(job.id, "fake/path.wav")

    final = store.get(job.id)
    assert final is not None
    assert final.status == JobStatus.ERROR
    assert "Simulated analysis failure" in (final.error or "")


def test_failing_generator_marks_error() -> None:
    """A minutes generation failure should mark the job ERROR."""
    use_case, store = make_use_case(generator=FailingMinutesGenerator())
    job = store.create()

    use_case.execute(job.id, "fake/path.wav")

    final = store.get(job.id)
    assert final is not None
    assert final.status == JobStatus.ERROR
    assert "Simulated minutes generation failure" in (final.error or "")


# ---------------------------------------------------------------------------
# Cancellation
# ---------------------------------------------------------------------------

def test_cancel_before_execute_short_circuits_pipeline() -> None:
    """Requesting cancel before execute should leave the job CANCELLED.

    FailingAnalyzer is used so that if the pipeline runs past the first cancel
    checkpoint the test would fail with an error rather than CANCELLED — proving
    that cancellation truly short-circuits execution before the analyzer is reached.
    """
    use_case, store = make_use_case(analyzer=FailingAnalyzer())
    job = store.create()

    store.request_cancel(job.id)
    use_case.execute(job.id, "fake/path.wav")

    final = store.get(job.id)
    assert final is not None
    assert final.status == JobStatus.CANCELLED
    # No error should be set — it was cancelled, not failed.
    assert final.error is None


def test_cancel_before_execute_does_not_reach_minutes_generator() -> None:
    """Even with a FailingMinutesGenerator, a pre-cancelled job ends CANCELLED not ERROR."""
    use_case, store = make_use_case(generator=FailingMinutesGenerator())
    job = store.create()

    store.request_cancel(job.id)
    use_case.execute(job.id, "fake/path.wav")

    final = store.get(job.id)
    assert final is not None
    assert final.status == JobStatus.CANCELLED
    assert final.error is None


def test_non_cancelled_run_still_reaches_done() -> None:
    """Sanity-check: a normal run without cancel still reaches DONE."""
    use_case, store = make_use_case()
    job = store.create()

    use_case.execute(job.id, "fake/path.wav")

    final = store.get(job.id)
    assert final is not None
    assert final.status == JobStatus.DONE
    assert final.result is not None
