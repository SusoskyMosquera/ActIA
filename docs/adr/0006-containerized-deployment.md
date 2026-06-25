# ADR-0006: Containerized one-command run via Docker Compose

**Status:** Accepted
**Date:** 2026-06-24
**Deciders:** Project stakeholders

## Context

The app is a two-process system: a FastAPI backend and a React/TypeScript
frontend. Running it meant following the README by hand — create a virtualenv,
`pip install`, start `uvicorn`, then `npm install` and `npm run dev` in a second
terminal, and rely on the Vite dev proxy to reach the API. That is fine for
development but it is friction for anyone who just wants to *run* the project,
and the dev server is not a way to serve the frontend.

The stakeholder ask was explicit: **bring the whole thing up with a single
command.** Separately, [ADR-0002](./0002-decoupled-audio-pipeline.md) freezes
*managed cloud hosting* until final adjustments are approved — that freeze is
about committing to a hosting provider, not about packaging the app for a
reproducible local/self-hosted run.

## Decision

Ship a **Docker Compose** stack so `docker compose up --build` starts everything:

| Service | Image | Role |
|---|---|---|
| `backend` | `python:3.12-slim` + `ffmpeg` | FastAPI on `:8000`, editable install |
| `frontend` | multi-stage `node:20-alpine` build → `nginx:alpine` | static build served on `:8080`, proxies `/api` → `backend:8000` |

Key choices:

- **Two services, one network.** nginx serves the built SPA and proxies `/api`
  to the backend over the compose network, so the browser only talks to one
  origin (`http://localhost:8080`) — no CORS, mirroring the dev proxy.
- **Demo by default.** With no `backend/.env` the app boots in demo mode (the
  code default), so the one-command path works with zero keys. `env_file` is
  loaded with `required: false`; dropping a real `.env` switches on real/hosted
  processing on the next `up`.
- **Light image by default, heavy ML opt-in.** The backend image installs only
  the light hosted/NLP clients (`INSTALL_EXTRAS="nlp,hosted"`). The heavy local
  stack (faster-whisper + pyannote + torch) is opt-in via a build arg —
  `docker compose build --build-arg INSTALL_EXTRAS="nlp,hosted,ml"` — so the
  default image stays small and builds fast.
- **Healthcheck** on the backend hits `/api/v1/health`; nginx allows large
  uploads (`client_max_body_size 2g`) and long proxy timeouts for slow analyses.
- `.dockerignore` on both sides keeps `.venv/`, `node_modules/`, `dist/`,
  build caches and **`.env`** out of the build context (no secrets in images).

## Options Considered

### Option A: Keep manual two-terminal setup only
**Pros:** Nothing to maintain.
**Cons:** High friction to run; no production-style serving of the frontend;
"works on my machine" drift. Does not meet the one-command ask.

### Option B: Single image running both processes
**Pros:** One container.
**Cons:** Couples two runtimes and lifecycles in one image; muddier logs,
scaling and healthchecks; an anti-pattern for the clean boundaries the rest of
the architecture keeps.

### Option C: Docker Compose, two services (chosen)
**Pros:** One command; each process isolated with its own image and healthcheck;
nginx serves the SPA properly and proxies the API; demo-by-default; heavy ML is
opt-in. Maps cleanly to the existing backend/frontend split.
**Cons:** Two images to build; ML images are large when the `ml` extra is added.

## Trade-off Analysis

Compose adds a handful of small, declarative files and in return removes all the
manual setup friction while keeping the backend and frontend as independent,
individually observable units. Demo-by-default means the happy path needs no
secrets; the build-arg split means the common case stays light and the heavy
local pipeline is one flag away. This does **not** lift the ADR-0002 freeze on
*managed cloud hosting* — it makes a reproducible local/self-hosted run trivial
and leaves a clean base to deploy from when hosting is approved.

## Consequences

- **Easier:** One-command run; reproducible environment; production-style static
  serving; demo works with zero config; heavy ML is opt-in.
- **Harder:** Two images to maintain; the `ml` image is large; local-mode CPU
  performance is unchanged (containerization is packaging, not acceleration).
- **To revisit:** When managed cloud hosting is unfrozen (ADR-0002), this stack
  is the starting point; a GPU base image would be needed to serve the local
  analyzer at usable speed.

## Action Items

1. [x] `backend/Dockerfile` (slim + ffmpeg, `INSTALL_EXTRAS` build arg, healthcheck).
2. [x] `frontend/Dockerfile` (multi-stage build → nginx) + `nginx.conf` (SPA + `/api` proxy).
3. [x] `docker-compose.yml` wiring both services, optional `backend/.env`.
4. [x] `.dockerignore` on both sides (no `.env`, no caches, no `node_modules`).
5. [x] README "Run with Docker (one command)" section.
