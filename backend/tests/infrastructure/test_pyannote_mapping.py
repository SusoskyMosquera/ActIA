from __future__ import annotations
from dataclasses import dataclass

from app.infrastructure.diarization.pyannote_diarizer import _turns_from_diarization


@dataclass
class _FakeSegment:
    start: float
    end: float


class _FakeAnnotation:
    """Mimics a pyannote Annotation's itertracks(yield_label=True) contract."""

    def __init__(self, tracks: list[tuple[_FakeSegment, str, str]]) -> None:
        self._tracks = tracks

    def itertracks(self, yield_label: bool = False):
        assert yield_label is True
        return iter(self._tracks)


def test_turns_from_diarization_maps_tracks() -> None:
    annotation = _FakeAnnotation(
        [
            (_FakeSegment(0.0, 4.5), "A", "SPEAKER_00"),
            (_FakeSegment(4.5, 9.0), "B", "SPEAKER_01"),
        ]
    )

    turns = _turns_from_diarization(annotation)

    assert len(turns) == 2
    assert turns[0].start == 0.0
    assert turns[0].end == 4.5
    assert turns[0].speaker == "SPEAKER_00"
    assert turns[1].speaker == "SPEAKER_01"
