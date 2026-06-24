from __future__ import annotations
from app.domain.models import AttributedSegment, Minutes


class GeminiMinutesGenerator:
    """Stub adapter for Gemini. Real implementation pending."""

    def generate(self, transcript: list[AttributedSegment]) -> Minutes:
        # Heavy imports kept inside the method so this module is safe to import
        # without google-generativeai installed.
        raise NotImplementedError("real adapter pending")
