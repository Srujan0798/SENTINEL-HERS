"""AI provider abstraction — wraps Claude and Gemini behind a single interface.

Provider selection is driven by env (``AI_PROVIDER`` = claude|gemini|mock).
Real LLM calls go through the official SDKs (``anthropic`` / ``google-generativeai``).
When the chosen provider's key is absent we fall back to the deterministic
:class:`MockProvider` — but we fail SAFE *and* LOUD by logging a WARNING (FM-11:
never silently mask a misconfiguration). Genuine API/timeout failures are surfaced
as a typed :class:`AIProviderError` so callers can turn them into a 5xx instead of
being swallowed by the mock.
"""
import logging
import os
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)

# Default Claude model per project AI guidance: newest capable Opus.
DEFAULT_CLAUDE_MODEL = "claude-opus-4-8"
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"

# How long (seconds) to wait on a single LLM request before treating it as failed.
_REQUEST_TIMEOUT = float(os.getenv("AI_REQUEST_TIMEOUT", "45"))


class AIProviderError(RuntimeError):
    """Raised when a real provider call fails (API error, timeout, bad response).

    Distinct from the mock fallback: this means a configured live provider was
    reached and genuinely failed. Routes convert it into a 5xx rather than
    silently degrading to mock output.
    """


class AIProvider(ABC):
    @abstractmethod
    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        """Send messages and return the assistant response text."""


def _claude_model() -> str:
    # AI_MODEL is the canonical knob; CLAUDE_MODEL kept for backward compat.
    return os.getenv("AI_MODEL") or os.getenv("CLAUDE_MODEL") or DEFAULT_CLAUDE_MODEL


def _gemini_model() -> str:
    return os.getenv("AI_MODEL") or os.getenv("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL


class ClaudeProvider(AIProvider):
    def __init__(self):
        import anthropic

        self._anthropic = anthropic
        self._client = anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
            timeout=_REQUEST_TIMEOUT,
        )
        self._model = _claude_model()

    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 2048,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        try:
            response = self._client.messages.create(**kwargs)
        except self._anthropic.APIError as exc:
            # Covers auth, rate-limit, timeout (APITimeoutError), overloaded, 5xx.
            raise AIProviderError(f"Claude API call failed: {exc}") from exc
        except Exception as exc:  # transport / unexpected — still fail loud, not silent
            raise AIProviderError(f"Claude call failed unexpectedly: {exc}") from exc

        try:
            return response.content[0].text
        except (IndexError, AttributeError) as exc:
            raise AIProviderError(
                f"Claude returned an unexpected response shape: {exc}"
            ) from exc


class GeminiProvider(AIProvider):
    def __init__(self):
        import google.generativeai as genai

        self._genai = genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self._model_name = _gemini_model()

    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        genai = self._genai
        system_inst = system if system else None
        model = genai.GenerativeModel(self._model_name, system_instruction=system_inst)
        gemini_messages = [
            {
                "role": m["role"] if m["role"] != "assistant" else "model",
                "parts": [m["content"]],
            }
            for m in messages
        ]
        try:
            response = model.generate_content(
                gemini_messages,
                request_options={"timeout": _REQUEST_TIMEOUT},
            )
        except Exception as exc:
            raise AIProviderError(f"Gemini API call failed: {exc}") from exc

        try:
            return response.text
        except (ValueError, AttributeError) as exc:
            # .text raises if the response was blocked / empty.
            raise AIProviderError(
                f"Gemini returned no usable text: {exc}"
            ) from exc


class MockProvider(AIProvider):
    """Fallback provider used when no API key is configured (tests/CI/offline)."""

    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        last = messages[-1]["content"] if messages else ""
        return f"[mock-ai] Response to: {last[:80]}"


def _fallback_to_mock(provider: str, missing_key: str) -> MockProvider:
    logger.warning(
        "AI_PROVIDER=%s selected but %s is not set — falling back to the "
        "deterministic MockProvider. Live AI output is DISABLED until the key "
        "is configured.",
        provider,
        missing_key,
    )
    return MockProvider()


def get_provider() -> AIProvider:
    """Factory: reads AI_PROVIDER env var (claude|gemini|mock). Defaults to mock.

    If the chosen live provider's key is absent, fall back to mock but log a
    clear WARNING (fail safe + loud, never a silent mask).
    """
    provider = os.getenv("AI_PROVIDER", "mock").lower()
    if provider == "claude":
        if not os.getenv("ANTHROPIC_API_KEY"):
            return _fallback_to_mock("claude", "ANTHROPIC_API_KEY")
        return ClaudeProvider()
    if provider == "gemini":
        if not os.getenv("GEMINI_API_KEY"):
            return _fallback_to_mock("gemini", "GEMINI_API_KEY")
        return GeminiProvider()
    return MockProvider()
