from __future__ import annotations
from app.domain.models import AttributedSegment

_PROMPT_TEMPLATE_ES = """\
You are an expert meeting-minutes (acta de reunión) writer.

Given the transcript below — where each line is "SPEAKER_LABEL: spoken text" — \
produce structured meeting minutes in Markdown, written in the SAME language as \
the transcript (Spanish when the transcript is in Spanish).

Use exactly these sections (if a section has no content write "Sin elementos"):

# Acta de Reunión
## Resumen
## Temas tratados
## Decisiones
## Compromisos / Action items
(include the responsible party when inferable from context)
## Próximos pasos

Rules:
- Be faithful to the transcript; do NOT invent information.
- Use a formal and concise tone.
- Avoid repeating verbatim quotes; synthesize instead.

Transcript:
{dialogue}
"""

_PROMPT_TEMPLATE_EN = """\
You are an expert meeting-minutes writer.

Given the transcript below — where each line is "SPEAKER_LABEL: spoken text" — \
produce structured meeting minutes in Markdown, written in the SAME language as \
the transcript (English when the transcript is in English).

Use exactly these sections (if a section has no content write "None"):

# Meeting Minutes
## Summary
## Topics discussed
## Decisions
## Action items
(include the responsible party when inferable from context)
## Next steps

Rules:
- Be faithful to the transcript; do NOT invent information.
- Use a formal and concise tone.
- Avoid repeating verbatim quotes; synthesize instead.

Transcript:
{dialogue}
"""


def _format_transcript(transcript: list[AttributedSegment]) -> str:
    """Render attributed segments as "SPEAKER_LABEL: text" lines (pure)."""
    return "\n".join(f"{seg.speaker}: {seg.text}" for seg in transcript)


def _build_prompt(dialogue: str, language: str = "es") -> str:
    """Wrap a pre-formatted dialogue string in the acta prompt template (pure)."""
    template = _PROMPT_TEMPLATE_ES if language == "es" else _PROMPT_TEMPLATE_EN
    return template.format(dialogue=dialogue)


def build_minutes_prompt(
    transcript: list[AttributedSegment],
    language: str = "es",
) -> str:
    """Build the LLM prompt for generating meeting minutes.

    Parameters
    ----------
    transcript:
        The attributed transcript produced by the speaker-attribution step.
    language:
        ISO 639-1 language code.  ``"es"`` (default) uses the Spanish
        template; anything else falls back to the English template.

    Returns
    -------
    str
        A ready-to-send prompt string — used by both the Gemini and Ollama
        adapters.  Pure function; no side effects.
    """
    return _build_prompt(_format_transcript(transcript), language)
