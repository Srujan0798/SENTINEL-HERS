"""Integration tests for voice-to-ticket pipeline."""
import io
import struct
import sys
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backend.incidents.database import Base, get_db
from src.backend.incidents.models import Incident
from src.backend.voice.transcribe import MockTranscriber
from src.backend.voice import routes as voice_routes
from api.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_voice.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Register the voice router
app.include_router(voice_routes.router)
client = TestClient(app)

TEAM_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.pop(get_db, None)


def _make_tiny_wav(duration_ms: int = 100, sample_rate: int = 16000) -> bytes:
    """Generate a minimal valid WAV file."""
    num_samples = int(sample_rate * duration_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * num_samples)
    return buf.getvalue()


def test_voice_upload_creates_incident():
    """Core acceptance: upload audio -> 201 with valid incident_id and severity."""
    wav_bytes = _make_tiny_wav()

    response = client.post(
        "/api/voice/incidents",
        params={"team_id": TEAM_ID, "actor": "voice-test"},
        files={"file": ("test.wav", wav_bytes, "audio/wav")},
    )

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()

    assert "id" in data
    assert data["severity"] in ["SEV1", "SEV2", "SEV3", "SEV4"]
    assert data["title"] is not None and len(data["title"]) > 0
    assert data["status"] == "detected"
    assert data["team_id"] == TEAM_ID


def test_voice_transcript_in_metadata():
    """Metadata should contain the transcript and source=voice."""
    wav_bytes = _make_tiny_wav()

    response = client.post(
        "/api/voice/incidents",
        params={"team_id": TEAM_ID},
        files={"file": ("test.wav", wav_bytes, "audio/wav")},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["metadata"]["source"] == "voice"
    assert "transcript" in data["metadata"]
    assert len(data["metadata"]["transcript"]) > 0


def test_voice_severity_mapping_sev1():
    """'database is on fire' should map to SEV1."""
    wav_bytes = _make_tiny_wav()

    response = client.post(
        "/api/voice/incidents",
        params={"team_id": TEAM_ID},
        files={"file": ("test.wav", wav_bytes, "audio/wav")},
    )

    assert response.status_code == 201
    data = response.json()
    # MockTranscriber returns "database is on fire..." -> SEV1
    assert data["severity"] == "SEV1"


def test_voice_invalid_extension():
    """Reject non-audio file extensions."""
    response = client.post(
        "/api/voice/incidents",
        params={"team_id": TEAM_ID},
        files={"file": ("test.txt", b"not audio", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported audio format" in response.json()["detail"]


def test_voice_empty_file():
    """Reject empty audio files."""
    response = client.post(
        "/api/voice/incidents",
        params={"team_id": TEAM_ID},
        files={"file": ("test.wav", b"", "audio/wav")},
    )

    assert response.status_code == 400
    assert "Empty audio file" in response.json()["detail"]


def test_voice_sample_endpoint():
    """GET /api/voice/sample returns a valid WAV."""
    response = client.get("/api/voice/sample")

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert len(response.content) > 44  # WAV header is 44 bytes minimum


def test_voice_affected_services_in_metadata():
    """MockTranscriber text mentions 'payments service' -> should appear in metadata."""
    wav_bytes = _make_tiny_wav()

    response = client.post(
        "/api/voice/incidents",
        params={"team_id": TEAM_ID},
        files={"file": ("test.wav", wav_bytes, "audio/wav")},
    )

    assert response.status_code == 201
    data = response.json()
    services = data["metadata"].get("affected_services", [])
    assert "payments" in services


def test_voice_multiple_uploads():
    """Multiple voice uploads should each create distinct incidents."""
    wav_bytes = _make_tiny_wav()

    ids = []
    for _ in range(3):
        resp = client.post(
            "/api/voice/incidents",
            params={"team_id": TEAM_ID},
            files={"file": ("test.wav", wav_bytes, "audio/wav")},
        )
        assert resp.status_code == 201
        ids.append(resp.json()["id"])

    assert len(set(ids)) == 3, "Each upload should create a unique incident"
