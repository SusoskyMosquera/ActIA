# ActIA — Architecture Blueprint

> Consolidated view of the closed architectural decisions. For the reasoning
> behind each, see the ADRs in [`docs/adr/`](./adr).

## Decisions at a glance

| # | Decision | ADR |
|---|----------|-----|
| 1 | Asynchronous processing: job + polling, in-memory state, no DB/Redis | [ADR-0001](./adr/0001-async-processing-model.md) |
| 2 | Audio pipeline behind ports (hexagonal); managed cloud hosting frozen, swap-ready | [ADR-0002](./adr/0002-decoupled-audio-pipeline.md) |
| 3 | `faster-whisper` for transcription; pyannote.audio for diarization | [ADR-0003](./adr/0003-transcription-engine.md) |
| 4 | Minutes provider selectable — Gemini default, Ollama (OSS/local) option | [ADR-0004](./adr/0004-minutes-provider.md) |
| 5 | Analysis behind an `AudioAnalyzer` port; AssemblyAI / Speechmatics options for long meetings | [ADR-0005](./adr/0005-analysis-provider.md) |
| 6 | Containerized one-command run via Docker Compose (backend API + nginx frontend) | [ADR-0006](./adr/0006-containerized-deployment.md) |

## Processing pipeline

The use case depends on a single high-level port, `AudioAnalyzer`, which returns
speaker-attributed segments. How those segments are produced is the adapter's
concern (see [ADR-0005](./adr/0005-analysis-provider.md)):

```
upload audio
    │
    ▼
[1] analyze           AudioAnalyzer   → attributed segments
    │                                    (speaker, start, end, text)
    │
    │   local adapter  → transcribe (faster-whisper) ║ diarize (pyannote)
    │                    run in parallel, then attribute (pure domain,
    │                    max temporal overlap)
    │   hosted adapter → one call (AssemblyAI / Speechmatics) returns
    │                    the transcript already attributed
    ▼
[2] generate minutes  Gemini / Ollama → meeting minutes (markdown)
    │
    ▼
result
```

Each job moves through `PENDING → PROCESSING → DONE | ERROR | CANCELLED`,
exposing a `stage` of `ANALYZING | GENERATING_MINUTES` while it runs.
(`TRANSCRIBING` / `DIARIZING` remain as valid legacy values but the analyzer now
reports a single `ANALYZING` stage.)

## API contract (v1)

### `POST /api/v1/transcriptions`
Create a transcription job.

- **Body:** `multipart/form-data`
  - `file` (required) — audio file
  - `language` (optional, default `es` / auto)
  - `model_size` (optional, default `small`)
  - `num_speakers` (optional hint for diarization)
- **202 Accepted:**
  ```json
  { "job_id": "f1e2...", "status": "PENDING" }
  ```
- **Errors:** `400` invalid file type, `413` too large, `422` validation.

### `GET /api/v1/transcriptions/{job_id}`
Poll job status / fetch result.

- **200 OK:**
  ```json
  {
    "job_id": "f1e2...",
    "status": "DONE",
    "stage": null,
    "result": {
      "transcript": [
        { "speaker": "SPEAKER_00", "start": 0.0, "end": 4.2, "text": "..." }
      ],
      "minutes": "# Meeting minutes\n...",
      "metadata": {
        "duration_sec": 0.0,
        "language": "es",
        "num_speakers": 2,
        "model": "faster-whisper:small"
      }
    },
    "error": null
  }
  ```
- **404 Not Found:** unknown `job_id`.

### `GET /api/v1/health`
Liveness probe → `{ "status": "ok" }`.

## Layered structure (hexagonal)

Dependency direction points **inward**: `domain` depends on nothing;
`application` depends on `domain`; `infrastructure` and `api` depend on the
inner layers.

```
ActIA/
├── backend/
│   ├── app/
│   │   ├── domain/                      # entities, ports, pure logic — no deps
│   │   │   ├── models.py                # TranscriptSegment, SpeakerTurn, Job, Minutes
│   │   │   ├── ports.py                 # AudioAnalyzer, AudioTranscriber,
│   │   │   │                            #   SpeakerDiarizer, MinutesGenerator, JobStore
│   │   │   └── services/
│   │   │       └── speaker_attribution.py   # pure merge: segments × turns
│   │   ├── application/                 # use cases
│   │   │   └── generate_meeting_minutes.py
│   │   ├── infrastructure/              # adapters implementing the ports
│   │   │   ├── analysis/                # AudioAnalyzer implementations
│   │   │   │   ├── local_audio_analyzer.py     # whisper ║ pyannote, then attribute
│   │   │   │   ├── assemblyai_analyzer.py       # hosted (long meetings)
│   │   │   │   └── speechmatics_analyzer.py     # hosted (auto speaker detect)
│   │   │   ├── transcription/faster_whisper_transcriber.py
│   │   │   ├── diarization/pyannote_diarizer.py
│   │   │   ├── nlp/                     # MinutesGenerator implementations
│   │   │   │   ├── gemini_minutes_generator.py
│   │   │   │   └── ollama_minutes_generator.py
│   │   │   └── jobs/in_memory_job_store.py
│   │   ├── api/                         # thin FastAPI layer
│   │   │   ├── routes/transcriptions.py
│   │   │   ├── schemas.py               # pydantic request/response models
│   │   │   └── dependencies.py          # DI wiring
│   │   ├── workers/job_worker.py        # background job runner
│   │   ├── config.py                    # pydantic-settings
│   │   └── main.py                      # app factory + lifespan (load models once)
│   ├── tests/
│   ├── pyproject.toml
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/                  # presentational (dumb) components
│   │   ├── features/transcription/
│   │   │   ├── hooks/useTranscriptionJob.ts   # state + polling (logic)
│   │   │   ├── api/transcriptionClient.ts      # infrastructure (fetch)
│   │   │   └── TranscriptionContainer.tsx       # container (smart)
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
├── docs/
│   ├── ARCHITECTURE.md
│   └── adr/
└── README.md
```

### Why this shape

- **Routes are thin** (spec requirement): they validate input and delegate to a
  use case. No transcription or API logic in the route.
- **Ports + DI** (spec requirement): the use case depends on interfaces; adapters
  are injected, so the domain is unit-testable with fakes.
- **Speaker attribution is pure** domain logic — testable without any model.
- **Frontend** follows container/presentational + hooks (spec requirement):
  polling and state live in `useTranscriptionJob`; components only render.

## Running it

- **Docker (one command):** `docker compose up --build` brings up the backend
  API and the nginx-served frontend together — open `http://localhost:8080`. The
  image ships the light hosted providers by default; the heavy local ML stack is
  opt-in via a build arg. See [ADR-0006](./adr/0006-containerized-deployment.md).
- **Local dev:** run the backend (`uvicorn`) and frontend (`npm run dev`)
  separately — see the [README](../README.md) for the step-by-step.

Either way the app boots in **demo mode** (canned data, no keys, no ML);
`ADAPTER_MODE=real` plus provider settings switches on real processing.

## Setup gotcha (do not skip)

When running the **local** analysis provider, `pyannote.audio` requires a Hugging
Face account, acceptance of the gated
`pyannote/speaker-diarization-community-1` terms (the pyannote 4.x model), and a
HF access token read from configuration. A plain `pip install` will succeed but
fail at runtime without this. The hosted providers (AssemblyAI / Speechmatics)
need no HF token — only their own API key.
