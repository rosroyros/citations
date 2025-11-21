import pytest
import asyncio
from unittest.mock import AsyncMock, patch, call, Mock
from openai import APITimeoutError, RateLimitError, AuthenticationError, APIError
from backend.providers.openai_provider import OpenAIProvider


class TestOpenAIRetryLogic:
    """Test retry logic with exponential backoff for OpenAI provider."""

    @pytest.fixture
    def provider(self):
        """Create OpenAI provider for testing."""
        return OpenAIProvider(api_key="test-key", model="gpt-4o-mini")

    @pytest.mark.asyncio
    async def test_retry_on_timeout_error_success_after_retries(self, provider):
        """Test that APITimeoutError triggers retry and eventually succeeds."""
        mock_client = AsyncMock()

        # Simulate 2 timeouts then success
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        mock_client.chat.completions.create.side_effect = [
            APITimeoutError(request=Mock()),
            APITimeoutError(request=Mock()),
            mock_response
        ]

        provider.client = mock_client

        with patch('asyncio.sleep') as mock_sleep:
            result = await provider.validate_citations("test citation")

        # Should have made 3 attempts total
        assert mock_client.chat.completions.create.call_count == 3

        # Should have slept 2 times between retries
        assert mock_sleep.call_count == 2
        mock_sleep.assert_has_calls([call(2), call(4)])  # 2s, 4s exponential backoff

        # Should return successful result
        assert "results" in result

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit_error_success_after_retries(self, provider):
        """Test that RateLimitError triggers retry and eventually succeeds."""
        mock_client = AsyncMock()

        # Simulate 1 rate limit then success
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        mock_client.chat.completions.create.side_effect = [
            RateLimitError(
                message="Rate limit exceeded",
                response=Mock(),
                body=Mock()
            ),
            mock_response
        ]

        provider.client = mock_client

        with patch('asyncio.sleep') as mock_sleep:
            result = await provider.validate_citations("test citation")

        # Should have made 2 attempts total
        assert mock_client.chat.completions.create.call_count == 2

        # Should have slept 1 time between retries
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_with(2)  # 2s first retry delay

        # Should return successful result
        assert "results" in result

    @pytest.mark.asyncio
    async def test_max_retries_exceeded_raises_error(self, provider):
        """Test that after max retries, ValueError is raised."""
        mock_client = AsyncMock()

        # Simulate timeout on all 3 attempts
        mock_client.chat.completions.create.side_effect = APITimeoutError(request=Mock())

        provider.client = mock_client

        with patch('asyncio.sleep'):
            with pytest.raises(ValueError, match="Request timed out after multiple retries"):
                await provider.validate_citations("test citation")

        # Should have made exactly 3 attempts
        assert mock_client.chat.completions.create.call_count == 3

    @pytest.mark.asyncio
    async def test_no_retry_on_authentication_error(self, provider):
        """Test that AuthenticationError does not trigger retry."""
        mock_client = AsyncMock()

        mock_client.chat.completions.create.side_effect = AuthenticationError(
            message="Invalid API key",
            response=Mock(),
            body=Mock()
        )

        provider.client = mock_client

        with patch('asyncio.sleep') as mock_sleep:
            with pytest.raises(ValueError, match="Invalid OpenAI API key"):
                await provider.validate_citations("test citation")

        # Should have made only 1 attempt (no retries)
        assert mock_client.chat.completions.create.call_count == 1
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_retry_on_api_error(self, provider):
        """Test that APIError does not trigger retry."""
        mock_client = AsyncMock()

        mock_client.chat.completions.create.side_effect = APIError(
            message="API error",
            request=Mock(),
            body=Mock()
        )

        provider.client = mock_client

        with patch('asyncio.sleep') as mock_sleep:
            with pytest.raises(ValueError, match="OpenAI API error"):
                await provider.validate_citations("test citation")

        # Should have made only 1 attempt (no retries)
        assert mock_client.chat.completions.create.call_count == 1
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_retry_logging_warnings(self, provider):
        """Test that retry attempts are logged with warning level."""
        mock_client = AsyncMock()

        # Simulate 1 timeout then success
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30

        mock_client.chat.completions.create.side_effect = [
            APITimeoutError(request=Mock()),
            mock_response
        ]

        provider.client = mock_client

        with patch('asyncio.sleep'):
            with patch('backend.providers.openai_provider.logger') as mock_logger:
                await provider.validate_citations("test citation")

                # Should log retry attempt with warning level
                mock_logger.warning.assert_called()
                warning_call = mock_logger.warning.call_args[0][0]
                assert "OpenAI API error" in warning_call
                assert "attempt 1/3" in warning_call
                assert "Retrying in 2s" in warning_call