from __future__ import annotations
import time
import pytest

from app.domain.models import AttributedSegment, SpeakerTurn, TranscriptSegment
from app.infrastructure.analysis.local_audio_analyzer import LocalAudioAnalyzer
from tests.fakes.adapters import FakeDiarizer, FakeTranscriber


# ---------------------------------------------------------------------------
# Attribution correctness
# ---------------------------------------------------------------------------

def test_attribution_correctness() -> None:
    """LocalAudioAnalyzer should correctly attribute speakers to transcript segments."""
    analyzer = LocalAudioAnalyzer(FakeTranscriber(), FakeDiarizer())
    result = analyzer.analyze("fake/path.wav")

    assert len(result) == 2
    assert result[0] == AttributedSegment(
        start=0.0, end=5.0, text="Hello world", speaker="SPEAKER_00"
    )
    assert result[1] == AttributedSegment(
        start=5.0, end=10.0, text="How are you", speaker="SPEAKER_01"
    )


# ---------------------------------------------------------------------------
# Parallelism timing
# ---------------------------------------------------------------------------

def test_parallelism_timing() -> None:
    """Transcription and diarization should run concurrently (wall < 0.85 s for two 0.5 s tasks)."""

    class _SlowTranscriber:
        def transcribe(self, audio_path: str) -> list[TranscriptSegment]:
            time.sleep(0.5)
            return [TranscriptSegment(start=0.0, end=1.0, text="hi")]

    class _SlowDiarizer:
        def diarize(self, audio_path: str) -> list[SpeakerTurn]:
            time.sleep(0.5)
            return [SpeakerTurn(start=0.0, end=1.0, speaker="SPEAKER_00")]

    analyzer = LocalAudioAnalyzer(_SlowTranscriber(), _SlowDiarizer())
    start = time.perf_counter()
    result = analyzer.analyze("fake/path.wav")
    elapsed = time.perf_counter() - start

    assert len(result) == 1
    assert result[0].speaker == "SPEAKER_00"
    # Parallel wall time ~0.5 s; sequential would be ~1.0 s.  Generous upper bound.
    assert elapsed < 0.85


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------

def test_failing_transcriber_propagates_exception() -> None:
    """A transcription error should propagate out of analyze."""

    class _FailingTranscriber:
        def transcribe(self, audio_path: str) -> list[TranscriptSegment]:
            raise RuntimeError("transcriber boom")

    analyzer = LocalAudioAnalyzer(_FailingTranscriber(), FakeDiarizer())
    with pytest.raises(RuntimeError, match="transcriber boom"):
        analyzer.analyze("fake/path.wav")


def test_failing_diarizer_propagates_exception() -> None:
    """A diarization error should propagate out of analyze."""

    class _FailingDiarizer:
        def diarize(self, audio_path: str) -> list[SpeakerTurn]:
            raise RuntimeError("diarizer boom")

    analyzer = LocalAudioAnalyzer(FakeTranscriber(), _FailingDiarizer())
    with pytest.raises(RuntimeError, match="diarizer boom"):
        analyzer.analyze("fake/path.wav")
