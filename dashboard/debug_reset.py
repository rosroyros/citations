#!/usr/bin/env python3
"""Debug script for reset functionality issue."""

import tempfile
import os
from log_parser import CitationLogParser

def create_test_log_file(content: str) -> str:
    """Create a temporary log file with test content."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.log') as f:
        f.write(content)
        return f.name

def debug_reset_issue():
    """Debug the reset functionality issue."""

    log_content = """2025-12-01 18:00:00 Creating async job reset-1 for free user
2025-12-01 18:00:03 OpenAI API call completed in 5.0s
2025-12-01 18:00:03 Found 2 citation results
2025-12-01 18:00:03 Token usage: 500 prompt + 250 completion = 750 total
2025-12-01 18:00:05 Job reset-1: Completed successfully"""

    log_file = create_test_log_file(log_content)
    pos_file = tempfile.mktemp(suffix='.position')

    try:
        print(f"Log file: {log_file}")
        print(f"Position file: {pos_file}")
        print(f"Log content:\n{log_content}")

        parser = CitationLogParser(log_file, pos_file)
        print(f"Initial position: {parser.get_current_position()}")

        # Initial parse
        entries = parser.parse_new_entries()
        print(f"Initial parse: {len(entries)} entries")
        for entry in entries:
            print(f"  Entry: {entry}")

        initial_position = parser.get_current_position()
        print(f"Position after initial parse: {initial_position}")

        # Reset position
        parser.reset_position()
        reset_position = parser.get_current_position()
        print(f"Position after reset: {reset_position}")

        # Parse again - should get entries again
        entries = parser.parse_new_entries()
        print(f"Parse after reset: {len(entries)} entries")
        for entry in entries:
            print(f"  Entry: {entry}")

    finally:
        # Clean up
        if os.path.exists(log_file):
            os.unlink(log_file)
        if os.path.exists(pos_file):
            os.unlink(pos_file)

if __name__ == "__main__":
    debug_reset_issue()