from __future__ import annotations
import pytest
from app.domain.models import SpeakerTurn, TranscriptSegment
from app.domain.services.speaker_attribution import attribute_speakers


def test_basic_assignment_segment_within_turn() -> None:
    """A segment fully within a speaker turn should get that speaker."""
    segments = [TranscriptSegment(start=1.0, end=4.0, text="hello")]
    turns = [SpeakerTurn(start=0.0, end=5.0, speaker="SPEAKER_00")]

    result = attribute_speakers(segments, turns)

    assert len(result) == 1
    assert result[0].speaker == "SPEAKER_00"
    assert result[0].text == "hello"


def test_empty_turns_all_unknown() -> None:
    """When no speaker turns exist, every segment should be UNKNOWN."""
    segments = [
        TranscriptSegment(start=0.0, end=3.0, text="hello"),
        TranscriptSegment(start=3.0, end=6.0, text="world"),
    ]
    result = attribute_speakers(segments, turns=[])

    assert all(seg.speaker == "UNKNOWN" for seg in result)


def test_no_overlapping_turn_is_unknown() -> None:
    """A segment with no overlapping turn should be UNKNOWN."""
    segments = [TranscriptSegment(start=10.0, end=15.0, text="late segment")]
    turns = [SpeakerTurn(start=0.0, end=5.0, speaker="SPEAKER_00")]

    result = attribute_speakers(segments, turns)

    assert result[0].speaker == "UNKNOWN"


def test_partial_overlap_correct_speaker_wins() -> None:
    """The speaker with more overlap area should win."""
    # Segment: 2.0 -> 8.0 (6 sec)
    # SPEAKER_00: 0.0 -> 4.0 -> overlap = 2.0 sec
    # SPEAKER_01: 4.0 -> 10.0 -> overlap = 4.0 sec
    segments = [TranscriptSegment(start=2.0, end=8.0, text="split")]
    turns = [
        SpeakerTurn(start=0.0, end=4.0, speaker="SPEAKER_00"),
        SpeakerTurn(start=4.0, end=10.0, speaker="SPEAKER_01"),
    ]

    result = attribute_speakers(segments, turns)

    assert result[0].speaker == "SPEAKER_01"


def test_tie_picks_earliest_starting_speaker() -> None:
    """When two speakers have equal overlap, the one whose turn started first wins."""
    # Segment: 2.0 -> 6.0 (4 sec)
    # SPEAKER_00: 0.0 -> 4.0 -> overlap = 2.0 sec, starts at 0.0
    # SPEAKER_01: 4.0 -> 8.0 -> overlap = 2.0 sec, starts at 4.0
    segments = [TranscriptSegment(start=2.0, end=6.0, text="tie")]
    turns = [
        SpeakerTurn(start=0.0, end=4.0, speaker="SPEAKER_00"),
        SpeakerTurn(start=4.0, end=8.0, speaker="SPEAKER_01"),
    ]

    result = attribute_speakers(segments, turns)

    assert result[0].speaker == "SPEAKER_00"


def test_multiple_segments_correct_attribution() -> None:
    """Each segment should be attributed to the correct speaker."""
    segments = [
        TranscriptSegment(start=0.0, end=5.0, text="first"),
        TranscriptSegment(start=5.0, end=10.0, text="second"),
    ]
    turns = [
        SpeakerTurn(start=0.0, end=5.0, speaker="SPEAKER_00"),
        SpeakerTurn(start=5.0, end=10.0, speaker="SPEAKER_01"),
    ]

    result = attribute_speakers(segments, turns)

    assert result[0].speaker == "SPEAKER_00"
    assert result[1].speaker == "SPEAKER_01"


def test_empty_segments_returns_empty() -> None:
    """Empty segments input should return empty list."""
    turns = [SpeakerTurn(start=0.0, end=5.0, speaker="SPEAKER_00")]
    result = attribute_speakers(segments=[], turns=turns)
    assert result == []


def test_summed_partial_overlaps_per_speaker() -> None:
    """Overlaps from multiple turns of the same speaker should be summed."""
    # Segment: 0.0 -> 10.0
    # SPEAKER_00: 0.0->3.0 (3 sec) + 7.0->10.0 (3 sec) = 6 sec
    # SPEAKER_01: 3.0->7.0 (4 sec) = 4 sec
    segments = [TranscriptSegment(start=0.0, end=10.0, text="mixed")]
    turns = [
        SpeakerTurn(start=0.0, end=3.0, speaker="SPEAKER_00"),
        SpeakerTurn(start=3.0, end=7.0, speaker="SPEAKER_01"),
        SpeakerTurn(start=7.0, end=10.0, speaker="SPEAKER_00"),
    ]

    result = attribute_speakers(segments, turns)

    assert result[0].speaker == "SPEAKER_00"
