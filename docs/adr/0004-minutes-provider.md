# ADR-0004: Minutes-generation provider — selectable (Gemini default, Ollama for OSS/privacy)

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Project stakeholders

## Context

The initial proposal included Gemini for minutes generation. A follow-up
requirement surfaced: the project is meant to be open source and free, and the
audio it processes (meeting recordings) is often confidential.

Verified facts (web research, June 2026):

- **Gemini free tier** (e.g. `gemini-2.5-flash`): 15 RPM, 1M TPM, 1,500 RPD —
  for a personal/low-volume stateless tool this is *far* more than enough (one
  meeting ≈ one request ≈ ~13K tokens; you would never approach the limits).
  **But** on the free tier Google may use prompts/outputs to train its models,
  and the EEA/UK/CH privacy exception does not apply here. It is also closed.
- **Local LLM via Ollama** (e.g. `qwen2.5:3b`, Apache 2.0): fully open source,
  free, local, private (nothing leaves the machine). Lower quality than Gemini
  Flash, and slower on CPU.
- **Groq** (open-weight models, hosted, free): high quality, but low free-tier
  TPM forces chunking of long transcripts, and data leaves the machine.

There is no single option that is simultaneously highest-quality, free,
fully-local/private, and fast on CPU. The choice is a values trade-off.

## Decision

Keep the `MinutesGenerator` port and make the provider **selectable** via
`MINUTES_PROVIDER`:

- **`gemini`** (default) — best quality, free at this volume. The stakeholder
  accepted the data-training trade-off for non-sensitive meetings.
- **`ollama`** — fully open-source, local, private alternative; one env var away.

Both providers share the same pure `build_minutes_prompt` / `_build_prompt`
logic. Adding Ollama was a new adapter + one wiring branch — the domain was not
touched (the payoff of ADR-0002).

## Options Considered

### Option A: Gemini only (as in ADR-0003)
**Pros:** Best quality; simplest. **Cons:** Closed; free tier trains on your
data; not aligned with the open-source goal.

### Option B: Ollama (local OSS) only
**Pros:** Fully open, private, unlimited. **Cons:** Lower quality on CPU; needs
local RAM/compute; user must install Ollama + pull a model.

### Option C: Selectable, Gemini default + Ollama option (chosen)
**Pros:** Quality by default, privacy/OSS on demand, zero domain cost.
**Cons:** Two client dependencies to maintain (`google-genai`, `ollama`).

## Consequences

- **Easier:** Users get max quality out of the box, or flip one env var for a
  fully-local private pipeline. With Ollama, the *entire* stack is OSS + local.
- **Harder:** Two minutes-client dependencies; two code paths to keep working.
- **To revisit:** If privacy becomes a hard requirement, flip the default to
  `ollama`. A Groq adapter could be added later for hosted open-weight quality.

## Action Items

1. [x] `OllamaMinutesGenerator` adapter (local, via the `ollama` client).
2. [x] `GeminiMinutesGenerator` on the modern `google-genai` SDK.
3. [x] `MINUTES_PROVIDER` setting + selectable wiring in `dependencies.py`.
4. [x] Shared prompt builder; CI-safe unit tests (no heavy deps).
5. [x] First real run validated on real Spanish audio — Gemini produced a
       structured acta; quality accepted. Gemini 503 errors handled with
       exponential-backoff retry (`_is_retryable`, `_call_with_retry`).
