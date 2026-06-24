from __future__ import annotations
from app.domain.models import AttributedSegment, SpeakerTurn, TranscriptSegment


def attribute_speakers(
    segments: list[TranscriptSegment],
    turns: list[SpeakerTurn],
) -> list[AttributedSegment]:
    """Assign a speaker to each transcript segment using maximum temporal overlap.

    Rules:
    - No overlapping turn -> speaker = "UNKNOWN"
    - Empty turns list -> all "UNKNOWN"
    - Tie in overlap -> pick earliest-starting speaker turn
    - Partial overlaps are summed per speaker
    """
    result: list[AttributedSegment] = []

    for segment in segments:
        speaker = _assign_speaker(segment, turns)
        result.append(
            AttributedSegment(
                start=segment.start,
                end=segment.end,
                text=segment.text,
                speaker=speaker,
            )
        )

    return result


def _assign_speaker(segment: TranscriptSegment, turns: list[SpeakerTurn]) -> str:
    overlap_by_speaker: dict[str, float] = {}
    earliest_start_by_speaker: dict[str, float] = {}

    for turn in turns:
        overlap = _compute_overlap(segment.start, segment.end, turn.start, turn.end)
        if overlap <= 0.0:
            continue

        if turn.speaker not in overlap_by_speaker:
            overlap_by_speaker[turn.speaker] = 0.0
            earliest_start_by_speaker[turn.speaker] = turn.start
        overlap_by_speaker[turn.speaker] += overlap
        earliest_start_by_speaker[turn.speaker] = min(
            earliest_start_by_speaker[turn.speaker], turn.start
        )

    if not overlap_by_speaker:
        return "UNKNOWN"

    max_overlap = max(overlap_by_speaker.values())
    candidates = [
        spk for spk, ovlp in overlap_by_speaker.items() if ovlp == max_overlap
    ]

    if len(candidates) == 1:
        return candidates[0]

    # Tie-break: pick the speaker whose turn started earliest
    return min(candidates, key=lambda spk: earliest_start_by_speaker[spk])


def _compute_overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    overlap_start = max(a_start, b_start)
    overlap_end = min(a_end, b_end)
    return max(0.0, overlap_end - overlap_start)
