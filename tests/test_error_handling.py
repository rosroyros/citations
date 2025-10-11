"""
Tests for error handling in the validation API.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from openai import APIError, APITimeoutError, RateLimitError, AuthenticationError
from backend.providers.openai_provider import OpenAIProvider


@pytest.mark.asyncio
async def test_timeout_error_handled():
    """Test that API timeouts raise ValueError with user-friendly message."""
    # Create provider with mocked client (use dummy API key for tests)
    provider = OpenAIProvider(api_key="test-key-123")

    # Mock the client's chat.completions.create to raise timeout error
    provider.client.chat.completions.create = AsyncMock(
        side_effect=APITimeoutError("Request timed out")
    )

    with pytest.raises(ValueError) as exc_info:
        await provider.validate_citations("Test citation", "apa7")

    assert "timed out" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_authentication_error_handled():
    """Test that authentication errors raise ValueError with clear message."""
    provider = OpenAIProvider(api_key="test-key-123")

    # Create proper AuthenticationError with required params
    mock_response = MagicMock()
    mock_response.status_code = 401
    error = AuthenticationError("Invalid API key", response=mock_response, body={})

    provider.client.chat.completions.create = AsyncMock(side_effect=error)

    with pytest.raises(ValueError) as exc_info:
        await provider.validate_citations("Test citation", "apa7")

    assert "api key" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_rate_limit_error_handled():
    """Test that rate limit errors raise ValueError with helpful message."""
    provider = OpenAIProvider(api_key="test-key-123")

    # Create proper RateLimitError with required params
    mock_response = MagicMock()
    mock_response.status_code = 429
    error = RateLimitError("Rate limit exceeded", response=mock_response, body={})

    provider.client.chat.completions.create = AsyncMock(side_effect=error)

    with pytest.raises(ValueError) as exc_info:
        await provider.validate_citations("Test citation", "apa7")

    assert "rate limit" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_generic_api_error_handled():
    """Test that generic API errors are caught and wrapped."""
    provider = OpenAIProvider(api_key="test-key-123")

    # Use generic Exception to simulate API error
    provider.client.chat.completions.create = AsyncMock(
        side_effect=Exception("Something went wrong")
    )

    # Should raise the exception since it's not a specific OpenAI error
    with pytest.raises(Exception):
        await provider.validate_citations("Test citation", "apa7")


@pytest.mark.asyncio
async def test_empty_response_handled():
    """Test that empty/malformed LLM responses are handled gracefully."""
    provider = OpenAIProvider(api_key="test-key-123")

    # Mock response with empty content
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = ""
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 0
    mock_response.usage.total_tokens = 100

    provider.client.chat.completions.create = AsyncMock(return_value=mock_response)

    result = await provider.validate_citations("Test citation", "apa7")

    # Should return empty results, not crash
    assert "results" in result
    assert isinstance(result["results"], list)
