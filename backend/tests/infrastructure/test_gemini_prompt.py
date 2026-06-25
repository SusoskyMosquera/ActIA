from __future__ import annotations
from app.domain.models import AttributedSegment
from app.infrastructure.nlp.gemini_minutes_generator import (
    _build_prompt,
    _format_transcript,
)


def test_format_transcript_joins_speaker_lines() -> None:
    transcript = [
        AttributedSegment(
            start=0.0, end=1.0, text="Hola a todos", speaker="SPEAKER_00"
        ),
        AttributedSegment(start=1.0, end=2.0, text="Buenos días", speaker="SPEAKER_01"),
    ]

    assert _format_transcript(transcript) == (
        "SPEAKER_00: Hola a todos\nSPEAKER_01: Buenos días"
    )


def test_format_transcript_empty_is_empty_string() -> None:
    assert _format_transcript([]) == ""


def test_build_prompt_embeds_dialogue_and_requests_acta_sections() -> None:
    prompt = _build_prompt("SPEAKER_00: hola")

    assert "SPEAKER_00: hola" in prompt
    assert "# Acta de Reunión" in prompt
    assert "## Compromisos" in prompt
