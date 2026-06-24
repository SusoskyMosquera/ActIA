from __future__ import annotations
from app.domain.models import AttributedSegment
from app.infrastructure.diarization.demo_diarizer import DemoDiarizer
from app.infrastructure.nlp.demo_minutes_generator import DemoMinutesGenerator
from app.infrastructure.transcription.demo_transcriber import DemoTranscriber


def test_demo_transcriber_returns_valid_segments() -> None:
    segments = DemoTranscriber(delay_seconds=0.0).transcribe("ignored.wav")

    assert len(segments) > 0
    assert all(seg.end > seg.start for seg in segments)
    assert all(seg.text.strip() for seg in segments)


def test_demo_diarizer_returns_valid_turns() -> None:
    turns = DemoDiarizer(delay_seconds=0.0).diarize("ignored.wav")

    assert len(turns) > 0
    assert all(turn.end > turn.start for turn in turns)
    assert all(turn.speaker.startswith("SPEAKER_") for turn in turns)


def test_demo_minutes_generator_reflects_speakers() -> None:
    transcript = [
        AttributedSegment(start=0.0, end=2.0, text="hola", speaker="SPEAKER_00"),
        AttributedSegment(start=2.0, end=4.0, text="qué tal", speaker="SPEAKER_01"),
    ]

    minutes = DemoMinutesGenerator(delay_seconds=0.0).generate(transcript)

    assert minutes.content.strip()
    assert "##" in minutes.content  # markdown headings
    assert "2 oradores" in minutes.content  # derived from the transcript
