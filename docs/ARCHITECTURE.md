# ActIA — Architecture Blueprint

> Consolidated view of the closed architectural decisions. For the reasoning
> behind each, see the ADRs in [`docs/adr/`](./adr).

## Decisions at a glance

| # | Decision | ADR |
|---|----------|-----|
| 1 | Asynchronous processing: job + polling, in-memory state, no DB/Redis | [ADR-0001](./adr/0001-async-processing-model.md) |
| 2 | Audio pipeline behind ports (hexagonal); deployment frozen, swap-ready | [ADR-0002](./adr/0002-decoupled-audio-pipeline.md) |
| 3 | `faster-whisper` for transcription; pyannote.audio for diarization | [ADR-0003](./adr/0003-transcription-engine.md) |
| 4 | Minutes provider selectable — Gemini default, Ollama (OSS/local) option | [ADR-0004](./adr/0004-minutes-provider.md) |
| 5 | Analysis behind an `AudioAnalyzer` port; AssemblyAI option for long meetings | [ADR-0005](./adr/0005-analysis-provider.md) |

## Processing pipeline

```
upload audio
    │
    ▼
[1] transcribe        faster-whisper  → segments (start, end, text)
    │
    ▼
[2] diarize           pyannote.audio  → speaker turns (start, end, speaker)
    │
    ▼
[3] attribute         pure domain     → each segment gets a speaker
    │                                    (max temporal overlap)
    ▼
[4] generate minutes  Gemini          → meeting minutes (markdown)
    │
    ▼
result
```

Each job moves through `PENDING → PROCESSING → DONE | ERROR`, exposing a
`stage` of `transcribing | diarizing | generating_minutes` during step 1–4.

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
│   │   │   ├── ports.py                 # AudioTranscriber, SpeakerDiarizer,
│   │   │   │                            #   MinutesGenerator, JobStore
│   │   │   └── services/
│   │   │       └── speaker_attribution.py   # pure merge: segments × turns
│   │   ├── application/                 # use cases
│   │   │   └── generate_meeting_minutes.py
│   │   ├── infrastructure/              # adapters implementing the ports
│   │   │   ├── transcription/faster_whisper_transcriber.py
│   │   │   ├── diarization/pyannote_diarizer.py
│   │   │   ├── nlp/gemini_minutes_generator.py
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

## Setup gotcha (do not skip)

`pyannote.audio` requires a Hugging Face account, acceptance of the gated
`pyannote/speaker-diarization-3.1` terms, and a HF access token read from
configuration. A plain `pip install` will succeed but fail at runtime without
this.
