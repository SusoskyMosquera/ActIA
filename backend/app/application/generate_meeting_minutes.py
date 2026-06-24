from __future__ import annotations
from app.domain.models import (
    AttributedSegment,
    JobStage,
    TranscriptionMetadata,
    TranscriptionResult,
)
from app.domain.ports import AudioTranscriber, JobStore, MinutesGenerator, SpeakerDiarizer
from app.domain.services.speaker_attribution import attribute_speakers


class GenerateMeetingMinutes:
    """Use case: orchestrate transcription, diarization, speaker attribution, and minutes generation."""

    def __init__(
        self,
        transcriber: AudioTranscriber,
        diarizer: SpeakerDiarizer,
        generator: MinutesGenerator,
        store: JobStore,
        language: str = "es",
        model_name: str = "faster-whisper:small",
    ) -> None:
        self._transcriber = transcriber
        self._diarizer = diarizer
        self._generator = generator
        self._store = store
        self._language = language
        self._model_name = model_name

    def execute(self, job_id: str, audio_path: str) -> None:
        """Run the full pipeline. Catches all exceptions and marks the job ERROR."""
        try:
            self._store.set_stage(job_id, JobStage.TRANSCRIBING)
            segments = self._transcriber.transcribe(audio_path)

            self._store.set_stage(job_id, JobStage.DIARIZING)
            turns = self._diarizer.diarize(audio_path)

            attributed: list[AttributedSegment] = attribute_speakers(segments, turns)

            self._store.set_stage(job_id, JobStage.GENERATING_MINUTES)
            minutes = self._generator.generate(attributed)

            duration_sec = max((seg.end for seg in segments), default=0.0)
            num_speakers = len({t.speaker for t in turns})
            metadata = TranscriptionMetadata(
                duration_sec=duration_sec,
                language=self._language,
                num_speakers=num_speakers,
                model=self._model_name,
            )
            result = TranscriptionResult(
                transcript=attributed,
                minutes=minutes.content,
                metadata=metadata,
            )
            self._store.mark_done(job_id, result)

        except Exception as exc:  # noqa: BLE001
            self._store.mark_error(job_id, str(exc))
