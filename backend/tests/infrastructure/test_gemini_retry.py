from __future__ import annotations
import pytest

from app.infrastructure.nlp.gemini_minutes_generator import (
    _MAX_ATTEMPTS,
    _call_with_retry,
    _is_retryable,
)


class _CodedError(Exception):
    """Mimics a google-genai APIError, which exposes an HTTP `.code`."""

    def __init__(self, code: int) -> None:
        super().__init__(f"HTTP {code}")
        self.code = code


def _no_sleep(_seconds: float) -> None:
    return None


def test_is_retryable_for_transient_codes() -> None:
    for code in (429, 500, 502, 503, 504):
        assert _is_retryable(_CodedError(code)) is True


def test_is_not_retryable_for_client_or_codeless_errors() -> None:
    assert _is_retryable(_CodedError(400)) is False
    assert _is_retryable(_CodedError(404)) is False
    assert _is_retryable(RuntimeError("no code attribute")) is False


def test_retries_then_succeeds_on_transient_failure() -> None:
    attempts = {"n": 0}

    def fn() -> str:
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise _CodedError(503)
        return "ok"

    assert _call_with_retry(fn, sleep=_no_sleep) == "ok"
    assert attempts["n"] == 3


def test_non_retryable_error_is_raised_immediately() -> None:
    attempts = {"n": 0}

    def fn() -> str:
        attempts["n"] += 1
        raise _CodedError(400)

    with pytest.raises(_CodedError):
        _call_with_retry(fn, sleep=_no_sleep)
    assert attempts["n"] == 1


def test_gives_up_after_max_attempts() -> None:
    attempts = {"n": 0}

    def fn() -> str:
        attempts["n"] += 1
        raise _CodedError(503)

    with pytest.raises(_CodedError):
        _call_with_retry(fn, sleep=_no_sleep)
    assert attempts["n"] == _MAX_ATTEMPTS
