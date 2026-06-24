from __future__ import annotations
from app.domain.models import SpeakerTurn


class PyannoteDiarizer:
    """Stub adapter for pyannote.audio. Real implementation pending."""

    def diarize(self, audio_path: str) -> list[SpeakerTurn]:
        # Heavy imports kept inside the method so this module is safe to import
        # without pyannote / torch installed.
        raise NotImplementedError("real adapter pending")
