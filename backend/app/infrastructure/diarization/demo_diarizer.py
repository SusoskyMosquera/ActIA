from __future__ import annotations
import time

from app.domain.models import SpeakerTurn

# Speaker turns aligned with the demo transcript (three speakers).
_DEMO_TURNS: list[tuple[float, float, str]] = [
    (0.0, 4.5, "SPEAKER_00"),
    (4.5, 9.0, "SPEAKER_01"),
    (9.0, 13.5, "SPEAKER_02"),
    (13.5, 18.0, "SPEAKER_00"),
    (18.0, 22.0, "SPEAKER_01"),
    (22.0, 27.0, "SPEAKER_02"),
    (27.0, 31.0, "SPEAKER_00"),
]


class DemoDiarizer:
    """Demo adapter: returns canned speaker turns aligned with the demo transcript.

    Selected when ADAPTER_MODE=demo (the default).
    """

    def __init__(self, delay_seconds: float = 1.5) -> None:
        self._delay_seconds = delay_seconds

    def diarize(self, audio_path: str) -> list[SpeakerTurn]:
        if self._delay_seconds > 0:
            time.sleep(self._delay_seconds)
        return [
            SpeakerTurn(start=start, end=end, speaker=speaker)
            for start, end, speaker in _DEMO_TURNS
        ]
