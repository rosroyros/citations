#!/usr/bin/env python3
"""
Test script to verify the test job indicator functionality
"""
import requests
import json
import time

# Test citation with testtesttest marker
test_citation = """
This is a test citation that includes the testtesttest marker to ensure it gets flagged as a test job.

Smith, J. (2023). testtesttest: A study on citation validation. Journal of Testing, 45(2), 123-145.
"""

# Test data
request_data = {
    "citations": test_citation,
    "style": "apa7"
}

print("Testing test job indicator functionality...")
print(f"Sending citation with 'testtesttest' marker")

# Send request
response = requests.post(
    "http://localhost:8000/api/validate/async",
    json=request_data,
    headers={"Content-Type": "application/json"}
)

if response.status_code == 200:
    data = response.json()
    job_id = data.get("job_id")
    print(f"✓ Job created successfully: {job_id}")

    # Poll for completion
    print("Polling for job completion...")
    for i in range(60):  # Max 2 minutes
        response = requests.get(f"http://localhost:8000/api/jobs/{job_id}")
        if response.status_code == 200:
            job_data = response.json()
            status = job_data.get("status")

            if status == "completed":
                print("✓ Job completed successfully")
                print("Check the dashboard logs for TEST_JOB_DETECTED entry")
                print("Check the dashboard to see if this job is filtered out")
                break
            elif status == "failed":
                print(f"✗ Job failed: {job_data.get('error', 'Unknown error')}")
                break
            else:
                print(f"  Status: {status}...")
                time.sleep(2)
        else:
            print(f"✗ Failed to check job status: {response.status_code}")
            break
else:
    print(f"✗ Failed to create job: {response.status_code}")
    print(response.text)