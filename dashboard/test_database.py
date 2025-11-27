#!/usr/bin/env python3
"""
Tests for database.py module
Following TDD: write failing tests first, then implement
"""
import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

# Import the module we're testing
import sys
sys.path.append(str(Path(__file__).parent))

from database import DatabaseManager


class TestDatabaseSchema:
    """Test database schema creation and basic functionality"""

    def test_creates_validations_table_with_correct_schema(self):
        """Test that validations table is created with all required columns"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = DatabaseManager(db_path)

            # Verify table exists and has correct schema
            schema = db.get_table_schema("validations")

            expected_columns = [
                "job_id TEXT PRIMARY KEY",
                "created_at TEXT NOT NULL",
                "completed_at TEXT",
                "duration_seconds REAL",
                "citation_count INTEGER",
                "token_usage_prompt INTEGER",
                "token_usage_completion INTEGER",
                "token_usage_total INTEGER",
                "user_type TEXT NOT NULL",
                "status TEXT NOT NULL",
                "error_message TEXT"
            ]

            for column_def in expected_columns:
                assert column_def in schema, f"Missing column: {column_def}"

    def test_creates_parser_metadata_table(self):
        """Test that parser_metadata table is created"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = DatabaseManager(db_path)

            # Verify table exists
            schema = db.get_table_schema("parser_metadata")

            expected_columns = [
                "key TEXT PRIMARY KEY",
                "value TEXT"
            ]

            for column_def in expected_columns:
                assert column_def in schema, f"Missing column: {column_def}"

    def test_creates_parser_errors_table(self):
        """Test that parser_errors table is created"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = DatabaseManager(db_path)

            # Verify table exists
            schema = db.get_table_schema("parser_errors")

            expected_columns = [
                "id INTEGER PRIMARY KEY AUTOINCREMENT",
                "timestamp TEXT NOT NULL",
                "error_message TEXT NOT NULL",
                "log_line TEXT"
            ]

            for column_def in expected_columns:
                assert column_def in schema, f"Missing column: {column_def}"

    def test_creates_required_indexes(self):
        """Test that required indexes are created for query performance"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = DatabaseManager(db_path)

            # Check indexes exist
            indexes = db.get_indexes()

            expected_indexes = [
                "idx_created_at",
                "idx_status",
                "idx_user_type"
            ]

            for index_name in expected_indexes:
                assert index_name in indexes, f"Missing index: {index_name}"


class TestDatabaseCRUD:
    """Test CRUD operations for validations table"""

    def test_insert_validation_record(self):
        """Test inserting a single validation record"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = DatabaseManager(db_path)

            # Test data
            validation_data = {
                "job_id": "test-job-123",
                "created_at": "2025-11-27T10:00:00Z",
                "completed_at": "2025-11-27T10:01:00Z",
                "duration_seconds": 60.0,
                "citation_count": 5,
                "token_usage_prompt": 1000,
                "token_usage_completion": 2000,
                "token_usage_total": 3000,
                "user_type": "free",
                "status": "completed",
                "error_message": None
            }

            # Insert record
            db.insert_validation(validation_data)

            # Verify record was inserted
            result = db.get_validation("test-job-123")

            assert result is not None
            assert result["job_id"] == "test-job-123"
            assert result["created_at"] == "2025-11-27T10:00:00Z"
            assert result["completed_at"] == "2025-11-27T10:01:00Z"
            assert result["duration_seconds"] == 60.0
            assert result["citation_count"] == 5
            assert result["token_usage_prompt"] == 1000
            assert result["token_usage_completion"] == 2000
            assert result["token_usage_total"] == 3000
            assert result["user_type"] == "free"
            assert result["status"] == "completed"
            assert result["error_message"] is None

    def test_upsert_validation_updates_existing_record(self):
        """Test that upsert updates existing validation record"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = DatabaseManager(db_path)

            # Insert initial record
            initial_data = {
                "job_id": "test-job-123",
                "created_at": "2025-11-27T10:00:00Z",
                "completed_at": None,
                "duration_seconds": None,
                "citation_count": None,
                "token_usage_prompt": None,
                "token_usage_completion": None,
                "token_usage_total": None,
                "user_type": "free",
                "status": "pending",
                "error_message": None
            }
            db.insert_validation(initial_data)

            # Update record with completion data
            updated_data = {
                "job_id": "test-job-123",
                "created_at": "2025-11-27T10:00:00Z",
                "completed_at": "2025-11-27T10:01:30Z",
                "duration_seconds": 90.0,
                "citation_count": 3,
                "token_usage_prompt": 800,
                "token_usage_completion": 1500,
                "token_usage_total": 2300,
                "user_type": "free",
                "status": "completed",
                "error_message": None
            }
            db.insert_validation(updated_data)  # This should be an upsert

            # Verify record was updated
            result = db.get_validation("test-job-123")

            assert result["completed_at"] == "2025-11-27T10:01:30Z"
            assert result["duration_seconds"] == 90.0
            assert result["citation_count"] == 3
            assert result["status"] == "completed"

    def test_get_validations_with_filters(self):
        """Test retrieving validations with various filters"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = DatabaseManager(db_path)

            # Insert test data
            base_time = datetime.now()

            test_validations = [
                {
                    "job_id": f"test-job-{i}",
                    "created_at": (base_time + timedelta(hours=i)).isoformat() + "Z",
                    "completed_at": (base_time + timedelta(hours=i, minutes=1)).isoformat() + "Z",
                    "duration_seconds": 60 + i * 10,
                    "citation_count": i + 1,
                    "token_usage_prompt": 1000 + i * 100,
                    "token_usage_completion": 2000 + i * 200,
                    "token_usage_total": 3000 + i * 300,
                    "user_type": "free" if i % 2 == 0 else "paid",
                    "status": "completed" if i < 8 else "failed",
                    "error_message": None if i < 8 else "Timeout error"
                }
                for i in range(10)
            ]

            for validation in test_validations:
                db.insert_validation(validation)

            # Test filtering by status
            completed = db.get_validations(status="completed", limit=100)
            assert len(completed) == 8
            assert all(v["status"] == "completed" for v in completed)

            # Test filtering by user_type
            free_validations = db.get_validations(user_type="free", limit=100)
            assert len(free_validations) == 5
            assert all(v["user_type"] == "free" for v in free_validations)

            # Test pagination
            page1 = db.get_validations(limit=3, offset=0)
            page2 = db.get_validations(limit=3, offset=3)

            assert len(page1) == 3
            assert len(page2) == 3
            assert page1[0]["job_id"] != page2[0]["job_id"]

            # Test search by job_id
            search_result = db.get_validations(search="test-job-5", limit=100)
            assert len(search_result) == 1
            assert search_result[0]["job_id"] == "test-job-5"


class TestDatabaseMetadata:
    """Test parser metadata operations"""

    def test_set_and_get_metadata(self):
        """Test setting and getting metadata values"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = DatabaseManager(db_path)

            # Set metadata
            db.set_metadata("last_parsed_timestamp", "2025-11-27T10:00:00Z")
            db.set_metadata("last_parsed_line_number", "12345")

            # Get metadata
            timestamp = db.get_metadata("last_parsed_timestamp")
            line_number = db.get_metadata("last_parsed_line_number")

            assert timestamp == "2025-11-27T10:00:00Z"
            assert line_number == "12345"

            # Test non-existent key
            non_existent = db.get_metadata("non_existent_key")
            assert non_existent is None


class TestDatabaseStats:
    """Test statistics aggregation queries"""

    def test_get_stats_summary(self):
        """Test getting summary statistics"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = DatabaseManager(db_path)

            # Insert test data
            base_time = datetime.now()

            test_validations = [
                {
                    "job_id": f"test-job-{i}",
                    "created_at": (base_time + timedelta(hours=i)).isoformat() + "Z",
                    "completed_at": (base_time + timedelta(hours=i, minutes=1)).isoformat() + "Z",
                    "duration_seconds": 60 + i * 10,
                    "citation_count": i + 1,
                    "token_usage_prompt": 1000 + i * 100,
                    "token_usage_completion": 2000 + i * 200,
                    "token_usage_total": 3000 + i * 300,
                    "user_type": "free" if i % 2 == 0 else "paid",
                    "status": "completed" if i < 8 else "failed",
                    "error_message": None if i < 8 else "Timeout error"
                }
                for i in range(10)
            ]

            for validation in test_validations:
                db.insert_validation(validation)

            # Get stats
            stats = db.get_stats()

            assert stats["total_validations"] == 10
            assert stats["completed"] == 8
            assert stats["failed"] == 2
            assert stats["total_citations"] == sum(i + 1 for i in range(10))  # 1+2+...+10 = 55
            assert stats["free_users"] == 5
            assert stats["paid_users"] == 5
            assert stats["avg_duration_seconds"] > 0
            assert stats["avg_citations_per_validation"] > 0


class TestDatabaseRetention:
    """Test data retention policy"""

    def test_delete_old_records(self):
        """Test deletion of old records based on retention policy"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = os.path.join(temp_dir, "test.db")
            db = DatabaseManager(db_path)

            # Insert test data with different ages
            base_time = datetime.now()

            # Old record (100 days ago)
            old_validation = {
                "job_id": "old-job",
                "created_at": (base_time - timedelta(days=100)).isoformat() + "Z",
                "completed_at": (base_time - timedelta(days=100, minutes=1)).isoformat() + "Z",
                "duration_seconds": 60.0,
                "citation_count": 5,
                "token_usage_prompt": 1000,
                "token_usage_completion": 2000,
                "token_usage_total": 3000,
                "user_type": "free",
                "status": "completed",
                "error_message": None
            }

            # Recent record (10 days ago)
            recent_validation = {
                "job_id": "recent-job",
                "created_at": (base_time - timedelta(days=10)).isoformat() + "Z",
                "completed_at": (base_time - timedelta(days=10, minutes=1)).isoformat() + "Z",
                "duration_seconds": 60.0,
                "citation_count": 5,
                "token_usage_prompt": 1000,
                "token_usage_completion": 2000,
                "token_usage_total": 3000,
                "user_type": "free",
                "status": "completed",
                "error_message": None
            }

            db.insert_validation(old_validation)
            db.insert_validation(recent_validation)

            # Delete records older than 90 days
            deleted_count = db.delete_old_records(days=90)

            assert deleted_count == 1

            # Verify only recent record remains
            remaining = db.get_validations(limit=100)
            assert len(remaining) == 1
            assert remaining[0]["job_id"] == "recent-job"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])