#!/usr/bin/env python3
"""Debug script for multiple rotation test."""

import tempfile
import os
from log_parser import extract_creation, extract_completion

def debug_rotation():
    """Debug the multiple rotation issue."""

    initial_content = """2025-12-01 19:00:00 Creating async job initial-job-abc-123 for free user
2025-12-01 19:00:03 OpenAI API call completed in 30.0s
2025-12-01 19:00:03 Found 8 citation results
2025-12-01 19:00:03 Token usage: 1200 prompt + 800 completion = 2000 total
2025-12-01 19:00:05 Job initial-job-abc-123: Completed successfully"""

    lines = initial_content.split('\n')

    print("=== TESTING JOB ID PATTERNS ===")
    for i, line in enumerate(lines):
        print(f"Line {i+1}: {line}")

        creation = extract_creation(line)
        if creation:
            job_id, ts, user_type = creation
            print(f"  -> CREATION: Job ID '{job_id}', User Type '{user_type}'")

        completion = extract_completion(line)
        if completion:
            job_id, ts = completion
            print(f"  -> COMPLETION: Job ID '{job_id}'")

if __name__ == "__main__":
    debug_rotation()