from __future__ import annotations
import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor

from app.application.generate_meeting_minutes import GenerateMeetingMinutes

logger = logging.getLogger(__name__)

# Single worker thread => jobs run ONE AT A TIME (ADR-0001), off the event loop,
# and never concurrently on a shared, non-thread-safe model instance.
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="actia-job")


async def run_job(
    job_id: str, audio_path: str, use_case: GenerateMeetingMinutes
) -> None:
    """Execute the pipeline on the single worker thread, then clean up the upload."""
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(_executor, use_case.execute, job_id, audio_path)
    finally:
        try:
            os.remove(audio_path)
        except OSError:
            logger.warning("Could not remove temp file: %s", audio_path)


def shutdown_worker() -> None:
    """Drain and stop the worker thread (called on application shutdown)."""
    _executor.shutdown(wait=True)
