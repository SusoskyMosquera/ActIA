from __future__ import annotations
from app.domain.models import AttributedSegment


def _speaker_label(speaker: str) -> str:
    """Map AssemblyAI speaker labels to the project's SPEAKER_NN convention.

    AssemblyAI labels speakers "A", "B", … — we map them to SPEAKER_00,
    SPEAKER_01, … for consistency with the local (pyannote) output. Non-single-
    letter labels are prefixed verbatim.
    """
    if len(speaker) == 1 and speaker.isalpha():
        return f"SPEAKER_{ord(speaker.upper()) - ord('A'):02d}"
    return f"SPEAKER_{speaker}"


def _to_attributed(utterances: object) -> list[AttributedSegment]:
    """Map AssemblyAI utterances (start/end in ms) to domain AttributedSegment (seconds)."""
    return [
        AttributedSegment(
            start=u.start / 1000.0,
            end=u.end / 1000.0,
            text=u.text.strip(),
            speaker=_speaker_label(u.speaker),
        )
        for u in (utterances or [])
    ]


class AssemblyAIAudioAnalyzer:
    """AudioAnalyzer backed by AssemblyAI (transcription + diarization in one call).

    Handles long audio (hours) server-side. The API key is validated BEFORE any
    SDK import so the ValueError is testable without the SDK installed.
    """

    def __init__(self, api_key: str, language: str = "es") -> None:
        if not api_key.strip():
            raise ValueError("ASSEMBLYAI_API_KEY is required for the AssemblyAI provider.")
        self._api_key = api_key
        self._language = language

    def analyze(self, audio_path: str) -> list[AttributedSegment]:
        import assemblyai as aai  # lazy import — SDK only needed in assemblyai mode

        aai.settings.api_key = self._api_key
        if self._language == "auto":
            config = aai.TranscriptionConfig(speaker_labels=True, language_detection=True)
        else:
            config = aai.TranscriptionConfig(speaker_labels=True, language_code=self._language)
        transcript = aai.Transcriber().transcribe(audio_path, config=config)
        if transcript.status == aai.TranscriptStatus.error:
            raise RuntimeError(f"AssemblyAI transcription failed: {transcript.error}")
        return _to_attributed(transcript.utterances)
