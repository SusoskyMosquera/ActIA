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

        pipeline = Pipeline.from_pretrained(model_name, use_auth_token=hf_token)
        # from_pretrained returns None (instead of raising) when the token is
        # invalid or the gated terms were not accepted — make that explicit.
        if pipeline is None:
            raise RuntimeError(
                f"Could not load '{model_name}'. Verify the HF token is valid and "
                "that you accepted the gated model terms on Hugging Face."
            )
        self._pipeline = pipeline.to(torch.device(device))

    def diarize(self, audio_path: str) -> list[SpeakerTurn]:
        """Run speaker diarization on *audio_path* and return speaker turns."""
        annotation = self._pipeline(audio_path)
        return _turns_from_diarization(annotation)
