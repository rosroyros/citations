#!/usr/bin/env python3
"""
Tests for citations field removal from ValidationResponse API
Verifies that citations field has been completely removed after citations_text column removal
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
    """Test ValidationResponse model after citations field removal"""

    def test_validation_response_no_citations_field(self):
        """Test that ValidationResponse no longer has citations field after cleanup"""
        validation_data = {
            "job_id": "test-after-removal",
            "created_at": "2025-01-28T10:00:00Z",
            "completed_at": "2025-01-28T10:05:00Z",
            "duration_seconds": 300.0,
            "citation_count": 2,
            "token_usage_prompt": 100,
            "token_usage_completion": 50,
            "token_usage_total": 150,
            "user_type": "free",
            "status": "completed",
            "error_message": None
        }

        response = ValidationResponse(**validation_data)

        # Should not have citations field
        with pytest.raises(AttributeError):
            _ = response.citations

        # Other fields should still work
        assert response.citation_count == 2, "citation_count should still work"
        assert response.job_id == "test-after-removal", "job_id should still work"

    def test_validation_response_model_schema_excludes_citations(self):
        """Test that ValidationResponse model schema excludes citations field"""
        schema = ValidationResponse.model_json_schema()
        properties = schema.get("properties", {})

        # citations field should not be in schema
        assert "citations" not in properties, "citations field should not be in model schema after removal"
        assert "citations_text" not in properties, "citations_text should not be in schema (column removed)"

    def test_validation_response_serializes_without_citations(self):
        """Test that ValidationResponse properly serializes to JSON without citations field"""
        validation_data = {
            "job_id": "test-serialization",
            "created_at": "2025-01-28T13:00:00Z",
            "user_type": "free",
            "status": "completed"
        }

        response = ValidationResponse(**validation_data)
        json_data = response.model_dump()

        # citations should not be in serialized JSON
        assert "citations" not in json_data, "citations should not be in serialized JSON after removal"
        assert "citations_text" not in json_data, "citations_text should not be in JSON (column removed)"


class TestCitationsFieldSecurity:
    """Test security aspects after citations field removal"""

    def test_no_citations_field_security_issue(self):
        """Test that removing citations field eliminates security surface"""
        # Ensure citations field cannot be set even if provided in data
        validation_data = {
            "job_id": "security-test-001",
            "created_at": "2025-01-28T20:00:00Z",
            "user_type": "free",
            "status": "completed",
            # Attempting to include citations field - should be ignored
            "citations": "1. <script>alert('xss')</script> (2023). Malicious Journal.\n\n2. '; DROP TABLE validations; -- (2024). SQL Injection Test."
        }

        response = ValidationResponse(**validation_data)

        # Should not have citations field even if provided in data
        with pytest.raises(AttributeError):
            _ = response.citations

        # Other fields should work normally
        assert response.job_id == "security-test-001", "Other fields should work normally"


class TestCitationsFieldDatabaseIntegration:
    """Test database integration after citations field removal"""

    def test_database_integration_after_citations_text_removal(self):
        """Test that database operations work correctly after citations_text and citations field removal"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            try:
                with DatabaseManager(tmp.name) as db:
                    # Insert test data without citations_text
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
                        "error_message": None
                    }

                    db.insert_validation(test_validation)

                    # Test retrieving validation
                    retrieved = db.get_validation("test-db-integration")
                    assert retrieved is not None, "Validation should be retrievable"
                    assert "citations_text" not in retrieved, "citations_text should not be present after removal"

                    # Test API response generation works without citations field
                    response = ValidationResponse(**retrieved)

                    # Should not have citations field
                    with pytest.raises(AttributeError):
                        _ = response.citations

                    # Other fields should work
                    assert response.job_id == "test-db-integration", "Other API fields should work"

            finally:
                os.unlink(tmp.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])