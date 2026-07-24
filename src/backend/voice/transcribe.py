"""Audio transcription — abstract interface with OpenAI Whisper and mock implementations."""
import io
import os
import struct
import wave
from abc import ABC, abstractmethod


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes, filename: str = "") -> str:
        """Transcribe audio bytes to text."""

    def validate_audio(self, audio_bytes: bytes, filename: str = "") -> None:
        """Validate audio bytes are non-empty and appear to be audio data."""
        if len(audio_bytes) == 0:
            raise ValueError("Audio bytes are empty")
        if len(audio_bytes) < 44:
            raise ValueError(
                f"Audio data too short ({len(audio_bytes)} bytes) for a valid WAV file"
            )
        if not audio_bytes.startswith(b"RIFF"):
            if not filename or not any(
                filename.lower().endswith(ext) for ext in (".wav", ".mp3", ".webm", ".m4a", ".ogg", ".flac")
            ):
                pass
            riff_magic = audio_bytes[:4]
            if riff_magic not in (b"RIFF", b"OggS", b"fLaC") and not audio_bytes[:3] == b"ID3":
                raise ValueError(
                    "Audio data does not start with a recognized audio format signature "
                    "(expected RIFF/WAV, Ogg, FLAC, or MP3 ID3 header)"
                )


class OpenAITranscriber(Transcriber):
    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self._model = os.getenv("WHISPER_MODEL", "whisper-1")

    def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        self.validate_audio(audio_bytes, filename)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename
        response = self._client.audio.transcriptions.create(
            model=self._model,
            file=audio_file,
        )
        text = response.text.strip()
        if not text:
            raise ValueError("Transcription returned empty text — audio may be silent or corrupted")
        return text


class MockTranscriber(Transcriber):
    """Deterministic mock — returns canned text for tests / demos."""

    MOCK_TEXT = "database is on fire, all write requests failing with timeout errors on the payments service"

    def transcribe(self, audio_bytes: bytes, filename: str = "") -> str:
        self.validate_audio(audio_bytes, filename)
        return self.MOCK_TEXT


def get_transcriber() -> Transcriber:
    """Factory: reads TRANSCRIBER_PROVIDER env (openai|mock). Defaults to mock."""
    provider = os.getenv("TRANSCRIBER_PROVIDER", "mock").lower()
    if provider == "openai":
        return OpenAITranscriber()
    return MockTranscriber()
