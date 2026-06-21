"""Voice-to-ticket API routes."""
import io
import os
import struct
import wave
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from src.backend.incidents.database import get_db
from src.backend.incidents.enums import SeverityLevel
from src.backend.incidents.service import IncidentService

from .parse import parse_voice_to_incident
from .transcribe import get_transcriber

router = APIRouter(prefix="/api/voice", tags=["voice"])

ALLOWED_EXTENSIONS = {".wav", ".mp3", ".webm", ".m4a", ".ogg", ".flac"}


@router.post("/incidents", status_code=status.HTTP_201_CREATED)
async def voice_to_incident(
    file: UploadFile = File(...),
    team_id: UUID = Query(...),
    actor: str = Query("voice"),
    db: Session = Depends(get_db),
):
    """Accept audio upload, transcribe, parse, and create incident."""
    # Validate file extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported audio format: {ext}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    audio_bytes = await file.read()
    if len(audio_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty audio file",
        )

    # Step 1: Transcribe
    transcriber = get_transcriber()
    try:
        transcript = transcriber.transcribe(audio_bytes, filename=file.filename or "audio.wav")
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Transcription failed: {exc}",
        )

    # Step 2: Parse via LLM
    try:
        parsed = parse_voice_to_incident(transcript)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Parsing failed: {exc}",
        )

    # Step 3: Create incident
    severity = SeverityLevel(parsed.severity)
    svc = IncidentService(db)
    result = svc.create_incident(
        team_id=team_id,
        title=parsed.title,
        severity=severity,
        description=parsed.description,
        metadata={
            "source": "voice",
            "transcript": transcript,
            "affected_services": parsed.affected_services,
        },
        actor=actor,
    )

    return result


@router.get("/sample")
async def get_sample_audio():
    """Return a small generated WAV file for demo/testing."""
    wav_bytes = _generate_silence_wav(duration_ms=1000, sample_rate=16000)
    from fastapi.responses import Response

    return Response(
        content=wav_bytes,
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=sample.wav"},
    )


def _generate_silence_wav(duration_ms: int = 1000, sample_rate: int = 16000) -> bytes:
    """Generate a minimal valid WAV file with silence."""
    num_samples = int(sample_rate * duration_ms / 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(b"\x00\x00" * num_samples)
    return buf.getvalue()
