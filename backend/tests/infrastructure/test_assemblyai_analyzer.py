from __future__ import annotations

"""CI-safe tests for AssemblyAI analyzer helpers (no SDK required)."""
import pytest

from app.infrastructure.analysis.assemblyai_analyzer import (
    AssemblyAIAudioAnalyzer,
    _speaker_label,
    _to_attributed,
)


# ---------------------------------------------------------------------------
# _speaker_label
# ---------------------------------------------------------------------------


def test_speaker_label_single_letters() -> None:
    assert _speaker_label("A") == "SPEAKER_00"
    assert _speaker_label("B") == "SPEAKER_01"
    assert _speaker_label("Z") == "SPEAKER_25"


def test_speaker_label_lowercase_treated_as_uppercase() -> None:
    assert _speaker_label("a") == "SPEAKER_00"
    assert _speaker_label("b") == "SPEAKER_01"


def test_speaker_label_non_single_letter_prefixed_verbatim() -> None:
    assert _speaker_label("SPKR1") == "SPEAKER_SPKR1"
    assert _speaker_label("12") == "SPEAKER_12"


# ---------------------------------------------------------------------------
# _to_attributed
# ---------------------------------------------------------------------------


class _FakeUtterance:
    """Minimal duck-type matching AssemblyAI's Utterance object."""

    def __init__(self, speaker: str, start: int, end: int, text: str) -> None:
        self.speaker = speaker
        self.start = start
        self.end = end
        self.text = text


def test_to_attributed_converts_ms_to_seconds() -> None:
    utterances = [
        _FakeUtterance(speaker="A", start=0, end=5000, text="Hello world"),
        _FakeUtterance(speaker="B", start=5000, end=10000, text="  How are you  "),
    ]
    result = _to_attributed(utterances)

    assert len(result) == 2
    assert result[0].start == 0.0
    assert result[0].end == 5.0
    assert result[0].text == "Hello world"
    assert result[0].speaker == "SPEAKER_00"

    assert result[1].start == 5.0
    assert result[1].end == 10.0
    assert result[1].text == "How are you"  # stripped
    assert result[1].speaker == "SPEAKER_01"


def test_to_attributed_empty_list() -> None:
    assert _to_attributed([]) == []


def test_to_attributed_none_returns_empty() -> None:
    assert _to_attributed(None) == []


# ---------------------------------------------------------------------------
# AssemblyAIAudioAnalyzer construction
# ---------------------------------------------------------------------------


def test_empty_api_key_raises_value_error() -> None:
    """ValueError must be raised BEFORE any SDK import when the key is empty."""
    with pytest.raises(ValueError, match="ASSEMBLYAI_API_KEY is required"):
        AssemblyAIAudioAnalyzer(api_key="")


def test_whitespace_only_api_key_raises_value_error() -> None:
    with pytest.raises(ValueError, match="ASSEMBLYAI_API_KEY is required"):
        AssemblyAIAudioAnalyzer(api_key="   ")


def test_valid_api_key_constructs_without_importing_sdk() -> None:
    """Construction with a valid key must succeed even if assemblyai is not installed."""
    analyzer = AssemblyAIAudioAnalyzer(api_key="fake-key-for-test", language="es")
    # We only check that the object is created; calling analyze() would require the SDK.
    assert analyzer._api_key == "fake-key-for-test"
    assert analyzer._language == "es"
