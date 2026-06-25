from __future__ import annotations
import io
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.api.dependencies import get_job_store, get_use_case
from app.application.generate_meeting_minutes import GenerateMeetingMinutes
from app.infrastructure.jobs.in_memory_job_store import InMemoryJobStore
from tests.fakes.adapters import FakeAnalyzer, FakeMinutesGenerator


def make_test_client() -> tuple[TestClient, InMemoryJobStore]:
    app = create_app()
    store = InMemoryJobStore()

    fake_use_case = GenerateMeetingMinutes(
        analyzer=FakeAnalyzer(),
        generator=FakeMinutesGenerator(),
        store=store,
    )

    app.dependency_overrides[get_job_store] = lambda: store
    app.dependency_overrides[get_use_case] = lambda: fake_use_case

    return TestClient(app), store


def test_post_transcription_returns_202_with_job_id() -> None:
    client, _ = make_test_client()
    audio_bytes = b"fake audio content"
    response = client.post(
        "/api/v1/transcriptions/",
        files={"file": ("test.wav", io.BytesIO(audio_bytes), "audio/wav")},
        data={"language": "es", "model_size": "small"},
    )
    assert response.status_code == 202
    body = response.json()
    assert "job_id" in body
    assert body["status"] == "PENDING"


def test_get_unknown_job_returns_404() -> None:
    client, _ = make_test_client()
    response = client.get("/api/v1/transcriptions/nonexistent-id")
    assert response.status_code == 404


def test_get_health_returns_ok() -> None:
    client, _ = make_test_client()
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_transcription_after_post_returns_200() -> None:
    client, store = make_test_client()
    audio_bytes = b"fake audio content"
    post_response = client.post(
        "/api/v1/transcriptions/",
        files={"file": ("test.wav", io.BytesIO(audio_bytes), "audio/wav")},
        data={"language": "es", "model_size": "small"},
    )
    assert post_response.status_code == 202
    job_id = post_response.json()["job_id"]

    get_response = client.get(f"/api/v1/transcriptions/{job_id}")
    assert get_response.status_code == 200
    body = get_response.json()
    assert body["job_id"] == job_id
    assert "status" in body


def test_cancel_active_job_returns_200_with_job_id() -> None:
    """POST /{job_id}/cancel on an active (PENDING) job should return 200 with the job_id."""
    client, store = make_test_client()
    job = store.create()

    response = client.post(f"/api/v1/transcriptions/{job.id}/cancel")

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == job.id
    assert "status" in body


def test_cancel_unknown_job_returns_404() -> None:
    """POST /{job_id}/cancel on a non-existent job should return 404."""
    client, _ = make_test_client()

    response = client.post("/api/v1/transcriptions/nonexistent-id/cancel")

    assert response.status_code == 404


def test_cancel_finished_job_returns_409() -> None:
    """POST /{job_id}/cancel on a DONE job should return 409 (not cancellable)."""
    from app.domain.models import (
        AttributedSegment,
        TranscriptionMetadata,
        TranscriptionResult,
    )

    client, store = make_test_client()
    job = store.create()
    result = TranscriptionResult(
        transcript=[
            AttributedSegment(start=0.0, end=5.0, text="hello", speaker="SPEAKER_00")
        ],
        minutes="# Minutes",
        metadata=TranscriptionMetadata(
            duration_sec=5.0, language="es", num_speakers=1, model="test"
        ),
    )
    store.mark_done(job.id, result)

    response = client.post(f"/api/v1/transcriptions/{job.id}/cancel")

    assert response.status_code == 409


def make_test_client_with_settings(
    settings_override,
) -> tuple[TestClient, InMemoryJobStore]:
    from app.config import get_settings

    app = create_app()
    store = InMemoryJobStore()

    fake_use_case = GenerateMeetingMinutes(
        analyzer=FakeAnalyzer(),
        generator=FakeMinutesGenerator(),
        store=store,
    )

    app.dependency_overrides[get_settings] = lambda: settings_override
    app.dependency_overrides[get_job_store] = lambda: store
    app.dependency_overrides[get_use_case] = lambda: fake_use_case

    return TestClient(app), store


def test_post_transcription_payload_too_large_via_content_length() -> None:
    from app.config import Settings

    custom_settings = Settings(max_upload_size_bytes=10)
    client, _ = make_test_client_with_settings(custom_settings)

    audio_bytes = b"fake audio content longer than 10 bytes"
    response = client.post(
        "/api/v1/transcriptions/",
        files={"file": ("test.wav", io.BytesIO(audio_bytes), "audio/wav")},
        headers={"content-length": str(len(audio_bytes))},
    )
    assert response.status_code == 413
    assert "Payload too large" in response.json()["detail"]


def test_post_transcription_payload_too_large_via_file_reading() -> None:
    from app.config import Settings

    custom_settings = Settings(max_upload_size_bytes=10)
    client, _ = make_test_client_with_settings(custom_settings)

    audio_bytes = b"fake audio content longer than 10 bytes"
    response = client.post(
        "/api/v1/transcriptions/",
        files={"file": ("test.wav", io.BytesIO(audio_bytes), "audio/wav")},
    )
    assert response.status_code == 413
    assert "Payload too large" in response.json()["detail"]


def test_post_transcription_invalid_extension() -> None:
    client, _ = make_test_client()
    audio_bytes = b"fake audio content"
    response = client.post(
        "/api/v1/transcriptions/",
        files={
            "file": ("test.exe", io.BytesIO(audio_bytes), "application/x-msdownload")
        },
    )
    assert response.status_code == 400
    assert "Unsupported file extension" in response.json()["detail"]


@pytest.mark.asyncio
async def test_periodic_cleanup_cleans_expired_jobs() -> None:
    import asyncio
    from app.main import periodic_cleanup
    from app.api.dependencies import get_job_store, get_settings
    from unittest.mock import patch
    from app.config import Settings

    get_job_store.cache_clear()
    get_settings.cache_clear()

    store = get_job_store()

    job = store.create()
    store.mark_cancelled(job.id)  # Mark it as a terminal status so it can be expired

    custom_settings = Settings(job_ttl_seconds=0)

    with patch("app.main.get_settings", return_value=custom_settings):
        with patch("asyncio.sleep", side_effect=asyncio.CancelledError):
            try:
                await periodic_cleanup()
            except asyncio.CancelledError:
                pass

    assert store.get(job.id) is None


def test_rate_limiting_blocks_after_5_requests() -> None:
    client, _ = make_test_client()
    audio_bytes = b"fake audio"

    # First 5 requests should succeed (202)
    for _ in range(5):
        response = client.post(
            "/api/v1/transcriptions/",
            files={"file": ("test.wav", io.BytesIO(audio_bytes), "audio/wav")},
            headers={"X-Forwarded-For": "2.2.2.2"},
        )
        assert response.status_code == 202

    # 6th request should fail with 429
    response = client.post(
        "/api/v1/transcriptions/",
        files={"file": ("test.wav", io.BytesIO(audio_bytes), "audio/wav")},
        headers={"X-Forwarded-For": "2.2.2.2"},
    )
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.text


def test_get_render_client_ip_extracts_correct_ip() -> None:
    from app.api.rate_limit import get_render_client_ip
    from unittest.mock import MagicMock

    # 1. Multiple IPs in X-Forwarded-For
    request_multi = MagicMock()
    request_multi.headers = {
        "X-Forwarded-For": "203.0.113.195, 70.41.3.18, 150.172.238.178"
    }
    assert get_render_client_ip(request_multi) == "203.0.113.195"

    # 2. Single IP in X-Forwarded-For
    request_single = MagicMock()
    request_single.headers = {"X-Forwarded-For": " 203.0.113.195 "}
    assert get_render_client_ip(request_single) == "203.0.113.195"

    # 3. No X-Forwarded-For, fall back to client host
    request_fallback = MagicMock()
    request_fallback.headers = {}
    request_fallback.client.host = "192.168.1.1"
    assert get_render_client_ip(request_fallback) == "192.168.1.1"

    # 4. No client info at all
    request_none = MagicMock()
    request_none.headers = {}
    request_none.client = None
    assert get_render_client_ip(request_none) == "127.0.0.1"
