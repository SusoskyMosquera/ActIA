# ADR-0003: Transcription engine — faster-whisper

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Project stakeholders

## Context

The spec describes a **lightweight** app and selects Whisper (OpenAI) for ASR
plus pyannote.audio for diarization. There are two mainstream ways to run
Whisper locally:

- `openai-whisper` — the reference PyTorch implementation.
- `faster-whisper` — a reimplementation on CTranslate2, substantially faster
  and lighter on memory for the same model weights.

Separately, `pyannote.audio` is **not** a plain `pip install`: it requires a
Hugging Face account, acceptance of the gated model terms for
`pyannote/speaker-diarization-community-1` (the pyannote 4.x pipeline), and a
HF access token at runtime.

## Decision

Use **`faster-whisper`** as the `AudioTranscriber` adapter.

- Model size is **configurable** (`tiny → large`), defaulting to `small` (or
  `base` on constrained machines) as a precision/speed balance for Spanish
  meetings.
- Language defaults to Spanish (`es`) but remains configurable / auto-detect.
- Diarization stays on `pyannote.audio` (`speaker-diarization-community-1`,
  pyannote 4.x); the HF token is read from configuration and required at runtime.
- Both `faster-whisper` and `pyannote` are encapsulated inside
  `LocalAudioAnalyzer` (see [ADR-0005](./0005-analysis-provider.md)). When a
  hosted analyzer (`assemblyai` or `speechmatics`) is selected, these local
  adapters are never loaded.

## Options Considered

### Option A: openai-whisper (reference)
| Dimension | Assessment |
|-----------|------------|
| Speed | Slower |
| Memory | Higher |
| Accuracy | Reference baseline |
| Maturity | Canonical |

**Pros:** Reference implementation; widest documentation.
**Cons:** Heavier RAM and slower — at odds with a "lightweight" app.

### Option B: faster-whisper (chosen)
| Dimension | Assessment |
|-----------|------------|
| Speed | Faster (CTranslate2) |
| Memory | Lower |
| Accuracy | Equivalent (same weights) |
| Maturity | Mature, widely used |

**Pros:** Less RAM, faster, same model quality; quantization options.
**Cons:** One more dependency to understand than the reference package.

## Trade-off Analysis

Both produce equivalent transcripts because they run the same Whisper weights;
faster-whisper simply executes them more efficiently. For an app explicitly
framed as lightweight, the lower memory footprint is the deciding factor. The
abstraction behind `AudioTranscriber` (ADR-0002) means this choice is reversible
without touching the domain.

## Consequences

- **Easier:** Lower memory and faster turnaround on commodity CPUs;
  configurable model size to trade accuracy for speed.
- **Harder:** Setup must document the pyannote HF token + gated-model acceptance
  (`speaker-diarization-community-1`), or runtime will fail despite a successful
  install. Only relevant for the `local` analyzer; hosted providers need no HF
  token.
- **To revisit:** Model size default may need tuning after testing on real
  Spanish meeting audio.

## Action Items

1. [x] Add `faster-whisper` as the transcription dependency.
2. [x] Expose `model_size` and `language` via configuration.
3. [x] Document HF token + `speaker-diarization-community-1` acceptance in setup/README.
4. [x] Both adapters encapsulated in `LocalAudioAnalyzer` (ADR-0005); hosted
       analyzers bypass them entirely.
5. [ ] Benchmark `base` vs `small` on representative Spanish audio (quality/speed
       trade-off not yet formally measured).
