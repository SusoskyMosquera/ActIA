# ActIA

Lightweight, open-source web app that turns a meeting recording into **meeting
minutes (acta)**: it transcribes the audio, separates who said what (speaker
diarization), and generates a structured summary.

Stateless by design — no accounts, no database, no persistence. Upload an audio
file, get the result on the same screen.

## How it works

```
upload audio → transcribe → diarize → attribute speakers → generate minutes → acta
```

- **Backend:** FastAPI, hexagonal architecture. Async job model — upload returns
  a `job_id`, the client polls for the result. Heavy work runs off the event
  loop on a single worker.
- **Frontend:** React + TypeScript. Container/presentational split — all logic
  lives in the `useTranscriptionJob` hook; components only render.
- **Processing:** `faster-whisper` (transcription) + `pyannote.audio`
  (diarization) + minutes via **Gemini or a local LLM through Ollama**
  (selectable). These are pluggable adapters behind domain ports, so they can be
  swapped without touching the core.

Architecture decisions are documented in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
and the ADRs under [`docs/adr/`](docs/adr).

## Demo mode (runs out of the box)

By default the backend runs with **demo adapters** that return canned data — so
you can run the whole app end-to-end **without** installing the heavy ML stack
or any API keys. Switch to real processing by setting `ADAPTER_MODE=real`.

## Prerequisites

- Python 3.11+
- Node.js 18+

## Quick start

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

The API is now on `http://localhost:8000` (docs at `/docs`). Demo mode is the
default — no extra setup needed.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The dev server proxies `/api` to the backend.
Upload any audio file and watch the pipeline run to a rendered acta.

## Configuration

Copy `backend/.env.example` to `backend/.env` and adjust as needed.

| Variable | Default | Purpose |
|----------|---------|---------|
| `ADAPTER_MODE` | `demo` | `demo` (canned data) or `real` (actual ML + LLM) |
| `DEMO_DELAY_SECONDS` | `1.5` | Per-stage delay in demo mode so the UI shows progress |
| `MODEL_SIZE` | `small` | faster-whisper model size (real mode) |
| `LANGUAGE` | `es` | Transcription language (`es`, `en`, … or `auto`) |
| `DEVICE` | `cpu` | `cpu` or `cuda` for whisper + pyannote |
| `COMPUTE_TYPE` | `int8` | faster-whisper compute type (`int8` CPU, `float16` GPU) |
| `DIARIZATION_MODEL` | `pyannote/speaker-diarization-community-1` | pyannote 4.x pipeline (real mode) |
| `HUGGINGFACE_TOKEN` | — | Required for pyannote in real mode (see below) |
| `MINUTES_PROVIDER` | `gemini` | `gemini` (hosted) or `ollama` (local, OSS, private) |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model id (`gemini-2.5-flash` recommended) |
| `GEMINI_API_KEY` | — | Required when `MINUTES_PROVIDER=gemini` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama server (`MINUTES_PROVIDER=ollama`) |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Local model id (`MINUTES_PROVIDER=ollama`) |
| `JOB_TTL_SECONDS` | `3600` | In-memory job retention before cleanup |

## Switching to real processing

1. Install the heavy extras:
   ```bash
   pip install -e ".[dev,ml,nlp]"
   ```
2. **Hugging Face / pyannote (diarization):** create a HF account, generate a read
   token, and accept the gated terms for
   `pyannote/speaker-diarization-community-1` (the pyannote 4.x model). Put the
   token in `HUGGINGFACE_TOKEN`. A plain install will succeed but fail at runtime
   without this.
3. **Minutes provider — pick one:**
   - **Gemini** (default, best quality, generous free tier): put your Google AI
     Studio key in `GEMINI_API_KEY`. Caveat: on the free tier Google may use your
     data to train its models — avoid for confidential meetings (or use Ollama).
   - **Ollama** (fully local, open-source, private — nothing leaves your machine):
     set `MINUTES_PROVIDER=ollama`, install [Ollama](https://ollama.com/download),
     and run `ollama pull qwen2.5:3b`.
4. Set `ADAPTER_MODE=real` and restart the backend.

> Note: the real models need real RAM/CPU (ideally a GPU) and will not run on
> free deployment tiers. On CPU, diarization runs ~3× slower than realtime, so a
> 10-minute recording can take 30+ minutes — use short audio or a GPU. The UI
> poll cap is `VITE_MAX_POLL_MINUTES` (default 45). Deployment is intentionally
> frozen — see [ADR-0002](docs/adr/0002-decoupled-audio-pipeline.md).

## Running tests

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test          # vitest
cd frontend && npx tsc --noEmit  # type-check
```

## Project layout

```
ActIA/
├── backend/    FastAPI app (domain / application / infrastructure / api)
├── frontend/   React + TS app (components + features/transcription)
└── docs/       ARCHITECTURE.md + ADRs
```

## Status

- [x] Architecture closed (ADRs) and documented
- [x] Backend skeleton (hexagonal) with tests
- [x] Frontend skeleton (container/presentational + hooks) with tests
- [x] Demo adapters — full pipeline runs end-to-end
- [x] Real adapters implemented (faster-whisper / pyannote / Gemini + Ollama) — pending first run with real models/keys
- [ ] File type/size validation (`400`/`413`) and periodic job cleanup
- [ ] Deployment (frozen pending stakeholder approval)
