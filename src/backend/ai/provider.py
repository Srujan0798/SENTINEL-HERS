"""AI provider abstraction — wraps Claude and Gemini behind a single interface."""
import os
from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    @abstractmethod
    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        """Send messages and return the assistant response text."""


class ClaudeProvider(AIProvider):
    def __init__(self):
        import anthropic
        self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._model = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")

    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        kwargs: dict[str, Any] = {"model": self._model, "max_tokens": 2048, "messages": messages}
        if system:
            kwargs["system"] = system
        response = self._client.messages.create(**kwargs)
        return response.content[0].text


class GeminiProvider(AIProvider):
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self._model = genai.GenerativeModel(model_name, system_instruction=None)

    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        import google.generativeai as genai
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        system_inst = system if system else None
        model = genai.GenerativeModel(model_name, system_instruction=system_inst)
        gemini_messages = [
            {"role": m["role"] if m["role"] != "assistant" else "model", "parts": [m["content"]]}
            for m in messages
        ]
        response = model.generate_content(gemini_messages)
        return response.text


class MockProvider(AIProvider):
    """Fallback provider used when no API key is configured (tests/CI)."""

    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        last = messages[-1]["content"] if messages else ""
        return f"[mock-ai] Response to: {last[:80]}"


def get_provider() -> AIProvider:
    """Factory: reads AI_PROVIDER env var (claude|gemini|mock). Defaults to mock."""
    provider = os.getenv("AI_PROVIDER", "mock").lower()
    if provider == "claude":
        return ClaudeProvider()
    if provider == "gemini":
        return GeminiProvider()
    return MockProvider()
