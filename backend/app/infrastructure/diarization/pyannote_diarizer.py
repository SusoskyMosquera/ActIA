from __future__ import annotations
from app.domain.models import SpeakerTurn


def _turns_from_diarization(annotation: object) -> list[SpeakerTurn]:
    """Map a pyannote Annotation to domain SpeakerTurn objects.

    Iterates ``annotation.itertracks(yield_label=True)`` which yields
    ``(segment, track_id, speaker_label)`` triples.  The mapping is a pure
    function so it can be unit-tested without pyannote installed.
    """
    return [
        SpeakerTurn(
            start=float(turn.start),
            end=float(turn.end),
            speaker=speaker,
        )
        for turn, _track, speaker in annotation.itertracks(yield_label=True)
    ]


class PyannoteDiarizer:
    """Real diarization adapter backed by pyannote.audio.

    Requires a Hugging Face token AND prior acceptance of the gated terms for
    the diarization model (and its segmentation dependency).  The token is
    validated BEFORE any heavy import so the ValueError is testable without the
    ML stack installed.
    """

    def __init__(
        self,
        hf_token: str,
        model_name: str = "pyannote/speaker-diarization-3.1",
        device: str = "cpu",
    ) -> None:
        if not hf_token.strip():
            raise ValueError(
                "HUGGINGFACE_TOKEN is required for real diarization. Create a "
                "token and accept the gated model terms on Hugging Face."
            )

        from pyannote.audio import Pipeline  # lazy heavy import
        import torch

        pipeline = Pipeline.from_pretrained(model_name, token=hf_token)
        # from_pretrained returns None (instead of raising) when the token is
        # invalid or the gated terms were not accepted — make that explicit.
        if pipeline is None:
            raise RuntimeError(
                f"Could not load '{model_name}'. Verify the HF token is valid and "
                "that you accepted the gated terms for BOTH "
                "pyannote/speaker-diarization-3.1 and pyannote/segmentation-3.0."
            )
        self._pipeline = pipeline.to(torch.device(device))

    def diarize(self, audio_path: str) -> list[SpeakerTurn]:
        """Run speaker diarization on *audio_path* and return speaker turns.

        The audio is decoded with soundfile and handed to the pipeline as an
        in-memory waveform, bypassing pyannote's optional torchcodec/ffmpeg
        decode path (brittle on Windows). Handles WAV/FLAC/OGG.
        """
        import soundfile as sf
        import torch

        data, sample_rate = sf.read(audio_path, dtype="float32", always_2d=True)
        waveform = torch.from_numpy(data.T)  # (channels, time)
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)  # downmix to mono
        output = self._pipeline(
            {"waveform": waveform, "sample_rate": sample_rate}
        )
        # pyannote 4.x returns a DiarizeOutput with a .speaker_diarization
        # Annotation; older 3.x returns the Annotation directly.
        annotation = getattr(output, "speaker_diarization", output)
        return _turns_from_diarization(annotation)
