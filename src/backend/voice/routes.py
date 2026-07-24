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

# Maximum audio file size: 60 MB
MAX_AUDIO_SIZE = 60 * 1024 * 1024


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

    # Validate audio content
    transcriber = get_transcriber()
    try:
        transcriber.validate_audio(audio_bytes, file.filename or "")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid audio data: {exc}",
        ) from exc

    if len(audio_bytes) > MAX_AUDIO_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"Audio file too large ({len(audio_bytes)} bytes). Maximum: {MAX_AUDIO_SIZE}",
        )

    # Step 1: Transcribe
    try:
        transcript = transcriber.transcribe(audio_bytes, filename=file.filename or "audio.wav")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transcription rejected: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Transcription failed unexpectedly: {exc}",
        ) from exc

    if not transcript or not transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Transcription returned empty text — could not extract incident details",
        ) from None

    # Step 2: Parse via LLM
    try:
        parsed = parse_voice_to_incident(transcript)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse transcript into incident: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Parsing failed unexpectedly: {exc}",
        ) from exc

    # Step 3: Create incident
    try:
        severity = SeverityLevel(parsed.severity)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Invalid severity from parse: {parsed.severity}",
        ) from exc

    svc = IncidentService(db)
    try:
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
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create incident: {exc}",
        ) from exc

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
