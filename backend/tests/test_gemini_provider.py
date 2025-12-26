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
            provider.model = "gemini-1.5-flash"
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
CORRECTED CITATION:
Doe, J. (2021). Article title. *Journal Name*, *15*(3), 123-145.
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
CORRECTED CITATION:
Smith, J. (2020). _The Book Title_. Publisher.
───────────────────────────────────────────────────────────────
        """.strip()

    @pytest.mark.asyncio
    async def test_validate_citations_success_new_api(self, gemini_provider_new_api, sample_citations, sample_gemini_response):
        """Test successful citation validation with new API."""
        # Mock the API call
        mock_response = Mock()
        mock_response.text = sample_gemini_response
        mock_response.text = sample_gemini_response
        # Mock metadata for logging
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 10
        mock_response.usage_metadata.total_token_count = 20
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
            assert citation2.get("corrected_citation") is not None
            assert "Article title" in citation2["corrected_citation"]
            assert "<em>Journal Name</em>" in citation2["corrected_citation"]

    @pytest.mark.asyncio
    async def test_validate_citations_success_legacy_api(self, gemini_provider_legacy_api, sample_citations, sample_gemini_response):
        """Test successful citation validation with legacy API."""
        # Mock the response
        mock_response = Mock()
        mock_response.text = sample_gemini_response
        
        # Patch GenerativeModel to return our mock
        with patch('google.generativeai.GenerativeModel') as mock_model_cls:
            mock_model_instance = Mock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_model_cls.return_value = mock_model_instance
            
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
        
        # Mock metadata for logging
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 10
        mock_response.usage_metadata.total_token_count = 20

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
        # Should return a result but with empty fields
        assert len(results) == 1
        assert results[0]["original"] == ""
        assert results[0]["errors"] == []

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
        # Mock to return mock_response directly (synchronous call)
        gemini_provider_new_api.client.models.generate_content = Mock(return_value=mock_response)

        result = gemini_provider_new_api.generate_completion("Test prompt")
        assert result == "Generated text"

    def test_generate_completion_legacy_api(self, gemini_provider_legacy_api):
        """Test generate_completion method with legacy API."""
        mock_response = Mock()
        mock_response.text = "Generated text"

        # The legacy API creates a new model instance, so we must mock the class
        with patch('google.generativeai.GenerativeModel') as mock_model_cls:
            mock_model_instance = Mock()
            mock_model_instance.generate_content.return_value = mock_response
            mock_model_cls.return_value = mock_model_instance
            
            result = gemini_provider_legacy_api.generate_completion("Test prompt")
            assert result == "Generated text"

    def test_generate_completion_error_handling(self, gemini_provider_new_api):
        """Test generate_completion error handling."""
        gemini_provider_new_api.client.models.generate_content = Mock(
            side_effect=Exception("API Error")
        )

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

    def test_parse_response_corrected_citation_multiline(self, gemini_provider_new_api):
        """Test parsing of multi-line corrected citation."""
        response = """
═══════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════
ORIGINAL: Smith, J. (2020). WRONG Title. Publisher.
SOURCE TYPE: Book
VALIDATION RESULTS:
❌ Title: Error found
Should be: Correct Title

───────────────────────────────────────────────────────────────
CORRECTED CITATION:
Smith, J. (2020).
Correct Title.
Publisher.
───────────────────────────────────────────────────────────────
        """.strip()
        
        results = gemini_provider_new_api._parse_response(response)
        assert len(results) == 1
        # Should join lines with space
        assert results[0].get("corrected_citation") == "Smith, J. (2020). Correct Title. Publisher."

    def test_corrected_citation_discarded_when_no_errors(self, gemini_provider_new_api):
        """Test that corrected citation is discarded if no errors found."""
        response = """
═══════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════
ORIGINAL: Smith, J. (2020). Title. Publisher.
SOURCE TYPE: Book
VALIDATION RESULTS:
✓ No APA 7 formatting errors detected

───────────────────────────────────────────────────────────────
CORRECTED CITATION:
Different Text
───────────────────────────────────────────────────────────────
        """.strip()
        
        results = gemini_provider_new_api._parse_response(response)
        assert len(results) == 1
        assert results[0].get("corrected_citation") is None

    def test_corrected_citation_discarded_when_identical(self, gemini_provider_new_api):
       """Test that corrected citation is discarded if identical to original."""
       response = """
═══════════════════════════════════════════════════════════════
CITATION #1
═══════════════════════════════════════════════════════════════
ORIGINAL: Smith, J. (2020). _Title_. Publisher.
SOURCE TYPE: Book
VALIDATION RESULTS:
❌ Random: Error
Should be: fix

───────────────────────────────────────────────────────────────
CORRECTED CITATION:
Smith, J. (2020). _Title_. Publisher.
───────────────────────────────────────────────────────────────
       """.strip()
       
       results = gemini_provider_new_api._parse_response(response)
       assert len(results) == 1
       assert results[0].get("corrected_citation") is None

    def test_format_markdown_to_html(self, gemini_provider_new_api):
        """Test markdown to HTML conversion helper."""
        input_text = "This is **bold** and _italic_ and *other italic*."
        expected = "This is <strong>bold</strong> and <em>italic</em> and <em>other italic</em>."
        assert gemini_provider_new_api._format_markdown_to_html(input_text) == expected
        
        # Test empty
        assert gemini_provider_new_api._format_markdown_to_html("") == ""
        assert gemini_provider_new_api._format_markdown_to_html(None) is None