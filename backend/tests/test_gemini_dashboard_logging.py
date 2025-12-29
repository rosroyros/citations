#!/usr/bin/env python3
"""Tests for Gemini provider dashboard logging functionality."""

import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from providers.gemini_provider import GeminiProvider


class TestGeminiDashboardLogging:
    """Test that Gemini provider logs duration and token usage correctly."""

    @pytest.fixture
    def provider(self):
        """Create a Gemini provider instance for testing."""
        with patch.dict('os.environ', {'GEMINI_API_KEY': 'test-key'}):
            return GeminiProvider(api_key="test-key")

    async def test_new_api_with_response_logs_tokens(self, provider):
        """Test that _call_new_api_with_response returns full response object."""
        mock_response = MagicMock()
        mock_response.text = "Test response"

        # Mock the client.models.generate_content method
        provider.client.models.generate_content = MagicMock(return_value=mock_response)

        result = await provider._call_new_api_with_response("Test prompt")

        assert result == mock_response
        assert hasattr(result, 'text')

    async def test_validate_citations_logs_token_usage(self, provider):
        """Test that validate_citations logs token usage from usage_metadata."""
        # Create mock response with usage_metadata
        mock_response = MagicMock()
        mock_response.text = "CITATION #1\n═══\nTest content"

        # Create mock usage_metadata with correct field names (Gemini API uses snake_case in Python SDK)
        mock_usage = MagicMock()
        mock_usage.prompt_token_count = 150
        mock_usage.total_token_count = 350
        mock_usage.candidates_token_count = 200
        mock_response.usage_metadata = mock_usage

        with patch.object(provider, '_call_new_api_with_response', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            # Capture logger output
            with patch('providers.gemini_provider.logger.info') as mock_logger:
                result = await provider.validate_citations("Test citation")

                # Verify token usage was logged with correct calculation
                mock_logger.assert_any_call("Token usage: 150 prompt + 200 completion = 350 total")

    async def test_validate_citations_handles_missing_usage_metadata(self, provider):
        """Test that validate_citations handles missing usage_metadata gracefully."""
        # Create mock response without usage_metadata
        mock_response = MagicMock()
        mock_response.text = "Test response"
        del mock_response.usage_metadata  # Ensure attribute doesn't exist

        with patch.object(provider, '_call_new_api_with_response', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_response

            # Should not raise an exception
            result = await provider.validate_citations("Test citation")
            assert result is not None

    async def test_legacy_api_logs_na(self, provider):
        """Test that legacy API logs 'N/A' for token usage."""
        provider.use_new_api = False  # Force legacy API

        with patch.object(provider, '_call_legacy_api', new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "Test response"

            with patch('providers.gemini_provider.logger.info') as mock_logger:
                result = await provider.validate_citations("Test citation")

                # Should log N/A for legacy API
                mock_logger.assert_any_call("Token usage: N/A (legacy API)")

    def test_duration_parsing_compatibility(self):
        """Test that our logging format is compatible with the dashboard parser."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from dashboard.log_parser import extract_duration, extract_token_usage

        # Test duration extraction
        duration_line = "2025-12-09 11:00:03 Gemini API call completed in 1.234s"
        duration = extract_duration(duration_line)
        assert duration == 1.234, f"Expected 1.234, got {duration}"

        # Test token usage extraction
        token_line = "2025-12-09 11:00:03 Token usage: 150 prompt + 200 completion = 350 total"
        token_usage = extract_token_usage(token_line)
        assert token_usage == {
            "prompt": 150,
            "completion": 200,
            "total": 350
        }, f"Unexpected token usage: {token_usage}"

    async def test_token_calculation_edge_cases(self, provider):
        """Test token calculation with various edge cases."""
        test_cases = [
            (0, 0, 0),  # No tokens
            (100, 100, 0),  # Only prompt tokens
            (50, 200, 150),  # Normal case
            (1000, 1000, 0),  # Prompt equals total (edge case)
        ]

        for prompt_tokens, total_tokens, expected_output in test_cases:
            mock_response = MagicMock()
            mock_response.text = "Test"

            mock_usage = MagicMock()
            mock_usage.prompt_token_count = prompt_tokens
            mock_usage.total_token_count = total_tokens
            # calculate completion tokens for the mock based on the test case
            # The test case structure is (prompt, output, total) based on usages in loop
            # But the loop unwrapping is: prompt_tokens, using output as total_tokens, and expected_output as completion??
            # Wait, line 117: for prompt_tokens, total_tokens, expected_output in test_cases:
            # But the assertions:
            # assert f"{expected_output} completion" in log_msg (line 139)
            # So expected_output IS the completion tokens.
            mock_usage.candidates_token_count = expected_output 
            mock_response.usage_metadata = mock_usage

            with patch.object(provider, '_call_new_api_with_response', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = mock_response

                with patch('providers.gemini_provider.logger.info') as mock_logger:
                    await provider.validate_citations("Test")

                    # Find the token usage log call
                    token_calls = [call for call in mock_logger.call_args_list
                                 if "Token usage:" in str(call)]
                    assert len(token_calls) == 1

                    log_msg = str(token_calls[0])
                    assert f"{prompt_tokens} prompt" in log_msg
                    assert f"{expected_output} completion" in log_msg
                    assert f"{total_tokens} total" in log_msg

    def test_openai_compatibility(self):
        """Verify our log format doesn't break OpenAI parsing."""
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from dashboard.log_parser import extract_token_usage

        # OpenAI format (should still work)
        openai_line = "Token usage: 300 input + 400 output = 700 total"
        openai_tokens = extract_token_usage(openai_line)
        assert openai_tokens == {"prompt": 300, "completion": 400, "total": 700}

        # Our Gemini format (should also work)
        gemini_line = "Token usage: 150 prompt + 200 completion = 350 total"
        gemini_tokens = extract_token_usage(gemini_line)
        assert gemini_tokens == {"prompt": 150, "completion": 200, "total": 350}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])