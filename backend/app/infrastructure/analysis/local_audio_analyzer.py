from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor

from app.domain.models import AttributedSegment
from app.domain.ports import AudioTranscriber, SpeakerDiarizer
from app.domain.services.speaker_attribution import attribute_speakers


class LocalAudioAnalyzer:
    """AudioAnalyzer backed by local transcription + diarization run in parallel.

    Independent stages run concurrently in two threads. faster-whisper (CTranslate2)
    and pyannote (torch) release the GIL during inference, so threads give real
    parallelism — wall time ≈ max(transcribe, diarize) instead of their sum.
    """

    def __init__(
        self, transcriber: AudioTranscriber, diarizer: SpeakerDiarizer
    ) -> None:
        self._transcriber = transcriber
        self._diarizer = diarizer

    def analyze(self, audio_path: str) -> list[AttributedSegment]:
        with ThreadPoolExecutor(max_workers=2) as pool:
            segments_future = pool.submit(self._transcriber.transcribe, audio_path)
            turns_future = pool.submit(self._diarizer.diarize, audio_path)
            segments = segments_future.result()
            turns = turns_future.result()
        return attribute_speakers(segments, turns)
