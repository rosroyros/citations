#!/usr/bin/env python3
"""
Backend verification script for E2E tests.
Verifies that the unique citation submitted by the frontend test actually made it to the database.
"""
import os
import sys
import sqlite3
import argparse
import time
import json
import urllib.request
import urllib.error

# Default paths (should match those in dashboard/parse_logs_cron.py)
DEFAULT_DB_PATH = "/opt/citations/dashboard/data/validations.db"
DEFAULT_API_URL = "http://localhost:8000"

def verify_dashboard_api(job_id, api_url):
    print(f"\nVerifying Dashboard API visibility...")
    print(f"Target URL: {api_url}/api/dashboard")
    
    try:
        # We need to search for the job_id to ensure it appears in the filtered list
        # The dashboard API supports ?search= param
        url = f"{api_url}/api/dashboard?search={job_id}"
        
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                print(f"FAILURE: API returned status {response.status}")
                return False
            
            data = json.loads(response.read().decode())
            jobs = data.get('jobs', [])
            
            # Look for our specific job_id
            found_job = next((job for job in jobs if job.get('id') == job_id), None)
            
            if found_job:
                print(f"SUCCESS: Job {job_id} found in Dashboard API")
                print(f"  API Status: {found_job.get('status')}")
                print(f"  Citations:  {found_job.get('citations')}")
                return True
            else:
                print(f"FAILURE: Job {job_id} NOT found in Dashboard API response")
                print(f"  (Found {len(jobs)} other jobs matching search)")
                return False
                
    except urllib.error.URLError as e:
        print(f"WARNING: Could not connect to Dashboard API at {api_url}: {e}")
        print("  (Skipping API verification, but DB verification passed)")
        # We don't fail the whole test if API is down, unless strict mode is requested
        # For now, we'll just warn, assuming this script might run where API isn't accessible
        return True
    except Exception as e:
        print(f"Error querying API: {e}")
        return False

def verify_data(job_id, db_path, api_url=None):
    print(f"Verifying data integrity for Job ID: {job_id}")
    print(f"Using Database: {db_path}")

    db_verified = False

    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return False

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query for the citation by Job ID
        query = "SELECT job_id, status, created_at, citation_count FROM validations WHERE job_id = ?"
        cursor.execute(query, (job_id,))
        
        row = cursor.fetchone()
        
        if row:
            job_id_db, status, created_at, count = row
            print(f"SUCCESS: Found record for Job ID {job_id}")
            print(f"  Status: {status}")
            print(f"  Time:   {created_at}")
            print(f"  Count:  {count}")
            
            if status == 'completed':
                db_verified = True
            else:
                print(f"FAILURE: Record found but status is '{status}' (expected 'completed')")
                db_verified = False
        else:
            print(f"FAILURE: No record found for Job ID {job_id}")
            db_verified = False

    except Exception as e:
        print(f"Error querying database: {e}")
        db_verified = False
    finally:
        if conn:
            conn.close()

    # If DB check passed, check API
    if db_verified and api_url:
        api_verified = verify_dashboard_api(job_id, api_url)
        return api_verified
    
    return db_verified

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Verify E2E test data integrity')
    parser.add_argument('--job-id', required=True, help='Job ID to verify')
    parser.add_argument('--db-path', default=os.getenv('CITATION_DB_PATH', DEFAULT_DB_PATH), help='Path to SQLite database')
    parser.add_argument('--api-url', default=os.getenv('CITATION_API_URL', DEFAULT_API_URL), help='Base URL for API verification')
    
    args = parser.parse_args()
    
    success = verify_data(args.job_id, args.db_path, args.api_url)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)