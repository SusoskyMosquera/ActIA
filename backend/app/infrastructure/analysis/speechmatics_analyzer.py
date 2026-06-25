from __future__ import annotations
import logging

from app.domain.models import AttributedSegment

logger = logging.getLogger(__name__)

_SPEECHMATICS_URL = "https://asr.api.speechmatics.com/v2"


def _speaker_label(speaker: str) -> str:
    """Map Speechmatics speaker labels ("S1","S2",…) to SPEAKER_00, SPEAKER_01,…"""
    if speaker and speaker[0].upper() == "S" and speaker[1:].isdigit():
        return f"SPEAKER_{int(speaker[1:]) - 1:02d}"
    return f"SPEAKER_{speaker}"


def _join_tokens(tokens: list[tuple[str, bool]]) -> str:
    """Join (content, is_punctuation) tokens: spaces between words, punctuation attached."""
    text = ""
    for content, is_punctuation in tokens:
        if not text or is_punctuation:
            text += content
        else:
            text += " " + content
    return text


def _to_attributed(results: object) -> list[AttributedSegment]:
    """Group Speechmatics word/punctuation items into per-speaker segments (pure)."""
    runs: list[dict] = []
    for item in (results or []):
        itype = item.get("type")
        if itype == "speaker_change":
            continue
        alternatives = item.get("alternatives") or []
        if not alternatives:
            continue
        content = (alternatives[0].get("content") or "").strip()
        if not content:
            continue
        speaker = alternatives[0].get("speaker") or "UU"
        start = float(item.get("start_time", 0.0))
        end = float(item.get("end_time", start))
        is_punctuation = itype == "punctuation"
        if not runs or runs[-1]["speaker"] != speaker:
            runs.append({"speaker": speaker, "start": start, "end": end, "tokens": []})
        runs[-1]["end"] = end
        runs[-1]["tokens"].append((content, is_punctuation))
    return [
        AttributedSegment(
            start=run["start"],
            end=run["end"],
            text=_join_tokens(run["tokens"]),
            speaker=_speaker_label(run["speaker"]),
        )
        for run in runs
    ]


class SpeechmaticsAudioAnalyzer:
    """AudioAnalyzer backed by Speechmatics batch (transcription + diarization).

    Speaker diarization is automatic (no fixed speaker count). The API key is
    validated BEFORE any SDK import so the ValueError is testable without the SDK.
    """

    def __init__(self, api_key: str, language: str = "es") -> None:
        if not api_key.strip():
            raise ValueError("SPEECHMATICS_API_KEY is required for the Speechmatics provider.")
        self._api_key = api_key
        # Speechmatics needs a concrete language code; fall back to Spanish for "auto".
        self._language = "es" if language == "auto" else language

    def analyze(self, audio_path: str) -> list[AttributedSegment]:
        import os
        import subprocess
        import tempfile
        import httpx
        from speechmatics.batch_client import BatchClient  # lazy import
        from speechmatics.models import BatchTranscriptionConfig, ConnectionSettings

        # If it's a webm file (common for browser recordings), transcode to wav using ffmpeg
        cleanup_temp_wav = False
        actual_audio_path = audio_path
        if audio_path.lower().endswith(".webm"):
            import shutil
            ffmpeg_exe = shutil.which("ffmpeg") or "ffmpeg"
            temp_wav_fd, temp_wav_path = tempfile.mkstemp(suffix=".wav")
            os.close(temp_wav_fd)
            try:
                subprocess.run(
                    [ffmpeg_exe, "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", temp_wav_path],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=180,
                )
                actual_audio_path = temp_wav_path
                cleanup_temp_wav = True
                logger.info("Successfully transcoded WebM browser recording to WAV format.")

            except subprocess.TimeoutExpired as e:
                logger.error("FFmpeg transcoding timed out after 180 seconds.")
                raise ValueError("FFmpeg transcoding timed out.") from e
            except subprocess.CalledProcessError as e:
                logger.error("FFmpeg transcoding failed (exit status %d):\n%s", e.returncode, e.stderr)
                raise ValueError(f"Failed to transcode WebM audio via FFmpeg: {e.stderr.strip()}") from e
            except Exception as e:
                logger.error("Unexpected error during FFmpeg transcoding: %s", e)
                raise ValueError(f"Unexpected error during FFmpeg transcoding: {e}") from e


        settings = ConnectionSettings(url=_SPEECHMATICS_URL, auth_token=self._api_key)
        config = BatchTranscriptionConfig(language=self._language, diarization="speaker")
        try:
            with BatchClient(settings) as client:
                job_id = client.submit_job(audio=actual_audio_path, transcription_config=config)
                transcript = client.wait_for_completion(job_id, transcription_format="json-v2")
        except httpx.HTTPStatusError as exc:
            try:
                err_json = exc.response.json()
                detail = err_json.get("detail") or err_json.get("error") or str(exc)
                raise ValueError(f"Speechmatics API error: {detail}") from exc
            except Exception:
                raise ValueError(f"Speechmatics API error: {exc.response.text or str(exc)}") from exc
        finally:
            if cleanup_temp_wav and os.path.exists(actual_audio_path):
                try:
                    os.remove(actual_audio_path)
                except OSError as e:
                    logger.warning("Could not remove temp WAV file: %s", e)

        results = transcript.get("results", []) if isinstance(transcript, dict) else []
        segments = _to_attributed(results)
        speakers = {seg.speaker for seg in segments}
        logger.info(
            "Speechmatics returned %d segment(s) across %d speaker(s): %s",
            len(segments), len(speakers), sorted(speakers),
        )
        return segments

