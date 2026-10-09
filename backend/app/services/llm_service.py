"""LLM Provider abstraction and Groq Cloud client implementation."""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)


# --- Domain Exceptions ---


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    pass


class LLMConfigurationError(LLMProviderError):
    """Raised when LLM provider is not properly configured (e.g., missing API key)."""
    pass


class LLMAuthenticationError(LLMProviderError):
    """Raised when LLM provider authentication/API key is invalid."""
    pass


class LLMRateLimitError(LLMProviderError):
    """Raised when LLM provider rate limit or quota is exceeded."""
    pass


class LLMTimeoutError(LLMProviderError):
    """Raised when LLM provider request times out."""
    pass


class LLMOutputParsingError(LLMProviderError):
    """Raised when the LLM returns unparseable or schema-violating output."""
    pass


# --- Abstract Base Interface ---


class BaseLLMProvider(ABC):
    """Abstract interface for large language model providers."""

    @abstractmethod
    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """Generate a text completion from chat messages.

        Args:
            messages: List of message dictionaries containing 'role' and 'content'.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens in response.
            response_format: Optional response format (e.g., {"type": "json_object"}).

        Returns:
            Completed response string.

        Raises:
            LLMProviderError: On any provider or communication failure.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the LLM provider."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the active model name."""
        pass


# --- Groq Provider Implementation ---


class GroqProvider(BaseLLMProvider):
    """Official Groq Cloud LLM provider implementation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "qwen/qwen3.8-27b",
        timeout: float = 60.0,
    ) -> None:
        """Initialize Groq client provider with configuration parameters."""
        self._api_key = api_key
        self._model_name = model_name
        self._timeout = timeout
        self._client: Optional[Any] = None

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_client(self):
        """Lazily initialize and return the Groq SDK client."""
        if not self._api_key or not self._api_key.strip() or self._api_key == "your_groq_api_key_here":
            raise LLMConfigurationError(
                "Groq API key is not configured. Please set the GROQ_API_KEY environment variable."
            )

        if self._client is None:
            try:
                from groq import Groq

                self._client = Groq(
                    api_key=self._api_key.strip(),
                    timeout=self._timeout,
                )
            except ImportError as e:
                raise LLMConfigurationError(
                    "The 'groq' Python package is not installed."
                ) from e
            except Exception as e:
                raise LLMProviderError(f"Failed to initialize Groq client: {str(e)}") from e

        return self._client

    def generate_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """Send chat messages to Groq and return text completion content."""
        client = self._get_client()

        kwargs: Dict[str, Any] = {
            "model": self._model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        try:
            logger.info("Dispatching Groq chat completion (model=%s)...", self._model_name)
            response = client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            content = choice.message.content
            if not content:
                raise LLMOutputParsingError("Received empty response content from Groq.")
            return content.strip()

        except LLMConfigurationError:
            raise
        except Exception as e:
            err_type = type(e).__name__
            err_msg = str(e)
            logger.error("Groq API error (%s): %s", err_type, err_msg)

            err_lower = f"{err_type} {err_msg}".lower()

            if "authentication" in err_lower or "invalid api key" in err_lower or "401" in err_lower:
                raise LLMAuthenticationError(
                    "Authentication failed with Groq API. Please verify your GROQ_API_KEY."
                ) from e
            elif "ratelimit" in err_lower or "rate limit" in err_lower or "429" in err_lower:
                raise LLMRateLimitError(
                    "Groq API rate limit or quota exceeded. Please retry after a brief delay."
                ) from e
            elif "timeout" in err_lower:
                raise LLMTimeoutError(
                    "Groq API request timed out. The meeting content may be too large or the server is busy."
                ) from e
            else:
                raise LLMProviderError(
                    f"An error occurred while communicating with Groq: {err_msg}"
                ) from e


def get_llm_provider() -> BaseLLMProvider:
    """Dependency helper returning the configured LLM provider instance."""
    settings = get_settings()
    if settings.LLM_PROVIDER.lower() == "groq":
        return GroqProvider(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
    # Default to Groq provider
    return GroqProvider(
        api_key=settings.GROQ_API_KEY,
        model_name=settings.GROQ_MODEL,
        timeout=settings.LLM_TIMEOUT_SECONDS,
    )
