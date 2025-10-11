"""
Integration tests for LLM-based citation validation.
These tests hit the real OpenAI API.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_validate_citation_with_errors():
    """
    Test that the endpoint calls LLM and returns structured errors for a bad citation.
    This citation has multiple APA 7 errors:
    - Uses "and" instead of "&"
    - Title case in article title (should be sentence case)
    - Old DOI format
    """
    bad_citation = """Smith, J. and Jones, M. (2020). The Impact of Climate Change on Polar Bears. Journal of Arctic Studies, 15(2), 45-67. doi:10.1234/jas.2020.001"""

    response = client.post(
        "/api/validate",
        json={
            "citations": bad_citation,
            "style": "apa7"
        }
    )

    assert response.status_code == 200
    data = response.json()

    # Should have results key with list of validation results
    assert "results" in data
    assert isinstance(data["results"], list)
    assert len(data["results"]) == 1

    # Check structure of first result
    result = data["results"][0]
    assert "citation_number" in result
    assert "original" in result
    assert "source_type" in result
    assert "errors" in result

    # Should detect errors
    assert isinstance(result["errors"], list)
    assert len(result["errors"]) > 0

    # Each error should have structured info
    for error in result["errors"]:
        assert "component" in error
        assert "problem" in error
        assert "correction" in error


def test_validate_correct_citation():
    """
    Test that a correctly formatted APA 7 citation passes validation.
    """
    good_citation = """Smith, J., & Jones, M. (2020). The impact of climate change on polar bears. Journal of Arctic Studies, 15(2), 45-67. https://doi.org/10.1234/jas.2020.001"""

    response = client.post(
        "/api/validate",
        json={
            "citations": good_citation,
            "style": "apa7"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    assert len(data["results"]) == 1

    result = data["results"][0]
    assert result["errors"] == [] or result["errors"][0]["component"] == "No errors"


def test_validate_multiple_citations():
    """
    Test validation of multiple citations at once (separated by blank lines).
    """
    # Note: Using very distinct citations to ensure LLM treats them separately
    citations = """Smith, J., & Jones, M. (2020). Climate study results. Nature, 15(2), 45-67. https://doi.org/10.1234/nature.2020.001

Brown, A., & Davis, B. (2019). Research methods in psychology (2nd ed.). Academic Press."""

    response = client.post(
        "/api/validate",
        json={
            "citations": citations,
            "style": "apa7"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "results" in data
    # LLM should recognize these as 2 distinct citations
    assert len(data["results"]) >= 1  # At minimum should process them

    # All results should have proper structure
    for result in data["results"]:
        assert "citation_number" in result
        assert "original" in result
        assert "source_type" in result
        assert "errors" in result
