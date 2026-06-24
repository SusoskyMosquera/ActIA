from __future__ import annotations
import pytest

from app.infrastructure.diarization.pyannote_diarizer import PyannoteDiarizer
from app.infrastructure.nlp.gemini_minutes_generator import GeminiMinutesGenerator


def test_pyannote_requires_hf_token() -> None:
    """Validation must fire before any heavy pyannote import."""
    with pytest.raises(ValueError, match="HUGGINGFACE_TOKEN"):
        PyannoteDiarizer(hf_token="   ", model_name="pyannote/x", device="cpu")


def test_gemini_requires_api_key() -> None:
    """Validation must fire before any google-genai import."""
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        GeminiMinutesGenerator(api_key="", model_name="gemini-2.5-flash")
