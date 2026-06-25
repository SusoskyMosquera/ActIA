from __future__ import annotations

from app.domain.models import (
    JobStage,
    TranscriptionMetadata,
    TranscriptionResult,
)
from app.domain.ports import AudioAnalyzer, JobStore, MinutesGenerator


class GenerateMeetingMinutes:
    """Use case: orchestrate analysis (transcription + diarization) and minutes generation.

    The heavy audio analysis is delegated to the AudioAnalyzer port, which may be
    a LocalAudioAnalyzer (faster-whisper + pyannote running in parallel) or a
    hosted analyzer such as AssemblyAIAudioAnalyzer.
    """

    def __init__(
        self,
        analyzer: AudioAnalyzer,
        generator: MinutesGenerator,
        store: JobStore,
        language: str = "es",
        model_name: str = "faster-whisper:small",
    ) -> None:
        self._analyzer = analyzer
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

        The analyzer encapsulates how transcription and diarization happen (locally
        in parallel, or via a hosted service). Cancellation checkpoints sit at the
        stage boundaries; if a cancel is requested the job is marked CANCELLED and
        the method returns without running further stages.
        """
        try:
            if self._check_cancelled(job_id):
                return

            self._store.set_stage(job_id, JobStage.ANALYZING)
            attributed = self._analyzer.analyze(audio_path)

            if self._check_cancelled(job_id):
                return

            self._store.set_stage(job_id, JobStage.GENERATING_MINUTES)
            minutes = self._generator.generate(attributed)

            if self._check_cancelled(job_id):
                return

            duration_sec = max((seg.end for seg in attributed), default=0.0)
            num_speakers = len({seg.speaker for seg in attributed})
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
