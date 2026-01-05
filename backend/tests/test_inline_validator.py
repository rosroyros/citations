"""
Unit tests for inline_validator.py module.

Tests cover:
- Main validation function with edge cases
- Batching logic
- Response parsing
- Result organization by reference
- Orphan extraction
- Error handling
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from inline_validator import (
    validate_inline_citations,
    _validate_batch,
    _parse_inline_response,
    _format_reference_list,
    _format_inline_citations,
    _organize_by_reference,
    _extract_orphans,
    BATCH_SIZE,
    MAX_CITATIONS
)


class TestValidateInlineCitations:
    """Tests for the main validate_inline_citations function."""

    @pytest.mark.asyncio
    async def test_empty_inline_citations(self):
        """Test with no inline citations."""
        result = await validate_inline_citations(
            inline_citations=[],
            reference_list=[],
            style="apa7",
            provider=None
        )

        assert result["total_found"] == 0
        assert result["total_validated"] == 0
        assert result["results_by_ref"] == {}
        assert result["orphans"] == []

    @pytest.mark.asyncio
    async def test_max_citations_limit_enforced(self):
        """Test that documents with >100 citations are rejected."""
        # Create 101 citations
        inline_citations = [
            {"id": f"c{i}", "text": f"(Smith, 2019)"}
            for i in range(1, 102)
        ]
        reference_list = [{"index": 0, "text": "Smith, J. (2019). Title."}]

        with pytest.raises(ValueError, match="Maximum allowed is 100"):
            await validate_inline_citations(
                inline_citations=inline_citations,
                reference_list=reference_list,
                style="apa7",
                provider=None
            )

    @pytest.mark.asyncio
    async def test_batching_single_batch(self):
        """Test that citations in single batch are processed."""
        inline_citations = [
            {"id": "c1", "text": "(Smith, 2019)"},
            {"id": "c2", "text": "(Jones, 2020)"},
        ]
        reference_list = [
            {"index": 0, "text": "Smith, J. (2019). Title."},
            {"index": 1, "text": "Jones, J. (2020). Article."}
        ]

        mock_provider = Mock()
        mock_provider._call_new_api = AsyncMock(return_value='{"results": []}')

        result = await validate_inline_citations(
            inline_citations=inline_citations,
            reference_list=reference_list,
            style="apa7",
            provider=mock_provider
        )

        assert result["total_found"] == 2
        assert result["total_validated"] == 0  # Empty results from mock

    @pytest.mark.asyncio
    async def test_batching_multiple_batches(self):
        """Test that citations are split into batches correctly."""
        # Create 15 citations - should be 2 batches (10 + 5)
        inline_citations = [
            {"id": f"c{i}", "text": f"(Author, 2020)"}
            for i in range(1, 16)
        ]
        reference_list = [{"index": 0, "text": "Author, A. (2020). Work."}]

        mock_provider = Mock()
        mock_provider._call_new_api = AsyncMock(return_value='{"results": []}')

        await validate_inline_citations(
            inline_citations=inline_citations,
            reference_list=reference_list,
            style="apa7",
            provider=mock_provider
        )

        # Should be called twice (2 batches)
        assert mock_provider._call_new_api.call_count == 2


class TestParseInlineResponse:
    """Tests for _parse_inline_response function."""

    def test_parse_json_in_code_block(self):
        """Test parsing JSON from markdown code block."""
        response = '''
```json
{
  "results": [
    {
      "id": "c1",
      "citation_text": "(Smith, 2019)",
      "match_status": "matched",
      "matched_ref_index": 0,
      "matched_ref_indices": null,
      "mismatch_reason": null,
      "format_errors": [],
      "suggested_correction": null
    }
  ]
}
```
'''
        batch = [{"id": "c1", "text": "(Smith, 2019)"}]

        results = _parse_inline_response(response, batch)

        assert len(results) == 1
        assert results[0]["id"] == "c1"
        assert results[0]["match_status"] == "matched"
        assert results[0]["matched_ref_index"] == 0

    def test_parse_raw_json(self):
        """Test parsing raw JSON without code block."""
        response = '{"results": [{"id": "c1", "match_status": "matched", "matched_ref_index": 0, "matched_ref_indices": null, "mismatch_reason": null, "format_errors": [], "suggested_correction": null, "citation_text": "(Smith, 2019)"}]}'
        batch = [{"id": "c1", "text": "(Smith, 2019)"}]

        results = _parse_inline_response(response, batch)

        assert len(results) == 1
        assert results[0]["id"] == "c1"
        assert results[0]["match_status"] == "matched"

    def test_parse_direct_array(self):
        """Test parsing when response is direct array."""
        response = '[{"id": "c1", "match_status": "matched", "matched_ref_index": 0, "matched_ref_indices": null, "mismatch_reason": null, "format_errors": [], "suggested_correction": null, "citation_text": "(Smith, 2019)"}]'
        batch = [{"id": "c1", "text": "(Smith, 2019)"}]

        results = _parse_inline_response(response, batch)

        assert len(results) == 1
        assert results[0]["id"] == "c1"

    def test_parse_sets_default_fields(self):
        """Test that missing fields get default values."""
        response = '{"results": [{"id": "c1"}]}'
        batch = [{"id": "c1", "text": "(Smith, 2019)"}]

        results = _parse_inline_response(response, batch)

        assert len(results) == 1
        assert results[0]["match_status"] == "not_found"
        assert results[0]["matched_ref_index"] is None
        assert results[0]["matched_ref_indices"] is None
        assert results[0]["mismatch_reason"] is None
        assert results[0]["format_errors"] == []
        assert results[0]["suggested_correction"] is None

    def test_parse_invalid_json_returns_fallback(self):
        """Test that invalid JSON returns placeholder results."""
        response = "This is not valid JSON at all"
        batch = [
            {"id": "c1", "text": "(Smith, 2019)"},
            {"id": "c2", "text": "(Jones, 2020)"}
        ]

        results = _parse_inline_response(response, batch)

        assert len(results) == 2
        # Both should be placeholder results
        assert results[0]["id"] == "c1"
        assert results[0]["match_status"] == "not_found"
        assert "Parse error" in results[0]["mismatch_reason"]


class TestOrganizeByReference:
    """Tests for _organize_by_reference function."""

    def test_organize_by_matched_index(self):
        """Test grouping by single matched reference index."""
        results = [
            {"id": "c1", "matched_ref_index": 0, "matched_ref_indices": None},
            {"id": "c2", "matched_ref_index": 1, "matched_ref_indices": None},
            {"id": "c3", "matched_ref_index": 0, "matched_ref_indices": None},
        ]
        reference_list = [
            {"index": 0, "text": "Ref 0"},
            {"index": 1, "text": "Ref 1"},
        ]

        organized = _organize_by_reference(results, reference_list)

        assert len(organized[0]) == 2  # c1 and c3
        assert len(organized[1]) == 1  # c2
        assert organized[0][0]["id"] == "c1"
        assert organized[0][1]["id"] == "c3"
        assert organized[1][0]["id"] == "c2"

    def test_organize_ambiguous_citations(self):
        """Test that ambiguous citations are added to all matched refs."""
        results = [
            {"id": "c1", "matched_ref_index": None, "matched_ref_indices": [0, 1]},
        ]
        reference_list = [
            {"index": 0, "text": "Smith, J. (2019). Book One."},
            {"index": 1, "text": "Smith, J. (2019). Book Two."},
        ]

        organized = _organize_by_reference(results, reference_list)

        # Should appear in both ref 0 and ref 1
        assert len(organized[0]) == 1
        assert len(organized[1]) == 1
        assert organized[0][0]["id"] == "c1"
        assert organized[1][0]["id"] == "c1"

    def test_organize_initializes_all_refs(self):
        """Test that all reference indices get initialized."""
        results = [
            {"id": "c1", "matched_ref_index": 1, "matched_ref_indices": None},
        ]
        reference_list = [
            {"index": 0, "text": "Ref 0"},
            {"index": 1, "text": "Ref 1"},
            {"index": 2, "text": "Ref 2"},
        ]

        organized = _organize_by_reference(results, reference_list)

        # All refs should be present, even if empty
        assert 0 in organized
        assert 1 in organized
        assert 2 in organized
        assert len(organized[0]) == 0  # Empty
        assert len(organized[1]) == 1  # Has c1
        assert len(organized[2]) == 0  # Empty


class TestExtractOrphans:
    """Tests for _extract_orphans function."""

    def test_extract_not_found_citations(self):
        """Test extracting citations with match_status=not_found."""
        results = [
            {"id": "c1", "match_status": "matched", "matched_ref_index": 0},
            {"id": "c2", "match_status": "not_found", "matched_ref_index": None},
            {"id": "c3", "match_status": "not_found", "matched_ref_index": None},
        ]

        orphans = _extract_orphans(results)

        assert len(orphans) == 2
        assert orphans[0]["id"] == "c2"
        assert orphans[1]["id"] == "c3"

    def test_extract_null_matched_index(self):
        """Test extracting citations with null matched_ref_index."""
        results = [
            {"id": "c1", "match_status": "matched", "matched_ref_index": 0},
            {"id": "c2", "match_status": "mismatch", "matched_ref_index": None},
        ]

        orphans = _extract_orphans(results)

        assert len(orphans) == 1
        assert orphans[0]["id"] == "c2"

    def test_ambiguous_not_orphan(self):
        """Test that ambiguous citations (with matched_ref_indices) are not orphans."""
        results = [
            {"id": "c1", "match_status": "ambiguous", "matched_ref_index": None, "matched_ref_indices": [0, 1]},
        ]

        orphans = _extract_orphans(results)

        assert len(orphans) == 0


class TestFormatHelpers:
    """Tests for formatting helper functions."""

    def test_format_reference_list(self):
        """Test formatting reference list."""
        reference_list = [
            {"index": 0, "text": "Smith, J. (2019). Title."},
            {"index": 1, "text": "Jones, A. (2020). Article."},
        ]

        formatted = _format_reference_list(reference_list)

        assert formatted == "0. Smith, J. (2019). Title.\n1. Jones, A. (2020). Article."

    def test_format_inline_citations(self):
        """Test formatting inline citations."""
        batch = [
            {"id": "c1", "text": "(Smith, 2019)"},
            {"id": "c2", "text": "(Jones, 2020)"},
        ]

        formatted = _format_inline_citations(batch)

        assert formatted == "c1: (Smith, 2019)\nc2: (Jones, 2020)"


class TestConstants:
    """Tests for module constants."""

    def test_batch_size(self):
        """Test BATCH_SIZE constant."""
        assert BATCH_SIZE == 10

    def test_max_citations(self):
        """Test MAX_CITATIONS constant."""
        assert MAX_CITATIONS == 100
