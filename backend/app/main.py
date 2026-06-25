from __future__ import annotations
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dependencies import get_use_case
from app.config import get_settings
from app.api.routes.transcriptions import router as transcriptions_router
from app.api.schemas import HealthResponse
from app.workers.job_worker import shutdown_worker

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    # Authenticate Hugging Face downloads (faster-whisper otherwise downloads its
    # model unauthenticated -> slower, rate-limited) and silence the Windows
    # symlink-cache warning. setdefault respects values already in the environment.
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    if settings.huggingface_token.strip():
        os.environ.setdefault("HF_TOKEN", settings.huggingface_token)

    # Warm the singletons so models load ONCE at startup (ADR-0001), not on the
    # first request. TODO: this becomes real model initialization once the
    # stub adapters are replaced.
    logger.info("Loading models (stub — replace with real  init)")
    get_use_case()
    yield
    shutdown_worker()
    logger.info("Shutting down")


def create_app() -> FastAPI:
    app = FastAPI(title="ActIA", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(transcriptions_router, prefix="/api/v1/transcriptions")

    @app.get("/api/v1/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    return app


app = create_app()
