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


class OpenAITranscriber(Transcriber):
    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self._model = os.getenv("WHISPER_MODEL", "whisper-1")

    def transcribe(self, audio_bytes: bytes, filename: str = "audio.wav") -> str:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename
        response = self._client.audio.transcriptions.create(
            model=self._model,
            file=audio_file,
        )
        return response.text


class MockTranscriber(Transcriber):
    """Deterministic mock — returns canned text for tests / demos."""

    MOCK_TEXT = "database is on fire, all write requests failing with timeout errors on the payments service"

    def transcribe(self, audio_bytes: bytes, filename: str = "") -> str:
        return self.MOCK_TEXT


def get_transcriber() -> Transcriber:
    """Factory: reads TRANSCRIBER_PROVIDER env (openai|mock). Defaults to mock."""
    provider = os.getenv("TRANSCRIBER_PROVIDER", "mock").lower()
    if provider == "openai":
        return OpenAITranscriber()
    return MockTranscriber()
