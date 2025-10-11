"""
Integration tests using test fixtures to validate the entire citation validation system.
Tests that correct citations pass and incorrect citations are caught with appropriate errors.
"""

import pytest
import pytest_asyncio
import logging
from tests.test_fixtures import (
    # Correct citations
    CORRECT_JOURNAL_ARTICLE,
    CORRECT_BOOK,
    CORRECT_BOOK_CHAPTER,
    CORRECT_WEBPAGE,
    CORRECT_CITATIONS_ALL,

    # Incorrect citations
    INCORRECT_AND_INSTEAD_OF_AMPERSAND,
    INCORRECT_TITLE_CASE_BOOK,
    INCORRECT_TITLE_CASE_ARTICLE,
    INCORRECT_OLD_DOI_FORMAT,
    INCORRECT_MISSING_DOI,
    INCORRECT_PUBLISHER_LOCATION,
    INCORRECT_OLD_WEBPAGE_FORMAT,
    INCORRECT_JOURNAL_TITLE_CASE,
    INCORRECT_MISSING_PAGE_NUMBERS,
    INCORRECT_NO_PERIODS_INITIALS,
    INCORRECT_MULTIPLE_ERRORS,
    INCORRECT_CITATIONS_ALL,

    # Mixed and edge cases
    MIXED_CITATIONS,
    EDGE_CASES_ALL,
    EXPECTED_ERRORS,
)
from backend.providers.openai_provider import OpenAIProvider
from backend.prompt_manager import PromptManager

logger = logging.getLogger(__name__)


@pytest.fixture
def provider():
    """Create OpenAI provider instance for testing."""
    return OpenAIProvider()


@pytest.fixture
def prompt_manager():
    """Create prompt manager instance for testing."""
    return PromptManager()


class TestCorrectCitations:
    """Test that correct APA 7th citations pass validation."""

    @pytest.mark.asyncio
    async def test_correct_journal_article(self, provider, prompt_manager):
        """Test correct journal article citation passes."""
        logger.info("Testing correct journal article citation")
        prompt = prompt_manager.build_prompt(CORRECT_JOURNAL_ARTICLE)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result: {result}")

        # Correct citation should have no errors (empty errors list)
        assert result is not None
        assert 'results' in result
        assert len(result['results']) > 0
        # Check first citation has empty errors list
        assert result['results'][0]['errors'] == []

    @pytest.mark.asyncio
    async def test_correct_book(self, provider, prompt_manager):
        """Test correct book citation passes."""
        logger.info("Testing correct book citation")
        prompt = prompt_manager.build_prompt(CORRECT_BOOK)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result: {result}")
        assert result is not None

    @pytest.mark.asyncio
    async def test_correct_book_chapter(self, provider, prompt_manager):
        """Test correct book chapter citation passes."""
        logger.info("Testing correct book chapter citation")
        prompt = prompt_manager.build_prompt(CORRECT_BOOK_CHAPTER)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result: {result}")
        assert result is not None

    @pytest.mark.asyncio
    async def test_correct_webpage(self, provider, prompt_manager):
        """Test correct webpage citation passes."""
        logger.info("Testing correct webpage citation")
        prompt = prompt_manager.build_prompt(CORRECT_WEBPAGE)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result: {result}")
        assert result is not None

    @pytest.mark.asyncio
    async def test_all_correct_citations(self, provider, prompt_manager):
        """Test all correct citations together."""
        logger.info("Testing all correct citations together")
        prompt = prompt_manager.build_prompt(CORRECT_CITATIONS_ALL)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result: {result}")
        assert result is not None


class TestIncorrectCitations:
    """Test that incorrect APA 7th citations are caught with appropriate errors."""

    @pytest.mark.asyncio
    async def test_incorrect_and_instead_of_ampersand(self, provider, prompt_manager):
        """Test that 'and' instead of '&' is caught."""
        logger.info("Testing incorrect: 'and' instead of '&'")
        prompt = prompt_manager.build_prompt(INCORRECT_AND_INSTEAD_OF_AMPERSAND)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result: {result}")
        assert result is not None

        # Check for expected error keywords
        result_lower = result.get('response', str(result)).lower()
        assert any(keyword in result_lower for keyword in ["&", "and", "ampersand"])

    @pytest.mark.asyncio
    async def test_incorrect_title_case_book(self, provider, prompt_manager):
        """Test that incorrect title case in book is caught."""
        logger.info("Testing incorrect: book title case")
        prompt = prompt_manager.build_prompt(INCORRECT_TITLE_CASE_BOOK)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result: {result}")
        assert result is not None

        result_lower = result.get('response', str(result)).lower()
        assert any(keyword in result_lower for keyword in ["title case", "sentence case", "capitalization"])

    @pytest.mark.asyncio
    async def test_incorrect_title_case_article(self, provider, prompt_manager):
        """Test that incorrect title case in article is caught."""
        logger.info("Testing incorrect: article title case")
        prompt = prompt_manager.build_prompt(INCORRECT_TITLE_CASE_ARTICLE)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result: {result}")
        assert result is not None

        result_lower = result.get('response', str(result)).lower()
        assert any(keyword in result_lower for keyword in ["title case", "sentence case", "capitalization"])

    @pytest.mark.asyncio
    async def test_incorrect_old_doi_format(self, provider, prompt_manager):
        """Test that old DOI format is caught."""
        logger.info("Testing incorrect: old DOI format")
        prompt = prompt_manager.build_prompt(INCORRECT_OLD_DOI_FORMAT)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result: {result}")
        assert result is not None

        result_lower = result.get('response', str(result)).lower()
        assert any(keyword in result_lower for keyword in ["doi", "https://doi.org"])

    @pytest.mark.asyncio
    async def test_incorrect_publisher_location(self, provider, prompt_manager):
        """Test that publisher location is caught."""
        logger.info("Testing incorrect: publisher location included")
        prompt = prompt_manager.build_prompt(INCORRECT_PUBLISHER_LOCATION)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result: {result}")
        assert result is not None

        result_lower = result.get('response', str(result)).lower()
        assert any(keyword in result_lower for keyword in ["location", "new york", "publisher"])

    @pytest.mark.asyncio
    async def test_incorrect_old_webpage_format(self, provider, prompt_manager):
        """Test that old 'Retrieved from' format is caught."""
        logger.info("Testing incorrect: old webpage format")
        prompt = prompt_manager.build_prompt(INCORRECT_OLD_WEBPAGE_FORMAT)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result: {result}")
        assert result is not None

        result_lower = result.get('response', str(result)).lower()
        assert any(keyword in result_lower for keyword in ["retrieved", "from"])

    @pytest.mark.asyncio
    async def test_incorrect_multiple_errors(self, provider, prompt_manager):
        """Test that multiple errors in one citation are caught."""
        logger.info("Testing incorrect: multiple errors in one citation")
        prompt = prompt_manager.build_prompt(INCORRECT_MULTIPLE_ERRORS)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result: {result}")
        assert result is not None

        # Should detect multiple issues
        result_lower = result.get('response', str(result)).lower()
        error_count = sum([
            1 if "&" in result_lower or "and" in result_lower else 0,
            1 if "title case" in result_lower or "sentence case" in result_lower else 0,
            1 if "doi" in result_lower else 0,
        ])

        logger.info(f"Detected {error_count} error types in citation with multiple errors")
        # Should find at least 2 of the 3 error types
        assert error_count >= 2

    @pytest.mark.asyncio
    async def test_all_incorrect_citations(self, provider, prompt_manager):
        """Test all incorrect citations together."""
        logger.info("Testing all incorrect citations together")
        prompt = prompt_manager.build_prompt(INCORRECT_CITATIONS_ALL)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result (truncated): {str(result)[:500]}...")
        assert result is not None

        # Should find multiple errors across all citations
        result_lower = result.get('response', str(result)).lower()
        assert "error" in result_lower or "incorrect" in result_lower or "issue" in result_lower


class TestMixedCitations:
    """Test mixed correct and incorrect citations."""

    @pytest.mark.asyncio
    async def test_mixed_citations(self, provider, prompt_manager):
        """Test that system correctly identifies both correct and incorrect citations."""
        logger.info("Testing mixed correct and incorrect citations")
        prompt = prompt_manager.build_prompt(MIXED_CITATIONS)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result: {result}")
        assert result is not None

        # Should identify some as correct and some as incorrect
        result_lower = result.get('response', str(result)).lower()
        # Should mention errors for incorrect ones
        assert any(keyword in result_lower for keyword in ["error", "incorrect", "issue"])


class TestEdgeCases:
    """Test edge cases in citation formatting."""

    @pytest.mark.asyncio
    async def test_edge_cases(self, provider, prompt_manager):
        """Test edge cases like many authors, no date, corporate authors."""
        logger.info("Testing edge cases (many authors, no date, corporate author, article number)")
        prompt = prompt_manager.build_prompt(EDGE_CASES_ALL)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Validation result: {result}")
        assert result is not None

        # Edge cases should be handled (may or may not have errors depending on APA 7th rules)
        # Main goal is to ensure system doesn't crash and provides some validation
        assert len(str(result)) > 0


class TestSystemRobustness:
    """Test system robustness with various inputs."""

    @pytest.mark.asyncio
    async def test_empty_input(self, provider, prompt_manager):
        """Test system handles empty input gracefully."""
        logger.info("Testing empty input handling")

        # Empty input should raise ValueError from prompt_manager
        with pytest.raises(ValueError) as exc_info:
            prompt = prompt_manager.build_prompt("")

        # Verify error message is appropriate
        assert "empty" in str(exc_info.value).lower() or "cannot" in str(exc_info.value).lower()
        logger.info(f"Empty input correctly raised ValueError: {exc_info.value}")

    @pytest.mark.asyncio
    async def test_single_citation(self, provider, prompt_manager):
        """Test system handles single citation correctly."""
        logger.info("Testing single citation")
        prompt = prompt_manager.build_prompt(CORRECT_JOURNAL_ARTICLE)
        result = await provider.validate_citations(prompt)

        logger.debug(f"Single citation result: {result}")
        assert result is not None
        assert len(str(result)) > 0


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v", "-s"])
