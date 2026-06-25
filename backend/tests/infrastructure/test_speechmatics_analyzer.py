from __future__ import annotations
"""CI-safe tests for Speechmatics analyzer helpers (no SDK required)."""
import pytest

from app.infrastructure.analysis.speechmatics_analyzer import (
    SpeechmaticsAudioAnalyzer,
    _join_tokens,
    _speaker_label,
    _to_attributed,
)


# ---------------------------------------------------------------------------
# _speaker_label
# ---------------------------------------------------------------------------

def test_speaker_label_s1_maps_to_speaker_00() -> None:
    assert _speaker_label("S1") == "SPEAKER_00"


def test_speaker_label_s2_maps_to_speaker_01() -> None:
    assert _speaker_label("S2") == "SPEAKER_01"


def test_speaker_label_s10_maps_to_speaker_09() -> None:
    assert _speaker_label("S10") == "SPEAKER_09"


def test_speaker_label_non_sn_format_prefixed_verbatim() -> None:
    assert _speaker_label("UU") == "SPEAKER_UU"
    assert _speaker_label("SPKR") == "SPEAKER_SPKR"


def test_speaker_label_lowercase_s_treated_as_s_prefix() -> None:
    # "s1" starts with "S" (case-insensitive check) and digits after
    assert _speaker_label("s1") == "SPEAKER_00"


# ---------------------------------------------------------------------------
# _join_tokens
# ---------------------------------------------------------------------------

def test_join_tokens_words_separated_by_spaces() -> None:
    tokens = [("Hola", False), ("mundo", False)]
    assert _join_tokens(tokens) == "Hola mundo"


def test_join_tokens_punctuation_attached_without_space() -> None:
    tokens = [("Hola", False), (",", True), ("mundo", False)]
    assert _join_tokens(tokens) == "Hola, mundo"


def test_join_tokens_leading_punctuation_no_leading_space() -> None:
    tokens = [(",", True), ("mundo", False)]
    assert _join_tokens(tokens) == ", mundo"


def test_join_tokens_empty_list_returns_empty_string() -> None:
    assert _join_tokens([]) == ""


def test_join_tokens_single_word() -> None:
    assert _join_tokens([("Hola", False)]) == "Hola"


def test_join_tokens_trailing_punctuation() -> None:
    tokens = [("Hola", False), ("mundo", False), (".", True)]
    assert _join_tokens(tokens) == "Hola mundo."


# ---------------------------------------------------------------------------
# _to_attributed
# ---------------------------------------------------------------------------

def _word(speaker: str, start: float, end: float, content: str) -> dict:
    return {
        "type": "word",
        "start_time": start,
        "end_time": end,
        "alternatives": [{"content": content, "speaker": speaker}],
    }


def _punct(speaker: str, start: float, end: float, content: str) -> dict:
    return {
        "type": "punctuation",
        "start_time": start,
        "end_time": end,
        "alternatives": [{"content": content, "speaker": speaker}],
    }


def _speaker_change(start: float) -> dict:
    return {"type": "speaker_change", "start_time": start, "end_time": start}


def test_to_attributed_two_speakers_produce_two_segments() -> None:
    results = [
        _word("S1", 0.0, 1.0, "Hola"),
        _word("S1", 1.0, 2.0, "mundo"),
        _word("S2", 3.0, 4.0, "Adios"),
    ]
    segments = _to_attributed(results)

    assert len(segments) == 2
    assert segments[0].speaker == "SPEAKER_00"
    assert segments[0].start == 0.0
    assert segments[0].end == 2.0
    assert segments[0].text == "Hola mundo"

    assert segments[1].speaker == "SPEAKER_01"
    assert segments[1].start == 3.0
    assert segments[1].end == 4.0
    assert segments[1].text == "Adios"


def test_to_attributed_speaker_change_items_are_skipped() -> None:
    results = [
        _word("S1", 0.0, 1.0, "Hola"),
        _speaker_change(1.5),
        _word("S2", 2.0, 3.0, "Mundo"),
    ]
    segments = _to_attributed(results)
    # speaker_change has no alternatives so it's skipped; we still get two segments
    assert len(segments) == 2
    assert segments[0].speaker == "SPEAKER_00"
    assert segments[1].speaker == "SPEAKER_01"


def test_to_attributed_punctuation_attaches_without_space() -> None:
    results = [
        _word("S1", 0.0, 1.0, "Hola"),
        _punct("S1", 1.0, 1.0, ","),
        _word("S1", 1.5, 2.5, "mundo"),
        _punct("S1", 2.5, 2.5, "."),
    ]
    segments = _to_attributed(results)

    assert len(segments) == 1
    assert segments[0].text == "Hola, mundo."
    assert segments[0].start == 0.0
    assert segments[0].end == 2.5


def test_to_attributed_empty_results_returns_empty_list() -> None:
    assert _to_attributed([]) == []


def test_to_attributed_none_returns_empty_list() -> None:
    assert _to_attributed(None) == []


def test_to_attributed_start_from_first_item_end_from_last_per_run() -> None:
    results = [
        _word("S1", 1.0, 2.0, "uno"),
        _word("S1", 2.5, 3.5, "dos"),
        _word("S2", 4.0, 5.0, "tres"),
        _word("S2", 5.5, 6.5, "cuatro"),
    ]
    segments = _to_attributed(results)

    assert segments[0].start == 1.0
    assert segments[0].end == 3.5
    assert segments[1].start == 4.0
    assert segments[1].end == 6.5


def test_to_attributed_items_without_alternatives_are_skipped() -> None:
    results = [
        {"type": "word", "start_time": 0.0, "end_time": 1.0, "alternatives": []},
        _word("S1", 1.0, 2.0, "Hola"),
    ]
    segments = _to_attributed(results)
    assert len(segments) == 1
    assert segments[0].text == "Hola"


# ---------------------------------------------------------------------------
# SpeechmaticsAudioAnalyzer construction
# ---------------------------------------------------------------------------

def test_empty_api_key_raises_value_error() -> None:
    """ValueError must be raised BEFORE any SDK import when the key is empty."""
    with pytest.raises(ValueError, match="SPEECHMATICS_API_KEY is required"):
        SpeechmaticsAudioAnalyzer(api_key="")


def test_whitespace_only_api_key_raises_value_error() -> None:
    with pytest.raises(ValueError, match="SPEECHMATICS_API_KEY is required"):
        SpeechmaticsAudioAnalyzer(api_key="   ")


def test_valid_api_key_constructs_without_importing_sdk() -> None:
    """Construction with a valid key must succeed even if speechmatics is not installed."""
    analyzer = SpeechmaticsAudioAnalyzer(api_key="fake-key-for-test", language="es")
    assert analyzer._api_key == "fake-key-for-test"
    assert analyzer._language == "es"


def test_auto_language_falls_back_to_spanish() -> None:
    analyzer = SpeechmaticsAudioAnalyzer(api_key="fake-key", language="auto")
    assert analyzer._language == "es"


def test_explicit_language_is_preserved() -> None:
    analyzer = SpeechmaticsAudioAnalyzer(api_key="fake-key", language="en")
    assert analyzer._language == "en"


def test_analyze_bubbles_up_clear_speechmatics_error(monkeypatch) -> None:
    import httpx

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def submit_job(self, *args, **kwargs):
            request = httpx.Request("POST", "https://asr.api.speechmatics.com/v2/jobs")
            response = httpx.Response(
                status_code=400,
                request=request,
                json={"code": 400, "detail": "Languagepack 'invalid_lang' is not supported", "error": "Requested product not available"}
            )
            raise httpx.HTTPStatusError("Client error '400 Bad Request'", request=request, response=response)

    monkeypatch.setattr("speechmatics.batch_client.BatchClient", MockClient)

    analyzer = SpeechmaticsAudioAnalyzer(api_key="fake-key", language="es")
    with pytest.raises(ValueError, match="Languagepack 'invalid_lang' is not supported"):
        analyzer.analyze("dummy_path.wav")


def test_analyze_handles_malformed_error_response(monkeypatch) -> None:
    import httpx

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def submit_job(self, *args, **kwargs):
            request = httpx.Request("POST", "https://asr.api.speechmatics.com/v2/jobs")
            response = httpx.Response(
                status_code=500,
                request=request,
                content=b"Internal Server Error (Plain Text)"
            )
            raise httpx.HTTPStatusError("Server error '500 Internal Server Error'", request=request, response=response)

    monkeypatch.setattr("speechmatics.batch_client.BatchClient", MockClient)

    analyzer = SpeechmaticsAudioAnalyzer(api_key="fake-key", language="es")
    with pytest.raises(ValueError, match="Internal Server Error"):
        analyzer.analyze("dummy_path.wav")


def test_analyze_transcodes_webm_to_wav(monkeypatch) -> None:
    import subprocess

    called_args = []

    def mock_run(args, **kwargs):
        called_args.append(args)
        return subprocess.CompletedProcess(args, 0)

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
        def submit_job(self, audio, *args, **kwargs):
            assert audio.endswith(".wav")
            return "mock-job-id"
        def wait_for_completion(self, *args, **kwargs):
            return {"results": []}

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr("speechmatics.batch_client.BatchClient", MockClient)

    analyzer = SpeechmaticsAudioAnalyzer(api_key="fake-key", language="es")
    analyzer.analyze("test_recording.webm")

    assert len(called_args) == 1
    assert called_args[0][0].lower().endswith("ffmpeg") or called_args[0][0].lower().endswith("ffmpeg.exe")
    assert called_args[0][3] == "test_recording.webm"
    assert called_args[0][8].endswith(".wav")

