#!/usr/bin/env python3
"""Debug script with verbose logging."""

import tempfile
import os
import logging
from log_parser import CitationLogParser

# Enable debug logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def create_test_log_file(content: str) -> str:
    """Create a temporary log file with test content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(content)
        return f.name

def debug_rotation_verbose():
    """Debug rotation with verbose logging."""

    # First rotation content (larger)
    first_rotation = """2025-12-01 19:05:00 Creating async job cafebeef-def-456-789 for paid user
2025-12-01 19:05:02 OpenAI API call completed in 15.0s
2025-12-01 19:05:02 Found 3 citation results
2025-12-01 19:05:02 Token usage: 600 prompt + 400 completion = 1000 total
2025-12-01 19:05:03 Job cafebeef-def-456-789: Completed successfully"""

    # Second rotation content (smaller)
    second_rotation = """2025-12-01 19:10:00 Creating async job deadbeef-ghi-abc-def for free user
2025-12-01 19:10:01 OpenAI API call completed in 2.0s
2025-12-01 19:10:01 Found 1 citation results
2025-12-01 19:10:01 Token usage: 300 prompt + 200 completion = 500 total
2025-12-01 19:10:02 Job deadbeef-ghi-abc-def: Completed successfully"""

    log_file = create_test_log_file(first_rotation)
    pos_file = tempfile.mktemp(suffix='.position')

    try:
        parser = CitationLogParser(log_file, pos_file)

        print(f"First file size: {os.path.getsize(log_file)}")

        # Parse first rotation
        entries = parser.parse_new_entries()
        print(f"After first rotation: {len(entries)} entries")
        if entries:
            print(f"  Job: {entries[0]['job_id']}")

        position_after_first = parser.get_current_position()
        print(f"Position after first: {position_after_first}")

        # Overwrite with second rotation (smaller)
        with open(log_file, 'w') as f:
            f.write(second_rotation)

        print(f"\nSecond file size: {os.path.getsize(log_file)}")
        print(f"Parser position before second parse: {parser.get_current_position()}")

        print("Calling parse_new_entries()...")
        # Parse second rotation
        entries = parser.parse_new_entries()
        print(f"After second rotation: {len(entries)} entries")
        if entries:
            print(f"  Job: {entries[0]['job_id']}")
        else:
            print("  No entries found!")

        position_after_second = parser.get_current_position()
        print(f"Position after second: {position_after_second}")

    finally:
        # Clean up
        if os.path.exists(log_file):
            os.unlink(log_file)
        if os.path.exists(pos_file):
            os.unlink(pos_file)

if __name__ == "__main__":
    debug_rotation_verbose()