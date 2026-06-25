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

    def _check_cancelled(self, job_id: str) -> bool:
        """Return True and mark the job CANCELLED if cancellation was requested.

        Must NOT raise — it is called inside the try/except that marks ERROR,
        and we do not want a cancellation to be mis-classified as an error.
        """
        if self._store.is_cancelled(job_id):
            self._store.mark_cancelled(job_id)
            return True
        return False

    def execute(self, job_id: str, audio_path: str) -> None:
        """Run the full pipeline. Catches all exceptions and marks the job ERROR.

        Cancellation checkpoints are inserted before each stage. If a cancel is
        requested the job is marked CANCELLED and the method returns early without
        running the remaining stages.
        """
        try:
            if self._check_cancelled(job_id):
                return
            self._store.set_stage(job_id, JobStage.TRANSCRIBING)
            segments = self._transcriber.transcribe(audio_path)

            if self._check_cancelled(job_id):
                return
            self._store.set_stage(job_id, JobStage.DIARIZING)
            turns = self._diarizer.diarize(audio_path)

            if self._check_cancelled(job_id):
                return
            attributed: list[AttributedSegment] = attribute_speakers(segments, turns)

            self._store.set_stage(job_id, JobStage.GENERATING_MINUTES)
            minutes = self._generator.generate(attributed)

            if self._check_cancelled(job_id):
                return

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
