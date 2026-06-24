# ADR-0002: Decoupled audio pipeline behind ports (hexagonal) and deployment scope

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Project stakeholders

## Context

The spec mandates SOLID/GRASP and a clean/hexagonal layering: FastAPI routes
only receive requests; transcription, diarization, and external-API logic live
in independent services with dependency injection.

Two operational realities shape the design:

- Local models (faster-whisper + pyannote.audio) are **heavy** (PyTorch, RAM,
  ideally GPU). They cannot run on free deployment tiers (e.g., Render's free
  tier offers ~512 MB RAM — not enough to even load the model).
- Deployment is **frozen** by stakeholders until final adjustments are approved.

So we develop **local-first**, and we must keep the door open to a future where
the heavy local models are swapped for a hosted transcription/diarization API
without rewriting the domain.

## Decision

Each external capability sits behind a **domain port** (an interface), with
concrete **adapters** in the infrastructure layer:

| Port (domain) | Adapter (infrastructure) |
|---|---|
| `AudioTranscriber` | `FasterWhisperTranscriber` |
| `SpeakerDiarizer` | `PyannoteDiarizer` |
| `MinutesGenerator` | `GeminiMinutesGenerator` |
| `JobStore` | `InMemoryJobStore` |

The application layer (use case `GenerateMeetingMinutes`) depends only on the
ports, never on concrete SDKs. Wiring happens via FastAPI dependency injection.

Deployment stays **frozen**. The port boundary makes a later swap (local model →
hosted API) a change of one adapter, at zero cost to the domain.

## Options Considered

### Option A: Couple the domain directly to the SDKs
| Dimension | Assessment |
|-----------|------------|
| Complexity | Low upfront |
| Testability | Poor — domain needs real models to test |
| Flexibility | Poor — swapping a provider means touching the core |

**Pros:** Less boilerplate today.
**Cons:** Violates the spec's hexagonal mandate; locks us to local models;
unit tests would require loading PyTorch.

### Option B: Ports + adapters (chosen)
| Dimension | Assessment |
|-----------|------------|
| Complexity | Slightly higher upfront |
| Testability | High — fake adapters for fast unit tests |
| Flexibility | High — swap providers without touching the domain |

**Pros:** Matches the spec; domain is testable with fakes; provider-agnostic.
**Cons:** A few extra interfaces to maintain.

## Trade-off Analysis

The interfaces cost almost nothing and pay off immediately: the speaker-
attribution logic and the use-case orchestration become unit-testable with fake
adapters (no PyTorch, no network, no Gemini key), and the "deploy on free tier"
question reduces to "write a hosted-API adapter" instead of "rewrite the core".

## Consequences

- **Easier:** Fast, deterministic unit tests; provider swaps; clear boundaries.
- **Harder:** Slightly more files and indirection.
- **To revisit:** If free-tier deployment becomes a goal, add hosted-API
  adapters behind `AudioTranscriber` / `SpeakerDiarizer` and choose at wiring
  time via configuration.

## Action Items

1. [ ] Declare ports in `domain/ports.py`.
2. [ ] Keep speaker-attribution as pure domain logic (no external deps).
3. [ ] Implement adapters in `infrastructure/`.
4. [ ] Wire adapters via FastAPI DI in `api/dependencies.py`.
5. [ ] Keep deployment frozen; document the swap path for later.
