# ADR-0005: Analysis behind an AudioAnalyzer port; hosted AssemblyAI option for long meetings

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Project stakeholders

## Context

The local pipeline (faster-whisper + pyannote on CPU) does not scale to long
recordings. Verified on real audio: diarization runs ~3× slower than realtime,
so a 2-hour meeting would take 6–8 hours of processing — unusable.

The bottleneck is **diarization**, not transcription:

- Transcription is cheap to offload — [Groq runs the same `large-v3-turbo` at
  ~228× realtime](https://groq.com/blog/whisper-large-v3-turbo-now-available-on-groq-combining-speed-quality-for-speech-recognition)
  (1 hour of audio in ~16 s) — but Groq does not diarize.
- pyannote on CPU is the killer. To make long meetings usable, diarization must
  be offloaded too.

Hosted speech APIs do transcription **and** diarization in one call and handle
multi-hour audio server-side in minutes, with generous free tiers
([AssemblyAI: 185 h free](https://www.assemblyai.com/pricing);
[Deepgram: $200 credit](https://deepgram.com/pricing)).

A complication: a hosted API returns the transcript already attributed to
speakers, which does not fit the two separate ports (`AudioTranscriber` +
`SpeakerDiarizer`) the local pipeline uses.

## Decision

Introduce a higher-level port **`AudioAnalyzer`** that yields speaker-attributed
segments directly:

```python
class AudioAnalyzer(Protocol):
    def analyze(self, audio_path: str) -> list[AttributedSegment]: ...
```

Two implementations, selectable via `ANALYSIS_PROVIDER`:

- **`LocalAudioAnalyzer`** (`local`, default) — wraps the existing transcriber +
  diarizer, runs them in parallel, and merges with the pure attribution logic.
  The parallel/attribution orchestration moves out of the use case into here.
- **`AssemblyAIAudioAnalyzer`** (`assemblyai`) — one hosted call does
  transcription + diarization; maps utterances to attributed segments. For long
  meetings. The local models are never loaded in this mode.

The use case now depends on the single `AudioAnalyzer` port (simpler, fully
provider-agnostic). The domain is untouched.

## Options Considered

| Option | Long-meeting time | Open / local / private | Cost |
|---|---|---|---|
| Local only (CPU) | 6–8 h for 2 h audio | yes | free — but unusable |
| GPU (local/cloud) | ~10–30 min | yes | hardware or ~$0.2–0.5/h |
| Hosted API — AssemblyAI (chosen) | minutes | no (data leaves) | free tier, then ~$0.15/h |
| Chunking + multi-core | ~1–2 h | yes | free, but complex (speaker stitching) and still slow |

## Trade-off Analysis

For multi-hour meetings there is no fast, fully-local CPU option. The hosted API
makes them usable in minutes for the least effort, at the cost of sending audio
to a third party (consistent with the earlier choice of hosted Gemini for
minutes). Keeping it **selectable** preserves the private/local path for short
or confidential meetings, and the `AudioAnalyzer` port means swapping engines
never touches the domain (the payoff of ADR-0002).

## Consequences

- **Easier:** Long meetings become usable; the use case is simpler and
  provider-agnostic; a GPU or Groq path can be added later as new analyzers.
- **Harder:** One more provider/dependency; the AssemblyAI path sends audio to
  the cloud (privacy) and depends on its free-tier limits.
- **To revisit:** A GPU `LocalAudioAnalyzer` (`DEVICE=cuda`) keeps long meetings
  local if hardware is available; a Groq transcription analyzer could be paired
  with hosted diarization.

## Action Items

1. [x] `AudioAnalyzer` port + use-case refactor to depend on it.
2. [x] `LocalAudioAnalyzer` (parallel whisper + pyannote) and
       `AssemblyAIAudioAnalyzer` (hosted).
3. [x] `ANALYSIS_PROVIDER` setting + DI wiring (assemblyai never loads local models).
4. [x] CI-safe unit tests (local parallelism/attribution; AssemblyAI mapping + validation).
5. [ ] First real run against AssemblyAI on a long recording.
