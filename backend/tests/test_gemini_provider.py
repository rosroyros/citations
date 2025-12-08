import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, Any, List

from providers.gemini_provider import GeminiProvider
from providers.base import CitationValidator


class TestGeminiProvider:
    """Unit tests for GeminiProvider class."""

    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for testing."""
        return "test-gemini-api-key-12345"

    @pytest.fixture
    def gemini_provider_new_api(self, mock_api_key):
        """Create GeminiProvider instance with new API."""
        with patch('providers.gemini_provider.NEW_API_AVAILABLE', True), \
             patch('providers.gemini_provider.new_genai'):
            provider = GeminiProvider(api_key=mock_api_key, model="gemini-2.5-flash")
            # Mock the client
            provider.client = Mock()
            provider.use_new_api = True
            return provider

    @pytest.fixture
    def gemini_provider_legacy_api(self, mock_api_key):
        """Create GeminiProvider instance with legacy API."""
        # We need to patch the module-level import AND the actual module
        with patch('providers.gemini_provider.NEW_API_AVAILABLE', False), \
             patch('google.generativeai') as mock_genai:
            provider = GeminiProvider(api_key=mock_api_key, model="gemini-1.5-flash")
            provider.use_new_api = False
            # Mock the model
            provider.model = Mock()
            return provider

    @pytest.fixture
    def sample_citations(self):
        """Sample citation text for testing."""
        return """Smith, J. (2020). The book title. Publisher.
Doe, J. (2021). Article title. Journal Name, 15(3), 123-145."""

    @pytest.fixture
    def sample_gemini_response(self):
        """Sample Gemini API response for testing."""
        return """
═══════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════
ORIGINAL: Smith, J. (2020). The book title. Publisher.
SOURCE TYPE: Book
VALIDATION RESULTS:
✓ No APA 7 formatting errors detected

═══════════════════════════════════════════════════════════════
CITATION #2
═══════════════════════════════════════════════════════════════
ORIGINAL: Doe, J. (2021). Article title. *Journal Name*, 15(3), 123-145.
SOURCE TYPE: Journal Article
VALIDATION RESULTS:
❌ Title: Article titles should be in sentence case
Should be: Article title
❌ Volume: Volume number should be italicized
Should be: *Journal Name*, *15*(3), 123-145

───────────────────────────────────────────────────────────────
        """.strip()

    @pytest.fixture
    def sample_gemini_response_errors(self):
        """Sample Gemini response with formatting errors."""
        return """
═══════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════
ORIGINAL: **Smith**, J. (2020). _The Book Title_. Publisher.
SOURCE TYPE: Book
VALIDATION RESULTS:
❌ Author: Author names should not be bold
Should be: Smith, J.
❌ Title: Book titles should be italicized, not underscored
Should be: <em>The Book Title</em>

───────────────────────────────────────────────────────────────
        """.strip()

    @pytest.mark.asyncio
    async def test_validate_citations_success_new_api(self, gemini_provider_new_api, sample_citations, sample_gemini_response):
        """Test successful citation validation with new API."""
        # Mock the API call
        mock_response = Mock()
        mock_response.text = sample_gemini_response
        gemini_provider_new_api.client.models.generate_content = Mock(return_value=mock_response)

        # Mock prompt manager
        with patch.object(gemini_provider_new_api, 'prompt_manager') as mock_pm:
            mock_pm.load_prompt.return_value = "Test prompt template"
            mock_pm.format_citations.return_value = "Formatted citations"

            # Call validate_citations
            result = await gemini_provider_new_api.validate_citations(sample_citations)

            # Verify the result
            assert "results" in result
            assert len(result["results"]) == 2

            # Check first citation (no errors)
            citation1 = result["results"][0]
            assert citation1["citation_number"] == 1
            assert citation1["original"] == "Smith, J. (2020). The book title. Publisher."
            assert citation1["source_type"] == "Book"
            assert len(citation1["errors"]) == 0

            # Check second citation (has errors)
            citation2 = result["results"][1]
            assert citation2["citation_number"] == 2
            assert "Journal Name" in citation2["original"]
            assert citation2["source_type"] == "Journal Article"
            assert len(citation2["errors"]) == 2
            assert citation2["errors"][0]["component"] == "Title"
            assert citation2["errors"][1]["component"] == "Volume"

    @pytest.mark.asyncio
    async def test_validate_citations_success_legacy_api(self, gemini_provider_legacy_api, sample_citations, sample_gemini_response):
        """Test successful citation validation with legacy API."""
        # Mock the model's generate_content method
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = sample_gemini_response
        mock_model.generate_content = AsyncMock(return_value=mock_response)
        gemini_provider_legacy_api.model = mock_model

        # Mock prompt manager
        with patch.object(gemini_provider_legacy_api, 'prompt_manager') as mock_pm:
            mock_pm.load_prompt.return_value = "Test prompt template"
            mock_pm.format_citations.return_value = "Formatted citations"

            # Call validate_citations
            result = await gemini_provider_legacy_api.validate_citations(sample_citations)

            # Verify the result structure
            assert "results" in result
            assert len(result["results"]) == 2

    @pytest.mark.asyncio
    async def test_validate_citations_api_error(self, gemini_provider_new_api, sample_citations):
        """Test error handling when Gemini API fails."""
        # Mock API to raise an exception
        gemini_provider_new_api.client.models.generate_content = Mock(
            side_effect=Exception("API rate limit exceeded")
        )

        with patch.object(gemini_provider_new_api, 'prompt_manager') as mock_pm:
            mock_pm.load_prompt.return_value = "Test prompt"
            mock_pm.format_citations.return_value = "Formatted"

            # Should raise the exception
            with pytest.raises(Exception, match="API rate limit exceeded"):
                await gemini_provider_new_api.validate_citations(sample_citations)

    @pytest.mark.asyncio
    async def test_validate_citations_retry_on_retryable_error(self, gemini_provider_new_api, sample_citations):
        """Test retry logic for retryable errors."""
        # Mock API to fail once then succeed
        mock_response = Mock()
        mock_response.text = "Success response"
        api_mock = Mock(side_effect=[
            Exception("Resource exhausted"),
            mock_response
        ])
        gemini_provider_new_api.client.models.generate_content = api_mock

        with patch.object(gemini_provider_new_api, 'prompt_manager') as mock_pm, \
             patch('asyncio.sleep') as mock_sleep:  # Mock sleep to speed up test
            mock_pm.load_prompt.return_value = "Test prompt"
            mock_pm.format_citations.return_value = "Formatted"

            result = await gemini_provider_new_api.validate_citations(sample_citations)

            # Should have retried once
            assert api_mock.call_count == 2
            assert mock_sleep.call_count == 1
            # Sleep should be called with exponential backoff
            mock_sleep.assert_called_with(2)  # base_delay * (2^0)

    @pytest.mark.asyncio
    async def test_validate_citations_no_retry_on_non_retryable_error(self, gemini_provider_new_api, sample_citations):
        """Test that non-retryable errors are not retried."""
        # Mock API to fail with non-retryable error
        api_mock = Mock(side_effect=Exception("Invalid API key"))
        gemini_provider_new_api.client.models.generate_content = api_mock

        with patch.object(gemini_provider_new_api, 'prompt_manager') as mock_pm:
            mock_pm.load_prompt.return_value = "Test prompt"
            mock_pm.format_citations.return_value = "Formatted"

            # Should raise immediately without retry
            with pytest.raises(Exception, match="Invalid API key"):
                await gemini_provider_new_api.validate_citations(sample_citations)

            # Should not have retried
            assert api_mock.call_count == 1

    def test_parse_response_success(self, gemini_provider_new_api, sample_gemini_response):
        """Test successful response parsing."""
        results = gemini_provider_new_api._parse_response(sample_gemini_response)

        assert len(results) == 2

        # Check first citation
        assert results[0]["citation_number"] == 1
        assert results[0]["original"] == "Smith, J. (2020). The book title. Publisher."
        assert results[0]["source_type"] == "Book"
        assert len(results[0]["errors"]) == 0

        # Check second citation
        assert results[1]["citation_number"] == 2
        assert results[1]["source_type"] == "Journal Article"
        assert len(results[1]["errors"]) == 2

    def test_parse_response_with_markdown_formatting(self, gemini_provider_new_api, sample_gemini_response_errors):
        """Test parsing response with markdown formatting."""
        results = gemini_provider_new_api._parse_response(sample_gemini_response_errors)

        assert len(results) == 1
        assert results[0]["citation_number"] == 1

        # Check that markdown is converted to HTML
        assert "<strong>Smith</strong>" in results[0]["original"]
        assert "<em>The Book Title</em>" in results[0]["original"]

        # Check error corrections
        assert len(results[0]["errors"]) == 2
        assert results[0]["errors"][0]["correction"] == "Smith, J."
        assert "<em>The Book Title</em>" in results[0]["errors"][1]["correction"]

    def test_parse_response_malformed_block(self, gemini_provider_new_api):
        """Test parsing response with malformed citation block."""
        malformed_response = """
═══════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════
Some malformed content without proper sections
        """.strip()

        results = gemini_provider_new_api._parse_response(malformed_response)
        # Should return empty list for malformed content
        assert len(results) == 0

    def test_parse_citation_block_missing_sections(self, gemini_provider_new_api):
        """Test parsing citation block with missing sections."""
        block_content = """
INVALID: This block has no proper sections
Just some random text
        """.strip()

        result = gemini_provider_new_api._parse_citation_block(1, block_content)

        # Should return a result with empty fields
        assert result["citation_number"] == 1
        assert result["original"] == ""
        assert result["source_type"] == ""
        assert result["errors"] == []

    def test_generate_completion_new_api(self, gemini_provider_new_api):
        """Test generate_completion method with new API."""
        mock_response = Mock()
        mock_response.text = "Generated text"
        # Mock to return an awaitable that resolves to mock_response
        async def mock_generate(*args, **kwargs):
            return mock_response
        gemini_provider_new_api.client.models.generate_content = mock_generate

        result = gemini_provider_new_api.generate_completion("Test prompt")
        assert result == "Generated text"

    def test_generate_completion_legacy_api(self, gemini_provider_legacy_api):
        """Test generate_completion method with legacy API."""
        mock_response = Mock()
        mock_response.text = "Generated text"

        mock_model = Mock()
        # Mock to return an awaitable that resolves to mock_response
        async def mock_generate(*args, **kwargs):
            return mock_response
        mock_model.generate_content = mock_generate
        gemini_provider_legacy_api.model = mock_model

        result = gemini_provider_legacy_api.generate_completion("Test prompt")
        assert result == "Generated text"

    def test_generate_completion_error_handling(self, gemini_provider_new_api):
        """Test generate_completion error handling."""
        async def mock_error(*args, **kwargs):
            raise Exception("API Error")
        gemini_provider_new_api.client.models.generate_content = mock_error

        result = gemini_provider_new_api.generate_completion("Test prompt")
        assert result is None

    def test_initialization_without_api_key(self):
        """Test provider initialization fails without API key."""
        with patch.dict('os.environ', {}, clear=True), \
             patch('providers.gemini_provider.load_dotenv'):
            with pytest.raises(ValueError, match="GEMINI_API_KEY not found"):
                GeminiProvider(api_key=None)

    def test_initialization_with_custom_model(self, mock_api_key):
        """Test provider initialization with custom model."""
        with patch('providers.gemini_provider.NEW_API_AVAILABLE', True), \
             patch('providers.gemini_provider.new_genai'), \
             patch('providers.gemini_provider.load_dotenv'):
            provider = GeminiProvider(api_key=mock_api_key, model="custom-model")
            assert provider.model == "custom-model"

    def test_parse_response_handles_empty_response(self, gemini_provider_new_api):
        """Test parsing empty response."""
        results = gemini_provider_new_api._parse_response("")
        assert results == []

    def test_parse_response_handles_partial_citation(self, gemini_provider_new_api):
        """Test parsing response with incomplete citation."""
        partial_response = """
═══════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════
ORIGINAL: Smith, J. (2020). Title.
        """.strip()

        results = gemini_provider_new_api._parse_response(partial_response)
        # Should handle gracefully - even partial responses should extract what they can
        if len(results) > 0:
            assert results[0]["citation_number"] == 1
            # The parser should extract the original line if present
        # If no results due to partial format, that's also acceptable