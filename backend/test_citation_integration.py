#!/usr/bin/env python3
"""
Test script for CitationLogParser integration with dashboard data flow.

This script tests:
1. Integration with existing jobs dictionary
2. Database connection and validation checking
3. Citation processing and job updates
4. Duplicate prevention
5. Dashboard data flow compatibility
"""

import os
import sys
import tempfile
import sqlite3
from pathlib import Path

# Add backend path to import modules
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from citation_logger import CitationLogParser, log_citations_to_dashboard
from database import get_validations_db_path, create_validation_record
from logger import setup_logger

# Setup test logger
logger = setup_logger("test_integration")

def create_test_validation_database(test_db_path: str) -> None:
    """Create a test validation database with sample data."""
    os.makedirs(os.path.dirname(test_db_path), exist_ok=True)

    with sqlite3.connect(test_db_path) as conn:
        cursor = conn.cursor()

        # Create validations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS validations (
                job_id TEXT PRIMARY KEY,
                user_type TEXT NOT NULL,
                citation_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert test validation records
        test_jobs = [
            ("test_job_1", "free", 3, "completed"),
            ("test_job_2", "paid", 5, "completed"),
            ("test_job_3", "free", 2, "processing"),
            ("nonexistent_job", "free", 1, "completed")  # This job won't exist in jobs dict
        ]

        for job_id, user_type, citation_count, status in test_jobs:
            create_validation_record(job_id, user_type, citation_count, status)

        conn.commit()
        logger.info(f"Created test validation database at {test_db_path}")

def create_test_citation_log(test_log_path: str) -> None:
    """Create a test citation log with sample data."""
    os.makedirs(os.path.dirname(test_log_path), exist_ok=True)

    # Sample citations in structured format
    log_content = """<<JOB_ID:test_job_1>>
Smith, J. (2023). Example citation one. Journal of Testing, 15(2), 123-145.
Doe, J. A. (2023). Another example citation. Book Publisher.
Brown, M. (2023). Third citation example. Conference Proceedings.
<<<END_JOB>>>
<<JOB_ID:test_job_2>>
Johnson, K. (2023). Paid user citation one. Medical Journal, 10(1), 45-67.
Williams, L. (2023). Paid user citation two. Academic Press.
Davis, R. (2023). Paid user citation three. Science Magazine, 25(3), 234-256.
Miller, S. T. (2023). Paid user citation four. Engineering Journal, 8(2), 89-101.
Wilson, A. (2023). Paid user citation five. Technology Review.
<<<END_JOB>>>
<<JOB_ID:test_job_3>>
Clark, P. (2023). Processing job citation. Research Paper.
Taylor, J. R. (2023). Another processing citation. Journal Article.
<<<END_JOB>>>
"""

    with open(test_log_path, 'w', encoding='utf-8') as f:
        f.write(log_content)

    logger.info(f"Created test citation log at {test_log_path}")

def test_integration():
    """Test the CitationLogParser integration."""
    logger.info("Starting CitationLogParser integration test")

    # Create temporary test files
    with tempfile.TemporaryDirectory() as temp_dir:
        test_log_path = os.path.join(temp_dir, "logs", "citations.log")
        test_db_path = os.path.join(temp_dir, "data", "validations.db")

        # Set environment variables for test paths
        os.environ['TEST_VALIDATIONS_DB_PATH'] = test_db_path

        # Create test data
        create_test_validation_database(test_db_path)
        create_test_citation_log(test_log_path)

        # Create sample jobs dictionary (mimicking app.py global jobs)
        jobs_dict = {
            "test_job_1": {
                "status": "completed",
                "created_at": 1638360000,
                "citation_count": 0,  # Will be updated by parser
                "user_type": "free"
            },
            "test_job_2": {
                "status": "completed",
                "created_at": 1638360100,
                "citation_count": 0,  # Will be updated by parser
                "user_type": "paid"
            },
            "test_job_3": {
                "status": "processing",
                "created_at": 1638360200,
                "citation_count": 0,  # Will be updated by parser
                "user_type": "free"
            }
        }

        # Initialize parser
        parser = CitationLogParser(jobs_dict)

        # Test 1: process_citations_for_dashboard()
        logger.info("Test 1: process_citations_for_dashboard()")
        success = parser.process_citations_for_dashboard(test_log_path)
        assert success, "process_citations_for_dashboard() should return True"

        # Test 2: Verify jobs were updated with citations
        logger.info("Test 2: Verify job updates")

        # Check test_job_1
        assert "test_job_1" in jobs_dict, "test_job_1 should still exist in jobs_dict"
        job1 = jobs_dict["test_job_1"]
        assert job1.get("has_citations") == True, "test_job_1 should have citations"
        assert job1.get("citation_count") == 3, f"test_job_1 should have 3 citations, got {job1.get('citation_count')}"
        assert "citations" in job1, "test_job_1 should have citations array"
        assert len(job1["citations"]) == 3, "test_job_1 citations array should have 3 items"

        # Check test_job_2
        assert "test_job_2" in jobs_dict, "test_job_2 should still exist in jobs_dict"
        job2 = jobs_dict["test_job_2"]
        assert job2.get("has_citations") == True, "test_job_2 should have citations"
        assert job2.get("citation_count") == 5, f"test_job_2 should have 5 citations, got {job2.get('citation_count')}"
        assert len(job2["citations"]) == 5, "test_job_2 citations array should have 5 items"

        # Check test_job_3
        assert "test_job_3" in jobs_dict, "test_job_3 should still exist in jobs_dict"
        job3 = jobs_dict["test_job_3"]
        assert job3.get("has_citations") == True, "test_job_3 should have citations"
        assert job3.get("citation_count") == 2, f"test_job_3 should have 2 citations, got {job3.get('citation_count')}"
        assert len(job3["citations"]) == 2, "test_job_3 citations array should have 2 items"

        # Test 3: get_jobs_with_citations()
        logger.info("Test 3: get_jobs_with_citations()")
        jobs_with_citations = parser.get_jobs_with_citations()
        assert len(jobs_with_citations) == 3, f"Should have 3 jobs with citations, got {len(jobs_with_citations)}"
        assert "test_job_1" in jobs_with_citations, "test_job_1 should be in jobs_with_citations"
        assert "test_job_2" in jobs_with_citations, "test_job_2 should be in jobs_with_citations"
        assert "test_job_3" in jobs_with_citations, "test_job_3 should be in jobs_with_citations"

        # Test 4: job_exists_in_validations()
        logger.info("Test 4: job_exists_in_validations()")
        assert parser.job_exists_in_validations("test_job_1") == True, "test_job_1 should exist in validations"
        assert parser.job_exists_in_validations("test_job_2") == True, "test_job_2 should exist in validations"
        assert parser.job_exists_in_validations("test_job_3") == True, "test_job_3 should exist in validations"
        assert parser.job_exists_in_validations("nonexistent_validation") == False, "nonexistent_validation should not exist"

        # Test 5: Duplicate prevention
        logger.info("Test 5: Duplicate prevention")
        initial_counts = {
            "test_job_1": jobs_dict["test_job_1"].get("citation_count", 0),
            "test_job_2": jobs_dict["test_job_2"].get("citation_count", 0),
            "test_job_3": jobs_dict["test_job_3"].get("citation_count", 0)
        }

        # Run processing again
        parser.process_citations_for_dashboard(test_log_path)

        # Verify citation counts didn't change (duplicates prevented)
        assert jobs_dict["test_job_1"].get("citation_count", 0) == initial_counts["test_job_1"], "test_job_1 citation count should not change on duplicate processing"
        assert jobs_dict["test_job_2"].get("citation_count", 0) == initial_counts["test_job_2"], "test_job_2 citation count should not change on duplicate processing"
        assert jobs_dict["test_job_3"].get("citation_count", 0) == initial_counts["test_job_3"], "test_job_3 citation count should not change on duplicate processing"

        # Test 6: add_citations_to_job() with non-existent job
        logger.info("Test 6: add_citations_to_job() with non-existent job")
        result = parser.add_citations_to_job("nonexistent_job", ["Test citation"])
        assert result == False, "add_citations_to_job() should return False for non-existent job"

        logger.info("All integration tests passed!")

if __name__ == "__main__":
    try:
        test_integration()
        print("✅ All integration tests passed!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}")
        print(f"❌ Integration test failed: {str(e)}")
        sys.exit(1)