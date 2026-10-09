"""Tests for LLM service provider abstraction and Groq provider."""

from unittest.mock import MagicMock, patch
import pytest
from app.services.llm_service import (
    GroqProvider,
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMOutputParsingError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    get_llm_provider,
)


def test_groq_provider_missing_key_raises():
    """Verify GroqProvider raises LLMConfigurationError if API key is not configured."""
    provider = GroqProvider(api_key=None)
    with pytest.raises(LLMConfigurationError, match="Groq API key is not configured"):
        provider.generate_chat_completion([{"role": "user", "content": "Hello"}])

    provider_empty = GroqProvider(api_key="   ")
    with pytest.raises(LLMConfigurationError, match="Groq API key is not configured"):
        provider_empty.generate_chat_completion([{"role": "user", "content": "Hello"}])


def test_groq_provider_successful_completion():
    """Verify GroqProvider formats request and returns message content."""
    provider = GroqProvider(api_key="gsk_test_key_valid", model_name="llama-3.3-70b-versatile")

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"executive_summary": "Meeting concluded successfully."}'
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])

    provider._client = mock_client

    result = provider.generate_chat_completion(
        messages=[{"role": "user", "content": "Analyze this"}],
        temperature=0.1,
        max_tokens=2048,
    )

    assert 'Meeting concluded successfully.' in result
    mock_client.chat.completions.create.assert_called_once_with(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "Analyze this"}],
        temperature=0.1,
        max_tokens=2048,
    )


def test_groq_provider_authentication_error():
    """Verify AuthenticationError is mapped to LLMAuthenticationError."""
    provider = GroqProvider(api_key="gsk_invalid_key")
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("AuthenticationError: 401 Invalid API Key")
    provider._client = mock_client

    with pytest.raises(LLMAuthenticationError, match="Authentication failed"):
        provider.generate_chat_completion([{"role": "user", "content": "Hello"}])


def test_groq_provider_rate_limit_error():
    """Verify RateLimitError is mapped to LLMRateLimitError."""
    provider = GroqProvider(api_key="gsk_valid_key")
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("RateLimitError: 429 TPM limit exceeded")
    provider._client = mock_client

    with pytest.raises(LLMRateLimitError, match="rate limit or quota exceeded"):
        provider.generate_chat_completion([{"role": "user", "content": "Hello"}])


def test_groq_provider_timeout_error():
    """Verify APITimeoutError is mapped to LLMTimeoutError."""
    provider = GroqProvider(api_key="gsk_valid_key")
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("APITimeoutError: Request timed out after 60s")
    provider._client = mock_client

    with pytest.raises(LLMTimeoutError, match="timed out"):
        provider.generate_chat_completion([{"role": "user", "content": "Hello"}])
