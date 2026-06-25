# ActIA

A lightweight, open-source web application that turns meeting recordings into structured minutes (**actas**). It transcribes the audio, performs speaker diarization, and generates a structured summary.

Stateless by design—no user accounts, no database, no persistence. Upload an audio file and get the results directly on the screen.

## Pipeline Workflow

```
upload audio → transcribe → diarize → attribute speakers → generate minutes → acta
```

- **Backend:** FastAPI implementing a clean hexagonal architecture. Async jobs are managed in-memory with client polling.
- **Frontend:** React + TypeScript using a container/presentational split. All logic is encapsulated in the `useTranscriptionJob` hook.
- **Audio Analysis:** The `AudioAnalyzer` adapter supports local processing (`faster-whisper` + `pyannote.audio` in parallel) or hosted APIs (`assemblyai` / `speechmatics`).
- **Minutes Generation:** The `MinutesGenerator` adapter supports `gemini` (hosted) or `ollama` (fully local and private).
- **Export:** Browser-side generation of Markdown, Word (.docx) files, or copy to clipboard.

Detailed architecture decisions are documented in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and the ADRs under [docs/adr/](docs/adr).

## Running the App

### 1. Docker Compose (Quickest Setup)
Run the entire application (FastAPI backend + Nginx frontend) with a single command:

```bash
docker compose up --build
```

Access the app at **http://localhost:8080** (API docs at `http://localhost:8000/docs`).

By default, the app runs in **demo mode** (uses canned mock data so you do not need ML dependencies or API keys). To run real processing, see [Real Processing Setup](#real-processing-setup).

### 2. Manual Development Setup

#### Prerequisites
- Python 3.11+
- Node.js 18+

#### Backend Setup
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```
The API is available at `http://localhost:8000` (docs at `http://localhost:8000/docs`).

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`. The dev server automatically proxies `/api` to the backend.

## Configuration

Copy `backend/.env.example` to `backend/.env` and adjust the variables.

| Variable | Default | Description |
|----------|---------|-------------|
| `ADAPTER_MODE` | `demo` | `demo` (canned mock data) or `real` (actual ML + LLM processing) |
| `DEMO_DELAY_SECONDS` | `1.5` | Delay per stage in demo mode to visualize UI progress |
| `ANALYSIS_PROVIDER` | `local` | `local` (faster-whisper + pyannote), `assemblyai`, or `speechmatics` |
| `MINUTES_PROVIDER` | `gemini` | `gemini` or `ollama` |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model ID |
| `GEMINI_API_KEY` | — | Google AI Studio API key |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5:3b` | Local model ID |
| `HUGGINGFACE_TOKEN` | — | Required for pyannote in `local` analysis mode |
| `ASSEMBLYAI_API_KEY` | — | Required for `assemblyai` analysis mode |
| `SPEECHMATICS_API_KEY` | — | Required for `speechmatics` analysis mode |
| `LANGUAGE` | `es` | Transcription language (`es`, `en`, or `auto`) |

## Real Processing Setup

To transition from demo mode to real audio processing:

1. **Install Dependencies:**
   - For **local processing** (`faster-whisper` + `pyannote.audio`):
     ```bash
     pip install -e ".[dev,ml,nlp]"
     ```
   - For **hosted API processing** (`assemblyai` or `speechmatics`):
     ```bash
     pip install -e ".[dev,nlp,hosted]"
     ```

2. **Diarization Setup (Local mode only):**
   - Create a Hugging Face account and accept terms for the model [pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1).
   - Generate a HF read token and set it in `HUGGINGFACE_TOKEN`.

3. **Minutes Generation Setup:**
   - **Gemini (Hosted):** Set `GEMINI_API_KEY` with a key from Google AI Studio.
   - **Ollama (Local):** Run `ollama pull qwen2.5:3b` and set `MINUTES_PROVIDER=ollama`.

4. **Hosted Analyzers (Optional - for long meetings):**
   - **AssemblyAI:** Set `ANALYSIS_PROVIDER=assemblyai` and configure `ASSEMBLYAI_API_KEY`.
   - **Speechmatics:** Set `ANALYSIS_PROVIDER=speechmatics` and configure `SPEECHMATICS_API_KEY`.

## Running Tests

```bash
# Backend tests
cd backend && pytest

# Frontend tests and type check
cd frontend
npm test
npx tsc --noEmit
```

## Project Layout

```
ActIA/
├── backend/    # FastAPI server (Domain, Application, Infrastructure, API layers)
├── frontend/   # React + TypeScript client (Components, hooks, api)
└── docs/       # Architecture documents and Architecture Decision Records (ADRs)
```

## Project Status

- [x] Architecture closed (ADRs) and documented
- [x] Backend skeleton (hexagonal) with tests
- [x] Frontend skeleton (container/presentational + hooks) with tests
- [x] Demo adapters — full pipeline runs end-to-end
- [x] Real local adapters (faster-whisper / pyannote / Gemini + Ollama)
- [x] Hosted analyzers (AssemblyAI + Speechmatics) behind `AudioAnalyzer` port
- [x] One-command run via Docker Compose (backend API + Nginx frontend)
- [x] File type/size validation (`400`/`413`) and periodic job cleanup
- [ ] Managed cloud hosting
