from __future__ import annotations
from app.domain.models import AttributedSegment, Minutes
from app.infrastructure.nlp.prompt import build_minutes_prompt


class OllamaMinutesGenerator:
    """Real minutes-generation adapter backed by a local Ollama instance.

    Selected when ``MINUTES_PROVIDER=ollama``.  The ``ollama`` package import
    and client construction happen in ``__init__`` (lazy, import-safe in demo
    mode).  No API key required — Ollama is self-hosted.

    Install and pull the model before use::

        pip install ollama
        ollama pull qwen2.5:3b   # or whatever OLLAMA_MODEL is set to
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = "qwen2.5:3b",
    ) -> None:
        import ollama  # lazy import

        self._client = ollama.Client(host=base_url)
        self._model_name = model_name

    def generate(self, transcript: list[AttributedSegment]) -> Minutes:
        """Generate meeting minutes by sending the prompt to a local Ollama model."""
        prompt = build_minutes_prompt(transcript)
        response = self._client.chat(
            model=self._model_name,
            messages=[{"role": "user", "content": prompt}],
        )
        content: str = response["message"]["content"]
        return Minutes(content=content)
