# Code Review Request - Free Tier Enforcement Tests

## What Was Implemented
Created comprehensive test suite for free tier enforcement using TDD methodology. Successfully implemented 6 failing tests that cover the X-Free-Used header logic for limiting free tier users to 10 citations total.

## Plan Or Requirements
**Original Task (citations-4pb):** Write failing backend tests for free tier limit enforcement (TDD)
- File: backend/tests/test_free_tier.py
- 6 specific test cases required (listed below)
- Expected: All tests FAIL - implementation doesn't exist yet

**Review Criteria:**
1. **Task Adherence**: Did we implement exactly the 6 test cases specified?
2. **TDD Discipline**: Are tests properly written to FAIL first (red phase)?
3. **Test Quality**: Clear names, specific assertions, isolated test cases?
4. **Code Quality**: Proper imports, mocking, FastAPI testing patterns?
5. **Edge Case Coverage**: Are the 6 specified scenarios comprehensive?
6. **Implementation Readiness**: Ready to drive implementation phase?

## Implementation Details
**Test Cases Implemented (as per task specification):**
1. ✅ Free user under limit (5 citations requested, 0 used)
2. ✅ Free user at limit (2 citations requested, 8 used)
3. ✅ Free user over limit (8 citations requested, 5 used)
4. ✅ Free user already at limit (5 citations requested, 10 used)
5. ✅ Missing X-Free-Used header
6. ✅ Invalid X-Free-Used header

**TDD Verification:**
- ✅ All 6 tests FAIL as expected (red phase confirmed)
- ✅ Tests fail because feature doesn't exist (not syntax errors)
- ✅ Ready for implementation in dependent issue citations-qmf

## Context
- Free tier limit: 10 citations total
- Header: X-Free-Used (number of citations already used)
- Implementation target: /api/validate endpoint
- Current status: tests ready, feature not implemented

## Assessment Required
Please evaluate:
- Are these tests ready to drive the implementation?
- Any critical gaps or issues before proceeding?
- Quality of test design and coverage?
- Adherence to TDD best practices?

Please provide feedback on: Critical/Important/Minor issues and overall readiness assessment.

## Test File: `backend/tests/test_free_tier.py`

```python
"""Tests for free tier enforcement using X-Free-Used header."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app

client = TestClient(app)


class TestFreeTierEnforcement:
    """Test free tier enforcement logic using X-Free-Used header."""

    @patch('backend.app.llm_provider.validate_citations')
    def test_free_user_under_limit_5_requested_0_used(self, mock_llm):
        """Test free user under limit (5 citations requested, 0 used) should succeed."""
        # Setup
        mock_llm.return_value = {
            "results": [
                {
                    "citation_number": 1,
                    "original": "Smith, 2023",
                    "source_type": "journal",
                    "errors": []
                },
                {
                    "citation_number": 2,
                    "original": "Jones, 2022",
                    "source_type": "book",
                    "errors": []
                },
                {
                    "citation_number": 3,
                    "original": "Brown, 2021",
                    "source_type": "article",
                    "errors": []
                },
                {
                    "citation_number": 4,
                    "original": "Davis, 2020",
                    "source_type": "website",
                    "errors": []
                },
                {
                    "citation_number": 5,
                    "original": "Wilson, 2019",
                    "source_type": "report",
                    "errors": []
                }
            ]
        }

        # Request with X-Free-Used header showing 0 citations used
        response = client.post(
            "/api/validate",
            json={"citations": "Smith, 2023\nJones, 2022\nBrown, 2021\nDavis, 2020\nWilson, 2019", "style": "apa7"},
            headers={"X-Free-Used": "0"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 5
        assert data["partial"] is False
        assert data["free_used"] == 5  # Should be updated to 5

    @patch('backend.app.llm_provider.validate_citations')
    def test_free_user_at_limit_2_requested_8_used(self, mock_llm):
        """Test free user at limit (2 citations requested, 8 used) should succeed."""
        # Setup
        mock_llm.return_value = {
            "results": [
                {
                    "citation_number": 1,
                    "original": "Smith, 2023",
                    "source_type": "journal",
                    "errors": []
                },
                {
                    "citation_number": 2,
                    "original": "Jones, 2022",
                    "source_type": "book",
                    "errors": []
                }
            ]
        }

        # Request with X-Free-Used header showing 8 citations used (8+2=10, at limit)
        response = client.post(
            "/api/validate",
            json={"citations": "Smith, 2023\nJones, 2022", "style": "apa7"},
            headers={"X-Free-Used": "8"}
        )

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 2
        assert data["partial"] is False
        assert data["free_used"] == 10  # Should be updated to 10 (at limit)

    @patch('backend.app.llm_provider.validate_citations')
    def test_free_user_over_limit_8_requested_5_used(self, mock_llm):
        """Test free user over limit (8 citations requested, 5 used) should be limited."""
        # Setup - return 8 potential results
        mock_llm.return_value = {
            "results": [
                {"citation_number": i+1, "original": f"Source {i+1}", "source_type": "journal", "errors": []}
                for i in range(8)
            ]
        }

        # Request with X-Free-Used header showing 5 citations used (5+8=13, over limit of 10)
        response = client.post(
            "/api/validate",
            json={"citations": "8 citations here", "style": "apa7"},
            headers={"X-Free-Used": "5"}
        )

        # Assertions - should only process 5 more citations (5 used + 5 new = 10 total)
        assert response.status_code == 200
        data = response.json()
        assert data["partial"] is True
        assert data["citations_checked"] == 5  # Only processed 5 out of 8
        assert data["citations_remaining"] == 3  # 3 left unprocessed
        assert len(data["results"]) == 5  # Only first 5 results
        assert data["free_used"] == 10  # At limit

    @patch('backend.app.llm_provider.validate_citations')
    def test_free_user_already_at_limit_5_requested_10_used(self, mock_llm):
        """Test free user already at limit (5 citations requested, 10 used) should reject."""
        # Request with X-Free-Used header showing 10 citations used (already at limit)
        response = client.post(
            "/api/validate",
            json={"citations": "5 citations here", "style": "apa7"},
            headers={"X-Free-Used": "10"}
        )

        # Assertions - should reject with 402 Payment Required
        assert response.status_code == 402
        error_data = response.json()
        assert "Free tier limit" in error_data["detail"]
        assert "10 citations" in error_data["detail"]

    @patch('backend.app.llm_provider.validate_citations')
    def test_missing_free_used_header_treated_as_0(self, mock_llm):
        """Test missing X-Free-Used header should be treated as 0 used."""
        # Setup
        mock_llm.return_value = {
            "results": [
                {
                    "citation_number": 1,
                    "original": "Smith, 2023",
                    "source_type": "journal",
                    "errors": []
                }
            ]
        }

        # Request without X-Free-Used header
        response = client.post(
            "/api/validate",
            json={"citations": "Smith, 2023", "style": "apa7"}
        )

        # Assertions - should treat as 0 used and allow processing
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 1
        assert data["partial"] is False
        assert data["free_used"] == 1  # Should be updated to 1

    def test_invalid_free_used_header_returns_400(self):
        """Test invalid X-Free-Used header should return 400 Bad Request."""
        # Request with invalid X-Free-Used header (non-numeric)
        response = client.post(
            "/api/validate",
            json={"citations": "Smith, 2023", "style": "apa7"},
            headers={"X-Free-Used": "invalid"}
        )

        # Assertions - should reject with 400 Bad Request
        assert response.status_code == 400
        error_data = response.json()
        assert "Invalid" in error_data["detail"]
        assert "X-Free-Used" in error_data["detail"]
```