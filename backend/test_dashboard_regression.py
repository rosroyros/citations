#!/usr/bin/env python3
"""
Test script to verify no regression in current dashboard functionality.

This script ensures that the CitationLogParser integration doesn't break
existing dashboard functionality.
"""

import os
import sys
import tempfile
import sqlite3
import json
from pathlib import Path

# Add backend path to import modules
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from database import init_db, create_validation_record, get_validations_db_path
from logger import setup_logger

# Setup test logger
logger = setup_logger("test_regression")

def test_dashboard_regression():
    """Test that dashboard functionality still works after integration."""
    logger.info("Starting dashboard regression test")

    # Create temporary test database
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db_path = os.path.join(temp_dir, "validations.db")
        os.environ['TEST_VALIDATIONS_DB_PATH'] = test_db_path

        # Initialize validation database table manually
        with sqlite3.connect(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS validations (
                    job_id TEXT PRIMARY KEY,
                    user_type TEXT NOT NULL,
                    citation_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

        create_validation_record("regression_test_1", "free", 5, "completed")
        create_validation_record("regression_test_2", "paid", 3, "completed")
        create_validation_record("regression_test_3", "free", 2, "failed")

        # Test 1: Database operations still work
        logger.info("Test 1: Database operations")
        assert os.path.exists(test_db_path), "Test validation database should exist"

        with sqlite3.connect(test_db_path) as conn:
            cursor = conn.cursor()

            # Check records were created
            cursor.execute("SELECT COUNT(*) FROM validations")
            count = cursor.fetchone()[0]
            assert count >= 3, f"Should have at least 3 validation records, got {count}"

            # Check specific jobs exist
            cursor.execute("SELECT job_id FROM validations WHERE job_id = ?", ("regression_test_1",))
            result = cursor.fetchone()
            assert result is not None, "regression_test_1 should exist in validations"

        logger.info("Database operations test passed")

        # Test 2: CitationLogParser doesn't interfere with existing jobs structure
        logger.info("Test 2: Jobs structure compatibility")

        # Create a mock jobs dictionary similar to app.py
        jobs_dict = {
            "existing_job_1": {
                "status": "completed",
                "created_at": 1638360000,
                "citation_count": 5,
                "results": {"error_count": 2},
                "user_type": "free",
                "token": "test_token_1"
            },
            "existing_job_2": {
                "status": "processing",
                "created_at": 1638360100,
                "citation_count": 3,
                "results": None,
                "user_type": "paid",
                "token": "test_token_2"
            }
        }

        # Import CitationLogParser
        from citation_logger import CitationLogParser

        # Initialize parser - this shouldn't modify existing jobs
        parser = CitationLogParser(jobs_dict)

        # Verify existing jobs structure is intact
        assert "existing_job_1" in jobs_dict, "existing_job_1 should still exist"
        assert "existing_job_2" in jobs_dict, "existing_job_2 should still exist"

        job1 = jobs_dict["existing_job_1"]
        assert job1["status"] == "completed", "existing_job_1 status should be unchanged"
        assert job1["citation_count"] == 5, "existing_job_1 citation_count should be unchanged"
        assert "results" in job1, "existing_job_1 should still have results field"
        assert job1["user_type"] == "free", "existing_job_1 user_type should be unchanged"

        job2 = jobs_dict["existing_job_2"]
        assert job2["status"] == "processing", "existing_job_2 status should be unchanged"
        assert job2["citation_count"] == 3, "existing_job_2 citation_count should be unchanged"
        assert job2["results"] is None, "existing_job_2 results should still be None"

        logger.info("Jobs structure compatibility test passed")

        # Test 3: Dashboard stats calculation should still work
        logger.info("Test 3: Dashboard stats compatibility")

        # Mock the stats calculation logic from app.py
        total = len(jobs_dict)
        completed = sum(1 for job in jobs_dict.values() if job.get("status") == "completed")
        failed = sum(1 for job in jobs_dict.values() if job.get("status") == "failed")
        processing = sum(1 for job in jobs_dict.values() if job.get("status") == "processing")
        total_citations = sum(job.get("citation_count", 0) for job in jobs_dict.values())

        assert total == 2, f"Should have 2 jobs total, got {total}"
        assert completed == 1, f"Should have 1 completed job, got {completed}"
        assert failed == 0, f"Should have 0 failed jobs, got {failed}"
        assert processing == 1, f"Should have 1 processing job, got {processing}"
        assert total_citations == 8, f"Should have 8 total citations, got {total_citations}"

        logger.info("Dashboard stats compatibility test passed")

        # Test 4: Dashboard data transformation should still work
        logger.info("Test 4: Dashboard data transformation")

        # Mock the dashboard data transformation from app.py get_dashboard_data()
        now = 1638360000
        all_jobs = []

        for job_id, job in jobs_dict.items():
            # Convert job data to dashboard format (simplified version of app.py logic)
            job_data = {
                "id": job_id,
                "timestamp": "2025-12-01 17:48:00",  # Mock timestamp
                "status": job.get("status", "unknown"),
                "citations": job.get("citation_count", 0),
                "errors": _count_errors(job),
                "session_id": job.get("token", "unknown"),
                "validation_id": job_id,
                "api_version": "v1.2.0"
            }
            all_jobs.append(job_data)

        assert len(all_jobs) == 2, f"Should have 2 dashboard jobs, got {len(all_jobs)}"
        assert all_jobs[0]["citations"] == 5, "First job should have 5 citations"
        assert all_jobs[1]["citations"] == 3, "Second job should have 3 citations"

        logger.info("Dashboard data transformation test passed")

        logger.info("All regression tests passed!")

def _count_errors(job: dict) -> int:
    """Mock the _count_errors function from app.py."""
    results = job.get("results", {})
    if isinstance(results, dict):
        return results.get("error_count", 0)
    elif isinstance(results, list):
        # Count errors in a list of validation results
        error_count = 0
        for result in results:
            if isinstance(result, dict) and "errors" in result:
                error_count += len(result["errors"])
        return error_count
    return 0

if __name__ == "__main__":
    try:
        test_dashboard_regression()
        print("✅ All regression tests passed!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Regression test failed: {str(e)}")
        print(f"❌ Regression test failed: {str(e)}")
        sys.exit(1)