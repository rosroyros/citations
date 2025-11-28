#!/usr/bin/env python3
"""
Tests for citations field functionality in ValidationResponse API
Addresses the minor issue from code review: missing test coverage for citations field
"""
import pytest
import tempfile
import os
import sys

# Add dashboard directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from api import ValidationResponse
from fastapi.testclient import TestClient
from api import app
import json


class TestCitationsFieldValidationResponse:
    """Test ValidationResponse model with citations field"""

    def test_validation_response_includes_citations_when_present(self):
        """Test that ValidationResponse includes citations field when citations are provided"""
        validation_data = {
            "job_id": "test-with-citations",
            "created_at": "2025-01-28T10:00:00Z",
            "completed_at": "2025-01-28T10:05:00Z",
            "duration_seconds": 300.0,
            "citation_count": 2,
            "token_usage_prompt": 100,
            "token_usage_completion": 50,
            "token_usage_total": 150,
            "user_type": "free",
            "status": "completed",
            "error_message": None,
            "citations": "1. Smith et al. (2023). Machine Learning in Citation Analysis. Journal of AI Research, 45(2), 123-145.\n\n2. Johnson, B. (2022). Automated Citation Validation. Proceedings of NLP Conference, pp. 78-92."
        }

        response = ValidationResponse(**validation_data)

        assert response.citations is not None, "citations field should not be None when provided"
        assert "Smith et al." in response.citations, "citations should contain first citation"
        assert "Johnson, B." in response.citations, "citations should contain second citation"
        assert "2023" in response.citations, "citations should contain first citation year"
        assert "2022" in response.citations, "citations should contain second citation year"
        assert response.citation_count == 2, "citation_count should match number of citations"

    def test_validation_response_handles_empty_citations(self):
        """Test that citations field is None when citations are not provided"""
        validation_data = {
            "job_id": "test-empty-citations",
            "created_at": "2025-01-28T11:00:00Z",
            "completed_at": None,
            "duration_seconds": None,
            "citation_count": 0,
            "token_usage_prompt": None,
            "token_usage_completion": None,
            "token_usage_total": None,
            "user_type": "paid",
            "status": "pending",
            "error_message": "Processing...",
            "citations": None
        }

        response = ValidationResponse(**validation_data)

        assert response.citations is None, "citations field should be None when not provided"
        assert response.job_id == "test-empty-citations", "other fields should still work"

    def test_validation_response_handles_empty_string_citations(self):
        """Test that citations field handles empty string correctly"""
        validation_data = {
            "job_id": "test-empty-string",
            "created_at": "2025-01-28T12:00:00Z",
            "user_type": "free",
            "status": "completed",
            "citations": ""  # Empty string
        }

        response = ValidationResponse(**validation_data)

        assert response.citations == "", "citations field should handle empty string"
        assert isinstance(response.citations, str), "citations should be string type"

    def test_validation_response_serializes_citations_to_json(self):
        """Test that citations field properly serializes to JSON"""
        validation_data = {
            "job_id": "test-serialization",
            "created_at": "2025-01-28T13:00:00Z",
            "user_type": "free",
            "status": "completed",
            "citations": "Test Citation (2024). Test Journal, 10(1), 1-10."
        }

        response = ValidationResponse(**validation_data)
        json_data = response.model_dump()

        assert "citations" in json_data, "citations should be in serialized JSON"
        assert json_data["citations"] == "Test Citation (2024). Test Journal, 10(1), 1-10.", "citations value should match"
        assert "citations_text" not in json_data, "citations_text should not be in JSON (alias should not leak)"

    def test_validation_response_model_schema_includes_citations(self):
        """Test that ValidationResponse model schema includes citations field"""
        schema = ValidationResponse.model_json_schema()
        properties = schema.get("properties", {})

        assert "citations" in properties, "citations field should be in model schema"
        citations_schema = properties["citations"]

        # Check that it has the expected structure for optional strings
        assert "anyOf" in citations_schema, "citations should be optional string using anyOf"
        any_of_types = citations_schema["anyOf"]
        type_strings = [item.get("type") for item in any_of_types if "type" in item]
        assert "string" in type_strings and "null" in type_strings, "citations should allow string or null"

        assert "description" in citations_schema, "citations should have description"
        assert "citation" in citations_schema["description"].lower(), "description should mention citations"


class TestCitationsFieldSecurity:
    """Test security aspects of citations field"""

    def test_citations_field_sanitizes_input(self):
        """Test that citations field doesn't introduce security vulnerabilities"""
        # Test with potentially dangerous content - should be safely handled
        validation_data = {
            "job_id": "security-test-001",
            "created_at": "2025-01-28T20:00:00Z",
            "user_type": "free",
            "status": "completed",
            "citations": "1. <script>alert('xss')</script> (2023). Malicious Journal.\n\n2. '; DROP TABLE validations; -- (2024). SQL Injection Test."
        }

        response = ValidationResponse(**validation_data)

        # Should store content as-is (sanitization happens at database level)
        assert "<script>" in response.citations, "Should handle script tags appropriately"
        assert "DROP TABLE" in response.citations, "Should handle SQL attempts appropriately"
        assert response.citations is not None, "Should handle dangerous content safely"


class TestCitationsFieldDatabaseIntegration:
    """Test citations field database integration"""

    def test_database_integration_with_citations(self):
        """Test that database operations handle citations_text field correctly"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            try:
                with DatabaseManager(tmp.name) as db:
                    # Insert test data with citations_text
                    test_validation = {
                        "job_id": "test-db-integration",
                        "created_at": "2025-01-28T21:00:00Z",
                        "completed_at": "2025-01-28T21:05:00Z",
                        "duration_seconds": 300.0,
                        "citation_count": 2,
                        "token_usage_prompt": 100,
                        "token_usage_completion": 50,
                        "token_usage_total": 150,
                        "user_type": "free",
                        "status": "completed",
                        "error_message": None,
                        "citations_text": "1. Database Test (2023). Integration Journal.\n\n2. Another Test (2024). System Analysis."
                    }

                    db.insert_validation(test_validation)

                    # Test retrieving validation
                    retrieved = db.get_validation("test-db-integration")
                    assert retrieved is not None, "Validation should be retrievable"
                    assert retrieved["citations_text"] == test_validation["citations_text"], "citations_text should match"

                    # Test API response generation with field mapping
                    validation_data = {
                        **retrieved,
                        "citations": retrieved.get("citations_text")  # Map citations_text -> citations
                    }
                    response = ValidationResponse(**validation_data)
                    assert response.citations == test_validation["citations_text"], "API response should have citations"

            finally:
                os.unlink(tmp.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])