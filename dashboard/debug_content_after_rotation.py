#!/usr/bin/env python3
"""Debug content parsing after rotation."""

import tempfile
import os
from log_parser import parse_logs, extract_creation, extract_completion

def create_test_log_file(content: str) -> str:
    """Create a temporary log file with test content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(content)
        return f.name

def debug_content_after_rotation():
    """Debug content parsing after rotation."""

    # Second rotation content
    second_rotation = """2025-12-01 19:10:00 Creating async job cafebeef-feed-face-123 for free user
2025-12-01 19:10:01 OpenAI API call completed in 2.0s
2025-12-01 19:10:01 Found 1 citation results
2025-12-01 19:10:01 Token usage: 300 prompt + 200 completion = 500 total
2025-12-01 19:10:02 Job cafebeef-feed-face-123: Completed successfully"""

    log_file = create_test_log_file(second_rotation)

    try:
        print("=== Testing parse_logs on fresh file ===")
        entries = parse_logs(log_file)
        print(f"parse_logs result: {len(entries)} entries")
        if entries:
            print(f"  Job: {entries[0]['job_id']}")

        print("\n=== Testing line-by-line parsing ===")
        lines = second_rotation.split('\n')
        for i, line in enumerate(lines):
            print(f"Line {i+1}: {line}")
            creation = extract_creation(line)
            completion = extract_completion(line)
            if creation:
                print(f"  -> CREATION: {creation}")
            if completion:
                print(f"  -> COMPLETION: {completion}")

    finally:
        # Clean up
        if os.path.exists(log_file):
            os.unlink(log_file)

if __name__ == "__main__":
    debug_content_after_rotation()