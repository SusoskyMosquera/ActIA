from __future__ import annotations
import time
from typing import Callable, TypeVar

from app.domain.models import AttributedSegment, Minutes
from app.infrastructure.nlp.prompt import _build_prompt, _format_transcript

_T = TypeVar("_T")

# Transient HTTP statuses worth retrying: rate limiting (429) and server
# overload / 5xx — e.g. Gemini's "503 UNAVAILABLE: high demand".
_RETRYABLE_CODES = frozenset({429, 500, 502, 503, 504})
_MAX_ATTEMPTS = 4
_BACKOFF_BASE_S = 2.0


def _is_retryable(exc: Exception) -> bool:
    """A google-genai APIError carries an HTTP ``.code``; retry transient ones."""
    return getattr(exc, "code", None) in _RETRYABLE_CODES


def _call_with_retry(
    fn: Callable[[], _T],
    sleep: Callable[[float], None] = time.sleep,
) -> _T:
    """Call ``fn``, retrying transient API errors with exponential backoff."""
    for attempt in range(_MAX_ATTEMPTS):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001
            if _is_retryable(exc) and attempt < _MAX_ATTEMPTS - 1:
                sleep(_BACKOFF_BASE_S * (2**attempt))
                continue
            raise
    raise RuntimeError("unreachable")  # pragma: no cover


class GeminiMinutesGenerator:
    """Real minutes-generation adapter backed by Google Gemini (google-genai SDK).

    Uses the modern ``google-genai`` SDK (``from google import genai``), NOT the
    legacy ``google-generativeai`` package.  The API key is validated BEFORE any
    heavy import so the ValueError is testable without the SDK installed.

    Transient errors (HTTP 429 / 5xx, e.g. "503 UNAVAILABLE: high demand") are
    retried with exponential backoff before the job is failed.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash") -> None:
        if not api_key.strip():
            raise ValueError(
                "GEMINI_API_KEY is required for the Gemini minutes provider."
            )

        from google import genai  # lazy heavy import

        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    def generate(self, transcript: list[AttributedSegment]) -> Minutes:
        """Generate meeting minutes from an attributed transcript via Gemini."""
        prompt = _build_prompt(_format_transcript(transcript))

        def _call() -> Minutes:
            response = self._client.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )
            text: str | None = getattr(response, "text", None)
            if not text:
                raise RuntimeError(
                    "Gemini returned an empty response (possibly blocked by safety filters)."
                )
            return Minutes(content=text.strip())

        return _call_with_retry(_call)
