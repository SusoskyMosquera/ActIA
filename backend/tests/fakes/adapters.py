from __future__ import annotations
from app.domain.models import AttributedSegment, Minutes, SpeakerTurn, TranscriptSegment


class FakeAnalyzer:
    """Returns canned attributed segments (two speakers, 10 s total)."""

    def analyze(self, audio_path: str) -> list[AttributedSegment]:
        return [
            AttributedSegment(
                start=0.0, end=5.0, text="Hello world", speaker="SPEAKER_00"
            ),
            AttributedSegment(
                start=5.0, end=10.0, text="How are you", speaker="SPEAKER_01"
            ),
        ]


class FailingAnalyzer:
    """Always raises RuntimeError to simulate an analysis failure."""

    def analyze(self, audio_path: str) -> list[AttributedSegment]:
        raise RuntimeError("Simulated analysis failure")


class FakeTranscriber:
    """Returns canned transcript segments."""

    def transcribe(self, audio_path: str) -> list[TranscriptSegment]:
        return [
            TranscriptSegment(start=0.0, end=5.0, text="Hello world"),
            TranscriptSegment(start=5.0, end=10.0, text="How are you"),
        ]


class FakeDiarizer:
    """Returns canned speaker turns."""

    def diarize(self, audio_path: str) -> list[SpeakerTurn]:
        return [
            SpeakerTurn(start=0.0, end=5.0, speaker="SPEAKER_00"),
            SpeakerTurn(start=5.0, end=10.0, speaker="SPEAKER_01"),
        ]


class FakeMinutesGenerator:
    """Returns a canned minutes string."""

    def generate(self, transcript: list[AttributedSegment]) -> Minutes:
        return Minutes(content="## Meeting Minutes\n\nTest minutes content.")


class FailingTranscriber:
    """Always raises RuntimeError to simulate a transcription failure."""

    def transcribe(self, audio_path: str) -> list[TranscriptSegment]:
        raise RuntimeError("Simulated transcription failure")


class FailingDiarizer:
    """Always raises RuntimeError to simulate a diarization failure."""

    def diarize(self, audio_path: str) -> list[SpeakerTurn]:
        raise RuntimeError("Simulated diarization failure")


class FailingMinutesGenerator:
    """Always raises RuntimeError to simulate a minutes generation failure."""

    def generate(self, transcript: list[AttributedSegment]) -> Minutes:
        raise RuntimeError("Simulated minutes generation failure")
