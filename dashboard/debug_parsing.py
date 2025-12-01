#!/usr/bin/env python3
"""Debug script to trace the parsing logic."""

import tempfile
import os
from log_parser import extract_creation, extract_completion, extract_timestamp

def create_test_log_file(content: str) -> str:
    """Create a temporary log file with test content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(content)
        return f.name

def debug_parsing():
    """Debug the parsing functions directly."""

    broken_log_content = """2025-12-01 18:00:00 Creating async job reset-1 for free user
2025-12-01 18:00:03 OpenAI API call completed in 5.0s
2025-12-01 18:00:03 Found 2 citation results
2025-12-01 18:00:03 Token usage: 500 prompt + 250 completion = 750 total
2025-12-01 18:00:05 Job reset-1: Completed successfully"""

    lines = broken_log_content.split('\n')

    print("=== PARSING EACH LINE ===")
    for i, line in enumerate(lines):
        print(f"\nLine {i+1}: {line}")

        timestamp = extract_timestamp(line)
        print(f"  Timestamp: {timestamp}")

        creation = extract_creation(line)
        print(f"  Creation: {creation}")

        completion = extract_completion(line)
        print(f"  Completion: {completion}")

        if creation:
            job_id, ts, user_type = creation
            print(f"    -> Job ID: {job_id}, Timestamp: {ts}, User Type: {user_type}")

if __name__ == "__main__":
    debug_parsing()