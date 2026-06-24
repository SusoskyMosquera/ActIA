from __future__ import annotations
from app.domain.models import AttributedSegment, Minutes
from app.infrastructure.nlp.prompt import _build_prompt, _format_transcript


class GeminiMinutesGenerator:
    """Real minutes-generation adapter backed by Google Gemini (google-genai SDK).

    Uses the modern ``google-genai`` SDK (``from google import genai``), NOT the
    legacy ``google-generativeai`` package.  The API key is validated BEFORE any
    heavy import so the ValueError is testable without the SDK installed.
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
