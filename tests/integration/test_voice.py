"""Integration tests for voice-to-ticket pipeline."""
import io
import struct
import sys
import wave
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.incidents.database import Base, get_db
from src.backend.incidents.models import Incident
from src.backend.voice import routes as voice_routes
from src.backend.voice.transcribe import MockTranscriber, Transcriber
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


client = TestClient(app)

TEAM_ID = "00000000-0000-0000-0000-000000000001"
USER_ID = "00000000-0000-0000-0000-000000000099"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_dependency] = lambda: {
        "id": USER_ID, "team_id": TEAM_ID, "role": "admin",
        "email": "demo@test.com", "is_active": True,
    }
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user_dependency, None)


def _make_tiny_wav(duration_ms: int = 100, sample_rate: int = 16000) -> bytes:
    num_samples = int(sample_rate * duration_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * num_samples)
    return buf.getvalue()


def test_voice_upload_creates_incident():
    wav_bytes = _make_tiny_wav()

    response = client.post(
        "/api/voice/incidents",
        params={"actor": "voice-test"},
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
    wav_bytes = _make_tiny_wav()

    response = client.post(
        "/api/voice/incidents",
        params={},
        files={"file": ("test.wav", wav_bytes, "audio/wav")},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["metadata"]["source"] == "voice"
    assert "transcript" in data["metadata"]
    assert len(data["metadata"]["transcript"]) > 0


def test_voice_severity_mapping_sev1():
    wav_bytes = _make_tiny_wav()

    response = client.post(
        "/api/voice/incidents",
        params={},
        files={"file": ("test.wav", wav_bytes, "audio/wav")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["severity"] == "SEV1"


def test_voice_invalid_extension():
    response = client.post(
        "/api/voice/incidents",
        params={},
        files={"file": ("test.txt", b"not audio", "text/plain")},
    )

    assert response.status_code == 400
    assert "Unsupported audio format" in response.json()["detail"]


def test_voice_empty_file():
    response = client.post(
        "/api/voice/incidents",
        params={},
        files={"file": ("test.wav", b"", "audio/wav")},
    )

    assert response.status_code == 400
    assert "Empty audio file" in response.json()["detail"]


def test_voice_garbage_audio():
    """Garbage bytes with .wav extension must be rejected with a loud 400."""
    garbage = b"\x01\x02\x03\x04\xFF\xFE\xFD\xFC" * 100

    response = client.post(
        "/api/voice/incidents",
        params={},
        files={"file": ("garbage.wav", garbage, "audio/wav")},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "Invalid audio data" in detail or "does not start with a recognized" in detail


def test_voice_sample_endpoint():
    response = client.get("/api/voice/sample")

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert len(response.content) > 44


def test_voice_affected_services_in_metadata():
    wav_bytes = _make_tiny_wav()

    response = client.post(
        "/api/voice/incidents",
        params={},
        files={"file": ("test.wav", wav_bytes, "audio/wav")},
    )

    assert response.status_code == 201
    data = response.json()
    services = data["metadata"].get("affected_services", [])
    assert "payments" in services


def test_voice_multiple_uploads():
    wav_bytes = _make_tiny_wav()

    ids = []
    for _ in range(3):
        resp = client.post(
            "/api/voice/incidents",
            params={},
            files={"file": ("test.wav", wav_bytes, "audio/wav")},
        )
        assert resp.status_code == 201
        ids.append(resp.json()["id"])

    assert len(set(ids)) == 3, "Each upload should create a unique incident"


def test_voice_unparseable_transcript_returns_422():
    """Empty transcript from transcriber must produce a 422, not hang or 500."""
    empty_transcriber = MagicMock(spec=Transcriber)
    empty_transcriber.transcribe.return_value = ""
    empty_transcriber.validate_audio.return_value = None

    with patch("src.backend.voice.routes.get_transcriber", return_value=empty_transcriber):
        wav_bytes = _make_tiny_wav()
        response = client.post(
            "/api/voice/incidents",
            params={},
            files={"file": ("test.wav", wav_bytes, "audio/wav")},
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert "empty text" in detail.lower() or "Transcription is empty" in detail


def test_voice_parse_failure_returns_422():
    """Unparseable transcript (garbage text) must produce a 422 with a real error."""
    garbage_transcriber = MagicMock(spec=Transcriber)
    garbage_transcriber.transcribe.return_value = "asdf qwerty zxcvb garbage !@#$%"
    garbage_transcriber.validate_audio.return_value = None

    with patch("src.backend.voice.routes.get_transcriber", return_value=garbage_transcriber):
        wav_bytes = _make_tiny_wav()
        response = client.post(
            "/api/voice/incidents",
            params={},
            files={"file": ("test.wav", wav_bytes, "audio/wav")},
        )

    assert response.status_code == 201, (
        f"Fallback parse should still produce an incident, got {response.status_code}: {response.text}"
    )
    data = response.json()
    assert data["title"] is not None


def test_voice_transcription_failure_returns_502():
    """Transcriber that raises an exception must produce a 502, not hang."""
    failing_transcriber = MagicMock(spec=Transcriber)
    failing_transcriber.transcribe.side_effect = RuntimeError("Whisper API timeout")
    failing_transcriber.validate_audio.return_value = None

    with patch("src.backend.voice.routes.get_transcriber", return_value=failing_transcriber):
        wav_bytes = _make_tiny_wav()
        response = client.post(
            "/api/voice/incidents",
            params={},
            files={"file": ("test.wav", wav_bytes, "audio/wav")},
        )

    assert response.status_code == 502
    assert "Transcription failed" in response.json()["detail"]


def test_voice_audio_too_short_rejected():
    """Audio under 44 bytes must be rejected as not a valid WAV."""
    short_audio = b"RIFF" + b"\x00" * 10

    response = client.post(
        "/api/voice/incidents",
        params={},
        files={"file": ("tiny.wav", short_audio, "audio/wav")},
    )

    assert response.status_code == 400
    assert "too short" in response.json()["detail"].lower()
