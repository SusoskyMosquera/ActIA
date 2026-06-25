# Deployment Guide - ActIA

This document details the production deployment architecture for the **ActIA** application, specifying where each service runs, how they are configured, and how to resolve common integration issues (CORS, URLs, etc.).

---

## 🏗️ Deployment Architecture (Hybrid)

To ensure stability, scalability, and compatibility of the application with serverless and persistent runtimes, a **hybrid deployment model** was chosen:

```
┌────────────────────────────────┐       ┌─────────────────────────────────┐
│     FRONTEND (React + Vite)    │ ────> │        BACKEND (FastAPI)        │
│     Deployed to: VERCEL        │       │      Deployed to: RENDER        │
│  https://act-ia.vercel.app     │       │    https://actia.onrender.com   │
└────────────────────────────────┘       └─────────────────────────────────┘
```

1. **Frontend (Vercel):** Served as a static Single Page Application (SPA), globally optimized and distributed at the edge.
2. **Backend (Render):** Runs on a persistent Docker container to support the in-memory job store (`InMemoryJobStore`) and allow background asynchronous threads to complete without runtime freezing.

---

## 🔗 Production Links & Endpoints

* **Web Application (Frontend):** [https://act-ia.vercel.app/](https://act-ia.vercel.app/)
* **Production API (Backend):** [https://actia.onrender.com/](https://actia.onrender.com/)
* **API Base URL (Vite):** `https://actia.onrender.com/api/v1`
* **Liveness Probe (Healthcheck):** [https://actia.onrender.com/api/v1/health](https://actia.onrender.com/api/v1/health)

---

## ⚙️ Configuration & Environment Variables

### 1. Frontend (Vercel)
In the Vercel project settings dashboard, configure the following parameters:

* **Root Directory:** `frontend`
* **Framework Preset:** `Vite`
* **Build Command:** `npm run build`
* **Output Directory:** `dist`
* **Environment Variables:**
  * `VITE_API_BASE_URL`: `https://actia.onrender.com/api/v1` *(⚠️ IMPORTANT: Do not include a trailing slash `/`)*

### 2. Backend (Render)
In the **Environment** tab of the web service in the Render control panel, configure the following variables:

* **Root Directory:** `backend`
* **Runtime:** `Docker` (Render automatically detects the [Dockerfile](file:///c:/Users/SOPORTES%20JPVM/Documents/Personal%20Proyects/ActIA/backend/Dockerfile))
* **Environment Variables:**
  * `CORS_ORIGINS`: `http://localhost:5173,https://act-ia.vercel.app` *(⚠️ Allows requests from both the local development server and the production frontend. Must be comma-separated without spaces and without a trailing slash `/`)*
  * `ADAPTER_MODE`: `real`
  * `ANALYSIS_PROVIDER`: `assemblyai` *(or `speechmatics`, recommended for free tiers/CPUs without GPUs to avoid resource exhaustion)*
  * `ASSEMBLYAI_API_KEY`: *(Your AssemblyAI API key)*
  * `GEMINI_API_KEY`: *(Your Google AI Studio API key)*

---

## 🚨 Gotchas & Troubleshooting

### 1. CORS Error (`CORS Missing Allow Origin`)
If the browser throws CORS errors when attempting to run a transcription job, verify:
* **Missing origin in `CORS_ORIGINS`:** Make sure the exact origin from which you are making the request is listed in the backend's `CORS_ORIGINS` variable. The production frontend needs `https://act-ia.vercel.app`. Testing locally requires `http://localhost:5173`.
* **Trailing slash (`/`):** The browser sends the `Origin` header without a trailing slash (e.g., `https://act-ia.vercel.app`). If you configured the variable with a trailing slash (`https://act-ia.vercel.app/`), the backend will reject the request due to a mismatch.
* **Pending redeploy:** Any changes to the environment variables on Render require you to save them and verify that a manual or automatic redeployment completes successfully so that FastAPI updates its loaded settings.

### 2. Double Slashes in API Requests
If you configure `VITE_API_BASE_URL` with a trailing slash (e.g., `https://actia.onrender.com/api/v1/`), requests resolve as `.../api/v1//transcriptions/`.
FastAPI responds with an automatic redirect (`307` or `308`) to clean up the double slash. During this redirect, the browser drops the CORS headers, leading to a CORS failure. **Always keep this URL without a trailing `/`**.

### 3. Cold Start on Render (Free Tier)
If you are using Render's free tier, the container spins down after 15 minutes of inactivity. The first request that wakes up the backend can take up to 50 seconds to respond. During this boot phase, the request may timeout, and the Render load balancer returns a `502 Bad Gateway` or `504 Gateway Timeout` response without CORS headers. The browser will report this as a CORS error.
* *Recommendation:* Visit `https://actia.onrender.com/api/v1/health` directly in your browser to wake up the service before using the web app.
