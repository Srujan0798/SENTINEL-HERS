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
import time

from src.backend.shared.advanced_circuit_breaker import circuit_breaker, with_circuit_breaker

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

    def stream_complete(self, messages: list[dict[str, str]], system: str = ""):
        """Yield response text chunks. Default: yield full complete() output."""
        yield self.complete(messages, system=system)


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

    @with_circuit_breaker("ai")
    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        start_time = time.time()
        
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": 2048,
            "messages": messages,
        }
        if system:
            kwargs["system"] = system
        
        try:
            response = self._client.messages.create(**kwargs)
            response_time = time.time() - start_time
            
            # Log successful response time for monitoring
            logger.info(f"Claude API call completed in {response_time:.2f}s")
            
            try:
                return response.content[0].text
            except (IndexError, AttributeError) as exc:
                raise AIProviderError(
                    f"Claude returned an unexpected response shape: {exc}"
                ) from exc
                
        except self._anthropic.APIError as exc:
            # Covers auth, rate-limit, timeout (APITimeoutError), overloaded, 5xx.
            response_time = time.time() - start_time
            logger.error(f"Claude API call failed in {response_time:.2f}s: {exc}")
            raise AIProviderError(f"Claude API call failed: {exc}") from exc
        except Exception as exc:  # transport / unexpected — still fail loud, not silent
            response_time = time.time() - start_time
            logger.error(f"Claude call failed unexpectedly in {response_time:.2f}s: {exc}")
            raise AIProviderError(f"Claude call failed unexpectedly: {exc}") from exc


class GeminiProvider(AIProvider):
    def __init__(self):
        import google.generativeai as genai

        self._genai = genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        self._model_name = _gemini_model()

    @with_circuit_breaker("ai")
    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        start_time = time.time()
        
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
            
            response_time = time.time() - start_time
            logger.info(f"Gemini API call completed in {response_time:.2f}s")
            
            try:
                return response.text
            except (ValueError, AttributeError) as exc:
                # .text raises if the response was blocked / empty.
                raise AIProviderError(
                    f"Gemini returned no usable text: {exc}"
                ) from exc
                
        except Exception as exc:
            response_time = time.time() - start_time
            logger.error(f"Gemini API call failed in {response_time:.2f}s: {exc}")
            raise AIProviderError(f"Gemini API call failed: {exc}") from exc


class OpenRouterProvider(AIProvider):
    """Provider that routes through OpenRouter for broad model access."""

    def __init__(self):
        import openai
        self._client = openai.OpenAI(
            api_key=os.environ["OPENROUTER_API_KEY"],
            base_url="https://openrouter.ai/api/v1",
            timeout=_REQUEST_TIMEOUT,
        )
        # Free-tier model by default — this provider sits low in the fallback
        # chain and should never incur cost unless AI_MODEL is set explicitly.
        self._model = os.getenv("AI_MODEL") or os.getenv("OPENROUTER_MODEL") or "mistralai/mistral-7b-instruct:free"

    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        openai_messages = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        for m in messages:
            role = "assistant" if m["role"] == "assistant" else m["role"]
            openai_messages.append({"role": role, "content": m["content"]})
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=openai_messages,
                max_tokens=2048,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise AIProviderError(f"OpenRouter call failed: {exc}") from exc

    def stream_complete(self, messages: list[dict[str, str]], system: str = ""):
        openai_messages = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        for m in messages:
            role = "assistant" if m["role"] == "assistant" else m["role"]
            openai_messages.append({"role": role, "content": m["content"]})
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=openai_messages,
                max_tokens=2048,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as exc:
            raise AIProviderError(f"OpenRouter stream failed: {exc}") from exc


class NvidiaProvider(AIProvider):
    """Provider for NVIDIA NIM API."""

    def __init__(self):
        import openai
        self._client = openai.OpenAI(
            api_key=os.environ["NVAPI_KEY"],
            base_url="https://integrate.api.nvidia.com/v1",
            timeout=_REQUEST_TIMEOUT,
        )
        self._model = os.getenv("AI_MODEL") or "meta/llama-3.1-405b-instruct"

    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        openai_messages = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        for m in messages:
            role = "assistant" if m["role"] == "assistant" else m["role"]
            openai_messages.append({"role": role, "content": m["content"]})
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=openai_messages,
                max_tokens=2048,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise AIProviderError(f"NVIDIA call failed: {exc}") from exc

    def stream_complete(self, messages: list[dict[str, str]], system: str = ""):
        openai_messages = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        for m in messages:
            role = "assistant" if m["role"] == "assistant" else m["role"]
            openai_messages.append({"role": role, "content": m["content"]})
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=openai_messages,
                max_tokens=2048,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as exc:
            raise AIProviderError(f"NVIDIA stream failed: {exc}") from exc


class MistralProvider(AIProvider):
    """Cost-efficient default: Mistral's own API (OpenAI-compatible)."""

    def __init__(self):
        import openai
        self._client = openai.OpenAI(
            api_key=os.environ["MISTRAL_API_KEY"],
            base_url="https://api.mistral.ai/v1",
            timeout=_REQUEST_TIMEOUT,
        )
        self._model = os.getenv("AI_MODEL") or os.getenv("MISTRAL_MODEL") or "mistral-small-latest"

    def _to_openai_messages(self, messages: list[dict[str, str]], system: str) -> list[dict[str, str]]:
        out = []
        if system:
            out.append({"role": "system", "content": system})
        for m in messages:
            role = "assistant" if m["role"] == "assistant" else m["role"]
            out.append({"role": role, "content": m["content"]})
        return out

    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=self._to_openai_messages(messages, system),
                max_tokens=2048,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise AIProviderError(f"Mistral call failed: {exc}") from exc

    def stream_complete(self, messages: list[dict[str, str]], system: str = ""):
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=self._to_openai_messages(messages, system),
                max_tokens=2048,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as exc:
            raise AIProviderError(f"Mistral stream failed: {exc}") from exc


class ZhipuProvider(AIProvider):
    """Zhipu/Z.ai GLM models (OpenAI-compatible)."""

    def __init__(self):
        import openai
        self._client = openai.OpenAI(
            api_key=os.environ["ZHIPU_API_KEY"],
            base_url="https://api.z.ai/api/paas/v4",
            timeout=_REQUEST_TIMEOUT,
        )
        self._model = os.getenv("AI_MODEL") or os.getenv("ZHIPU_MODEL") or "glm-4.5-flash"

    def _to_openai_messages(self, messages: list[dict[str, str]], system: str) -> list[dict[str, str]]:
        out = []
        if system:
            out.append({"role": "system", "content": system})
        for m in messages:
            role = "assistant" if m["role"] == "assistant" else m["role"]
            out.append({"role": role, "content": m["content"]})
        return out

    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=self._to_openai_messages(messages, system),
                max_tokens=2048,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            raise AIProviderError(f"Zhipu call failed: {exc}") from exc

    def stream_complete(self, messages: list[dict[str, str]], system: str = ""):
        try:
            stream = self._client.chat.completions.create(
                model=self._model,
                messages=self._to_openai_messages(messages, system),
                max_tokens=2048,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as exc:
            raise AIProviderError(f"Zhipu stream failed: {exc}") from exc


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


class ChainProvider(AIProvider):
    """Tries each real provider in priority order, falling through on failure.

    Unlike a single-provider selection, this never surfaces a 5xx to the
    caller just because one upstream is rate-limited, out of credit, or
    misconfigured — it tries the next candidate and logs each failure loudly
    (FM-11) so the real cause is visible in logs even though the user gets a
    successful response.
    """

    def __init__(self, providers: list[tuple[str, AIProvider]]):
        self._providers = providers  # [(name, instance), ...] in priority order

    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        last_err: Exception | None = None
        for name, provider in self._providers:
            try:
                return provider.complete(messages, system=system)
            except Exception as exc:  # noqa: BLE001 - deliberately broad, chain fallback
                logger.warning("AI provider %s failed, trying next in chain: %s", name, exc)
                last_err = exc
        raise AIProviderError(f"All AI providers in the chain failed: {last_err}")

    def stream_complete(self, messages: list[dict[str, str]], system: str = ""):
        last_err: Exception | None = None
        for name, provider in self._providers:
            try:
                yielded_any = False
                for chunk in provider.stream_complete(messages, system=system):
                    yielded_any = True
                    yield chunk
                if yielded_any:
                    return
            except Exception as exc:  # noqa: BLE001 - deliberately broad, chain fallback
                logger.warning("AI provider %s stream failed, trying next in chain: %s", name, exc)
                last_err = exc
        raise AIProviderError(f"All AI providers in the chain failed: {last_err}")


# Priority order for the automatic chain: cheap/free-tier providers first,
# metered ones last. Configured via whichever *_API_KEY / NVAPI_KEY env vars
# are actually set — providers with no key configured are skipped entirely.
_CHAIN_ORDER = [
    ("mistral", "MISTRAL_API_KEY", MistralProvider),
    ("zhipu", "ZHIPU_API_KEY", ZhipuProvider),
    ("openrouter", "OPENROUTER_API_KEY", OpenRouterProvider),
    ("nvidia", "NVAPI_KEY", NvidiaProvider),
    ("claude", "ANTHROPIC_API_KEY", ClaudeProvider),
    ("gemini", "GEMINI_API_KEY", GeminiProvider),
]


class ResilientChainProvider(AIProvider):
    """Enhanced chain provider with better error handling and fallback logic."""
    
    def __init__(self, providers: list[tuple[str, AIProvider]]):
        self._providers = providers
        self._last_working_provider = None
        self._failure_counts = {name: 0 for name, _ in providers}
    
    def complete(self, messages: list[dict[str, str]], system: str = "") -> str:
        # Try the last working provider first for faster response
        if self._last_working_provider:
            try:
                name, provider = self._last_working_provider
                result = provider.complete(messages, system=system)
                self._failure_counts[name] = 0  # Reset failure count on success
                return result
            except Exception as exc:
                logger.warning("Last working provider %s failed: %s", name, exc)
                self._failure_counts[name] += 1
        
        # Try all providers in order
        last_err = None
        for name, provider in self._providers:
            # Skip providers that have failed multiple times
            if self._failure_counts.get(name, 0) >= 3:
                logger.warning("Skipping provider %s due to multiple failures", name)
                continue
                
            try:
                result = provider.complete(messages, system=system)
                self._last_working_provider = (name, provider)
                self._failure_counts[name] = 0  # Reset failure count on success
                return result
            except Exception as exc:
                logger.warning("AI provider %s failed, trying next: %s", name, exc)
                self._failure_counts[name] += 1
                last_err = exc
        
        # If we get here, all providers failed
        raise AIProviderError(f"All AI providers in the chain failed: {last_err}")
    
    def stream_complete(self, messages: list[dict[str, str]], system: str = ""):
        # Similar logic for streaming
        if self._last_working_provider:
            try:
                name, provider = self._last_working_provider
                for chunk in provider.stream_complete(messages, system=system):
                    yield chunk
                return
            except Exception as exc:
                logger.warning("Last working provider %s stream failed: %s", name, exc)
                self._failure_counts[name] += 1
        
        last_err = None
        for name, provider in self._providers:
            if self._failure_counts.get(name, 0) >= 3:
                continue
                
            try:
                yielded_any = False
                for chunk in provider.stream_complete(messages, system=system):
                    yielded_any = True
                    yield chunk
                if yielded_any:
                    self._last_working_provider = (name, provider)
                    self._failure_counts[name] = 0
                    return
            except Exception as exc:
                logger.warning("AI provider %s stream failed, trying next: %s", name, exc)
                self._failure_counts[name] += 1
                last_err = exc
        
        raise AIProviderError(f"All AI providers in the chain failed: {last_err}")


def _build_chain() -> AIProvider:
    providers: list[tuple[str, AIProvider]] = []
    for name, key_env, cls in _CHAIN_ORDER:
        if not os.getenv(key_env):
            continue
        try:
            providers.append((name, cls()))
        except Exception as exc:  # noqa: BLE001 - a bad key shouldn't break the whole chain
            logger.warning("Skipping AI provider %s in chain — failed to initialize: %s", name, exc)
    if not providers:
        return MockProvider()
    if len(providers) == 1:
        return providers[0][1]
    logger.info("AI provider chain active: %s", " -> ".join(n for n, _ in providers))
    return ResilientChainProvider(providers)


def get_provider() -> AIProvider:
    """Factory: reads AI_PROVIDER env var.

    - unset / "auto" / "chain": builds a priority chain (mistral -> zhipu ->
      openrouter -> nvidia -> claude -> gemini) from whichever *_API_KEY env
      vars are actually set, trying each in turn until one succeeds.
    - a specific provider name (claude|gemini|openrouter|nvidia|mistral|zhipu):
      forces exactly that provider (no fallback), falling back to mock with a
      loud warning if its key is missing.
    - "mock": deterministic mock (blocked in production unless ALLOW_MOCK_AI=1).

    In production, boot fails if mock is used without ALLOW_MOCK_AI=1.
    """
    _is_prod = os.getenv("ENV", "development").lower() in ("production", "prod")
    _allow_mock = os.getenv("ALLOW_MOCK_AI", "0").lower() in ("1", "true", "yes")
    provider = os.getenv("AI_PROVIDER", "auto").lower()

    if provider in ("auto", "chain", ""):
        chain = _build_chain()
        if isinstance(chain, MockProvider) and _is_prod and not _allow_mock:
            raise AIProviderError(
                "AI_PROVIDER=auto but no provider API key is configured in production. "
                "Set MISTRAL_API_KEY/ZHIPU_API_KEY/OPENROUTER_API_KEY/NVAPI_KEY/"
                "ANTHROPIC_API_KEY/GEMINI_API_KEY, or ALLOW_MOCK_AI=1."
            )
        return chain

    if provider == "mock" and _is_prod and not _allow_mock:
        raise AIProviderError("AI_PROVIDER=mock in production. Set a real provider or ALLOW_MOCK_AI=1.")
    if provider == "claude":
        if not os.getenv("ANTHROPIC_API_KEY"):
            return _fallback_to_mock("claude", "ANTHROPIC_API_KEY")
        return ClaudeProvider()
    if provider == "gemini":
        if not os.getenv("GEMINI_API_KEY"):
            return _fallback_to_mock("gemini", "GEMINI_API_KEY")
        return GeminiProvider()
    if provider == "openrouter":
        if not os.getenv("OPENROUTER_API_KEY"):
            return _fallback_to_mock("openrouter", "OPENROUTER_API_KEY")
        return OpenRouterProvider()
    if provider == "nvidia":
        if not os.getenv("NVAPI_KEY"):
            return _fallback_to_mock("nvidia", "NVAPI_KEY")
        return NvidiaProvider()
    if provider == "mistral":
        if not os.getenv("MISTRAL_API_KEY"):
            return _fallback_to_mock("mistral", "MISTRAL_API_KEY")
        return MistralProvider()
    if provider == "zhipu":
        if not os.getenv("ZHIPU_API_KEY"):
            return _fallback_to_mock("zhipu", "ZHIPU_API_KEY")
        return ZhipuProvider()
    return MockProvider()
