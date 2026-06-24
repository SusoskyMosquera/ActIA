# ADR-0001: Asynchronous processing model (job + polling)

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Project stakeholders

## Context

ActIA transcribes and diarizes a full meeting audio file. With local models
(faster-whisper + pyannote.audio), processing a 30–60 minute recording on CPU
takes **minutes**, not milliseconds.

The product spec mandates a **stateless** flow: no authentication, no user
accounts, no database, no persistence. The user uploads audio and gets the
result on the same screen.

Two forces collide:

- A naive synchronous request would exceed browser/proxy timeouts (typically
  30–100s) and leave the user staring at a blind spinner for minutes.
- "Stateless" must not be confused with "synchronous single request". We can be
  stateless (no DB) and still need a way to track long-running work.

## Decision

Adopt an **asynchronous job model with client polling**:

1. `POST /transcriptions` accepts the audio, enqueues a job, and immediately
   returns a `job_id` with status `PENDING`.
2. A **background worker** runs the heavy pipeline **off the FastAPI event
   loop** (faster-whisper is CPU-bound; running it inline would block the whole
   server).
3. Models are loaded **once at application startup** (singleton in the
   infrastructure layer), never per request.
4. The client polls `GET /transcriptions/{job_id}` until status is `DONE` or
   `ERROR`, reading an intermediate `stage` field for progress UX.
5. Job state lives in an **in-memory store** (a dict behind a `JobStore` port).
   Transient, no Redis, no Celery, no DB — consistent with the "lightweight,
   stateless" goal.

## Options Considered

### Option A: Synchronous single request
| Dimension | Assessment |
|-----------|------------|
| Complexity | Low |
| Cost | None extra |
| Scalability | Poor — blocks the event loop per request |
| UX | Poor — blind wait, timeout risk |

**Pros:** Trivial to implement; no job lifecycle.
**Cons:** Breaks on long audio (timeouts); one request can stall the server;
no progress feedback.

### Option B: Async + in-memory job + polling (chosen)
| Dimension | Assessment |
|-----------|------------|
| Complexity | Medium |
| Cost | None extra (no broker/DB) |
| Scalability | Good for a single instance |
| UX | Good — progress stages, no timeouts |

**Pros:** Robust to long audio; visible progress; no extra infrastructure;
keeps the event loop free.
**Cons:** In-memory state is single-instance only and does not survive a
restart; needs a TTL/cleanup policy.

### Option C: Async + SSE / WebSocket streaming
| Dimension | Assessment |
|-----------|------------|
| Complexity | High |
| Cost | None extra |
| Scalability | Good for a single instance |
| UX | Best — real-time progress |

**Pros:** Live progress without polling.
**Cons:** More moving parts on both backend and frontend; not justified for the
first slice.

## Trade-off Analysis

Polling (Option B) is the sweet spot: it solves the timeout and event-loop
problems with the least machinery and zero new infrastructure. SSE (Option C)
buys nicer progress at a complexity cost we don't need yet — and because the
job lifecycle is identical, SSE can be layered on later without redesign.

## Consequences

- **Easier:** Long recordings no longer risk timeouts; the UI can show
  `transcribing → diarizing → generating minutes`; the server stays responsive.
- **Harder:** We must manage the in-memory job lifecycle (status transitions,
  result retention, TTL-based cleanup to avoid unbounded memory growth).
- **To revisit:** Horizontal scaling or restart-survival would require swapping
  the `JobStore` port to a Redis/DB adapter. Live progress would mean adding an
  SSE endpoint. Both are additive thanks to the port boundary.

## Action Items

1. [ ] Define `JobStore` port and `InMemoryJobStore` adapter.
2. [ ] Define job states: `PENDING → PROCESSING → DONE | ERROR` with a `stage`.
3. [ ] Implement a single-worker background runner (`asyncio.to_thread` / a
       1-worker executor) that pulls jobs and updates state.
4. [ ] Add a TTL/cleanup policy for finished jobs.
5. [ ] Load models once via the FastAPI `lifespan` hook.
