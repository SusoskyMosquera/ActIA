from __future__ import annotations
from dataclasses import dataclass

from app.infrastructure.transcription.faster_whisper_transcriber import (
    _segments_from_whisper,
)


@dataclass
class _FakeWhisperSegment:
    start: float
    end: float
    text: str


def test_segments_from_whisper_maps_and_strips() -> None:
    raw = [
        _FakeWhisperSegment(0.0, 2.5, "  hello world  "),
        _FakeWhisperSegment(2.5, 4.0, "second"),
    ]

    result = _segments_from_whisper(raw)

    assert len(result) == 2
    assert result[0].start == 0.0
    assert result[0].end == 2.5
    assert result[0].text == "hello world"  # stripped
    assert result[1].text == "second"


def test_segments_from_whisper_empty() -> None:
    assert _segments_from_whisper([]) == []
