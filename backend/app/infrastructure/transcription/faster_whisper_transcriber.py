from __future__ import annotations
from app.domain.models import TranscriptSegment


class FasterWhisperTranscriber:
    """Stub adapter for faster-whisper. Real implementation pending."""

    def transcribe(self, audio_path: str) -> list[TranscriptSegment]:
        # Heavy imports are kept here (inside the method) so the module
        # can be imported without torch/faster-whisper installed.
        raise NotImplementedError("real adapter pending")
