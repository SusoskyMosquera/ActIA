from __future__ import annotations
import io
import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.api.dependencies import get_job_store, get_use_case
from app.application.generate_meeting_minutes import GenerateMeetingMinutes
from app.infrastructure.jobs.in_memory_job_store import InMemoryJobStore
from tests.fakes.adapters import FakeDiarizer, FakeMinutesGenerator, FakeTranscriber


def make_test_client() -> tuple[TestClient, InMemoryJobStore]:
    app = create_app()
    store = InMemoryJobStore()

    fake_use_case = GenerateMeetingMinutes(
        transcriber=FakeTranscriber(),
        diarizer=FakeDiarizer(),
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
