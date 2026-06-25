from __future__ import annotations
from app.application.generate_meeting_minutes import GenerateMeetingMinutes
from app.domain.models import JobStatus
from app.infrastructure.analysis.local_audio_analyzer import LocalAudioAnalyzer
from app.infrastructure.diarization.demo_diarizer import DemoDiarizer
from app.infrastructure.jobs.in_memory_job_store import InMemoryJobStore
from app.infrastructure.nlp.demo_minutes_generator import DemoMinutesGenerator
from app.infrastructure.transcription.demo_transcriber import DemoTranscriber


def test_demo_pipeline_produces_done_job_with_attributed_acta() -> None:
    """End-to-end: real use case + demo adapters yields a DONE job with an acta."""
    store = InMemoryJobStore()
    analyzer = LocalAudioAnalyzer(
        transcriber=DemoTranscriber(delay_seconds=0.0),
        diarizer=DemoDiarizer(delay_seconds=0.0),
    )
    use_case = GenerateMeetingMinutes(
        analyzer=analyzer,
        generator=DemoMinutesGenerator(delay_seconds=0.0),
        store=store,
    )
    job = store.create()

    use_case.execute(job.id, "ignored.wav")

    final = store.get(job.id)
    assert final is not None
    assert final.status == JobStatus.DONE
    assert final.error is None
    assert final.result is not None

    # Every transcript segment is attributed to a real diarized speaker.
    assert len(final.result.transcript) > 0
    assert all(seg.speaker.startswith("SPEAKER_") for seg in final.result.transcript)
    assert all(seg.speaker != "UNKNOWN" for seg in final.result.transcript)

    # The acta is non-empty markdown and the metadata reflects the input.
    assert "Acta" in final.result.minutes
    assert final.result.metadata.num_speakers >= 2
    assert final.result.metadata.duration_sec > 0
