from __future__ import annotations
import logging

from app.domain.models import AttributedSegment

logger = logging.getLogger(__name__)


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

    ``speakers_expected`` (0 = auto) is passed as a diarization hint; AssemblyAI
    uses it for files longer than ~2 minutes to avoid collapsing similar voices
    into a single speaker.
    """

    def __init__(
        self,
        api_key: str,
        language: str = "es",
        speakers_expected: int = 0,
    ) -> None:
        if not api_key.strip():
            raise ValueError(
                "ASSEMBLYAI_API_KEY is required for the AssemblyAI provider."
            )
        self._api_key = api_key
        self._language = language
        self._speakers_expected = speakers_expected

    def analyze(self, audio_path: str) -> list[AttributedSegment]:
        import assemblyai as aai  # lazy import — SDK only needed in assemblyai mode

        aai.settings.api_key = self._api_key

        params: dict[str, object] = {"speaker_labels": True}
        if self._language == "auto":
            params["language_detection"] = True
        else:
            params["language_code"] = self._language
        if self._speakers_expected > 0:
            params["speakers_expected"] = self._speakers_expected

        config = aai.TranscriptionConfig(**params)
        transcript = aai.Transcriber().transcribe(audio_path, config=config)
        if transcript.status == aai.TranscriptStatus.error:
            raise RuntimeError(f"AssemblyAI transcription failed: {transcript.error}")

        utterances = transcript.utterances or []
        speakers = {u.speaker for u in utterances}
        logger.info(
            "AssemblyAI returned %d utterance(s) across %d speaker(s): %s",
            len(utterances),
            len(speakers),
            sorted(speakers),
        )
        if len(speakers) <= 1:
            logger.warning(
                "AssemblyAI detected a single speaker. If the meeting had several, "
                "set ASSEMBLYAI_SPEAKERS_EXPECTED to the known count, or the audio "
                "(single far-field mic / overlapping speech) may be hard to diarize."
            )

        return _to_attributed(utterances)
