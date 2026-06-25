FROM python:3.12-slim

# ffmpeg improves audio-format support for the local (whisper/pyannote) pipeline.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Which optional extras to install. Default: the light hosted/NLP clients
# (Gemini, Ollama, AssemblyAI, Speechmatics). Add "ml" to also install the heavy
# local stack (faster-whisper + pyannote + torch), e.g.:
#   docker compose build --build-arg INSTALL_EXTRAS="nlp,hosted,ml"
ARG INSTALL_EXTRAS="nlp,hosted"

COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir -e ".[${INSTALL_EXTRAS}]"

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
