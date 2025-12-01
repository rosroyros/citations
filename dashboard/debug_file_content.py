#!/usr/bin/env python3
"""Debug script to check file content."""

import tempfile
import os

def create_test_log_file(content: str) -> str:
    """Create a temporary log file with test content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(content)
        return f.name

def debug_file_content():
    """Debug the file content."""

    working_log_content = """2025-12-01 15:30:00 Creating async job abc-123 for free user
2025-12-01 15:30:05 OpenAI API call completed in 47.0s
2025-12-01 15:30:05 Found 5 citation results
2025-12-01 15:30:05 Token usage: 1025 prompt + 997 completion = 2022 total
2025-12-01 15:30:06 Job abc-123: Completed successfully"""

    broken_log_content = """2025-12-01 18:00:00 Creating async job reset-1 for free user
2025-12-01 18:00:03 OpenAI API call completed in 5.0s
2025-12-01 18:00:03 Found 2 citation results
2025-12-01 18:00:03 Token usage: 500 prompt + 250 completion = 750 total
2025-12-01 18:00:05 Job reset-1: Completed successfully"""

    # Test working content
    print("=== WORKING CONTENT ===")
    working_file = create_test_log_file(working_log_content)
    with open(working_file, 'r') as f:
        content = f.read()
        print(f"Length: {len(content)}")
        print(f"Content repr:\n{repr(content)}")
        print(f"Content:\n{content}")

    from log_parser import CitationLogParser
    working_parser = CitationLogParser(working_file, tempfile.mktemp())
    entries = working_parser.parse_new_entries()
    print(f"Working parser result: {len(entries)} entries")

    if entries:
        print(f"First entry: {entries[0]}")

    print("\n=== BROKEN CONTENT ===")
    broken_file = create_test_log_file(broken_log_content)
    with open(broken_file, 'r') as f:
        content = f.read()
        print(f"Length: {len(content)}")
        print(f"Content repr:\n{repr(content)}")
        print(f"Content:\n{content}")

    broken_parser = CitationLogParser(broken_file, tempfile.mktemp())
    entries = broken_parser.parse_new_entries()
    print(f"Broken parser result: {len(entries)} entries")

    if entries:
        print(f"First entry: {entries[0]}")

    # Cleanup
    os.unlink(working_file)
    os.unlink(broken_file)

if __name__ == "__main__":
    debug_file_content()