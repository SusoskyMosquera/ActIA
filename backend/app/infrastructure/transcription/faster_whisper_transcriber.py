from __future__ import annotations
from app.domain.models import TranscriptSegment


def _segments_from_whisper(raw: object) -> list[TranscriptSegment]:
    """Map faster-whisper segment objects to domain TranscriptSegment.

    Each object in ``raw`` must expose ``.start``, ``.end``, and ``.text``
    attributes (matching faster-whisper's ``Segment`` namedtuple).  The mapping
    is a pure function so it can be unit-tested without the ML stack installed.
    """
    return [
        TranscriptSegment(
            start=float(seg.start),
            end=float(seg.end),
            text=seg.text.strip(),
        )
        for seg in raw
    ]


class FasterWhisperTranscriber:
    """Real transcription adapter backed by faster-whisper (CTranslate2).

    The heavy import and model load happen in ``__init__``, so:
    - the model is loaded exactly once (ADR-0001), and
    - this module stays import-safe when the ML extras are NOT installed
      (demo mode), because ``__init__`` only runs when ``ADAPTER_MODE=real``.
    """

    def __init__(
        self,
        model_size: str = "small",
        device: str = "cpu",
        compute_type: str = "int8",
        language: str = "es",
    ) -> None:
        from faster_whisper import WhisperModel  # lazy heavy import

        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)
        # "auto" -> None lets Whisper auto-detect the language.
        self._language: str | None = None if language == "auto" else language

    def transcribe(self, audio_path: str) -> list[TranscriptSegment]:
        """Transcribe *audio_path* and return domain transcript segments.

        ``vad_filter`` drops silent regions, which improves speed and accuracy.
        ``segments`` is a lazy generator — iterating it is what runs inference.
        """
        lang = self._language if self._language and self._language != "auto" else None
        segments, _info = self._model.transcribe(
            audio_path,
            language=lang,
            vad_filter=True,
        )
        return _segments_from_whisper(segments)
