# ADR-0005: Analysis behind an AudioAnalyzer port; hosted AssemblyAI / Speechmatics options for long meetings

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
multi-hour audio server-side in minutes. Their free offers differ in an
important way:

- **AssemblyAI** — a **one-time** sign-up credit (~$50), *not* a recurring
  monthly allowance. Good to evaluate the quality; it runs out and does not
  renew.
- **Speechmatics** — a **recurring** free tier of ~480 min/month, and it
  **auto-detects** the number of speakers (no fixed count to configure).

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

Three implementations, selectable via `ANALYSIS_PROVIDER`:

- **`LocalAudioAnalyzer`** (`local`, default) — wraps the existing transcriber +
  diarizer, runs them in parallel, and merges with the pure attribution logic.
  The parallel/attribution orchestration moves out of the use case into here.
- **`AssemblyAIAudioAnalyzer`** (`assemblyai`) — one hosted call does
  transcription + diarization; maps utterances to attributed segments. For long
  meetings. Accepts an optional `speakers_expected` hint (default `0` = auto).
- **`SpeechmaticsAudioAnalyzer`** (`speechmatics`) — hosted batch API that
  auto-detects the speaker count; groups word items by speaker into attributed
  segments. Recurring free tier.

In both hosted modes the local faster-whisper / pyannote models are never loaded.
The use case depends on the single `AudioAnalyzer` port (simpler, fully
provider-agnostic). The domain is untouched.

**On speaker count:** we deliberately do **not** hardcode it. `local` and
`speechmatics` auto-detect; `assemblyai` auto-detects too but accepts an optional
hint when the operator already knows the count. Versatility over a fixed
assumption.

## Options Considered

| Option | Long-meeting time | Open / local / private | Cost |
|---|---|---|---|
| Local only (CPU) | 6–8 h for 2 h audio | yes | free — but unusable |
| GPU (local/cloud) | ~10–30 min | yes | hardware or ~$0.2–0.5/h |
| Hosted API — AssemblyAI (chosen) | minutes | no (data leaves) | one-time ~$50 credit, then ~$0.15/h |
| Hosted API — Speechmatics (chosen) | minutes | no (data leaves) | recurring ~480 min/month free, then paid |
| Chunking + multi-core | ~1–2 h | yes | free, but complex (speaker stitching) and still slow |

Both hosted providers were kept rather than one: AssemblyAI is a strong baseline
but its free credit is one-time, while Speechmatics gives a recurring monthly
allowance and auto speaker detection — a better fit for ongoing use.

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
- **Harder:** Two more providers/dependencies; the hosted paths send audio to the
  cloud (privacy) and depend on their free-tier limits (AssemblyAI's is one-time).
- **Diarization quality is audio-bound, not just provider-bound:** a real 13-min
  single-microphone Spanish meeting came back from AssemblyAI as a single
  speaker. Far-field single-mic audio with overlapping voices is the worst case
  for *any* diarizer. The fix is not to hardcode a count but to compare providers
  on the *same* audio (diagnostic logging was added for this) and, where
  possible, improve the capture setup.
- **To revisit:** A GPU `LocalAudioAnalyzer` (`DEVICE=cuda`) keeps long meetings
  local if hardware is available; a Groq transcription analyzer could be paired
  with hosted diarization.

## Action Items

1. [x] `AudioAnalyzer` port + use-case refactor to depend on it.
2. [x] `LocalAudioAnalyzer` (parallel whisper + pyannote), `AssemblyAIAudioAnalyzer`
       and `SpeechmaticsAudioAnalyzer` (hosted).
3. [x] `ANALYSIS_PROVIDER` setting + DI wiring (hosted modes never load local models).
4. [x] CI-safe unit tests (local parallelism/attribution; hosted mapping + validation).
5. [x] First real run against a hosted provider — AssemblyAI returned a single
       speaker on hard single-mic audio; added `speakers_expected` hint +
       diagnostic logging and kept provider choice open to compare on the same file.
