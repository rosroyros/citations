import sys
import os
import sqlite3
import tempfile
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from dashboard.database import DatabaseManager
from dashboard.log_parser import extract_test_job_indicator, parse_job_events

def test_database_schema():
    print("Testing Database Schema...")
    with tempfile.NamedTemporaryFile() as tmp:
        db = DatabaseManager(tmp.name)
        schema = db.get_table_schema('validations')
        
        has_column = any('is_test_job' in col for col in schema)
        if has_column:
            print("PASS: is_test_job column found.")
        else:
            print("FAIL: is_test_job column NOT found.")
            print("Schema:", schema)

def test_log_extraction():
    print("\nTesting Log Extraction...")
    line = "2025-12-09 21:00:00 INFO: TEST_JOB_DETECTED: job_id=test-uuid-123 indicator=[TEST_JOB_DETECTED]"
    job_id = extract_test_job_indicator(line)
    
    if job_id == "test-uuid-123":
        print("PASS: Extracted job_id correctly.")
    else:
        print(f"FAIL: Expected test-uuid-123, got {job_id}")

def test_log_parsing_integration():
    print("\nTesting Log Parsing Integration...")
    lines = [
        "2025-12-09 21:00:00 INFO: Creating async job test-uuid-123 for free user",
        "2025-12-09 21:00:01 INFO: TEST_JOB_DETECTED: job_id=test-uuid-123 indicator=[TEST_JOB_DETECTED]"
    ]
    
    jobs = parse_job_events(lines)
    
    if "test-uuid-123" in jobs:
        job = jobs["test-uuid-123"]
        if job.get("is_test_job"):
            print("PASS: Job marked as test job.")
        else:
            print(f"FAIL: Job NOT marked as test job. Job data: {job}")
    else:
        print("FAIL: Job not found.")

def test_db_insertion():
    print("\nTesting DB Insertion...")
    with tempfile.NamedTemporaryFile() as tmp:
        db = DatabaseManager(tmp.name)
        
        # Test INSERT
        db.insert_validation({
            "job_id": "job-1",
            "created_at": "2025-01-01T00:00:00Z",
            "user_type": "free",
            "is_test_job": True,
            "error_message": None
        })
        
        val = db.get_validation("job-1")
        # SQLite stores booleans as 0/1
        if val and val.get("is_test_job") in [1, True]:
             print("PASS: Inserted is_test_job=True")
        else:
             print(f"FAIL: Inserted is_test_job failed. Val: {val}")

        # Test UPDATE
        db.insert_validation({
            "job_id": "job-1",
            "is_test_job": False 
        })
        
        val = db.get_validation("job-1")
        if val and val.get("is_test_job") in [0, False]:
             print("PASS: Updated is_test_job=False")
        else:
             print(f"FAIL: Updated is_test_job failed. Val: {val}")

if __name__ == "__main__":
    test_database_schema()
    test_log_extraction()
    test_log_parsing_integration()
    test_db_insertion()
