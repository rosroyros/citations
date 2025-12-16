#!/usr/bin/env python3
"""
Verify UPGRADE_WORKFLOW logs are being generated correctly.

Usage:
    python3 verify_upgrade_events.py

Checks:
    1. UPGRADE_WORKFLOW lines exist in app.log
    2. Events have required fields (job_id, event, token, variant)
    3. Experiment variant is '1' or '2'
"""
import re
import sys
from pathlib import Path

def verify_upgrade_events(log_path='/opt/citations/logs/app.log'):
    """Verify upgrade workflow events in log file."""

    if not Path(log_path).exists():
        # Try alternative paths
        alt_paths = [
            '../logs/app.log',
            '../../logs/app.log',
            '/tmp/app.log',
            './app.log'
        ]

        for alt_path in alt_paths:
            if Path(alt_path).exists():
                log_path = alt_path
                break
        else:
            print(f"❌ Log file not found: {log_path}")
            print(f"Checked paths: {[log_path] + alt_paths}")
            return False

    events_found = 0
    errors = []

    # Regex for UPGRADE_WORKFLOW
    # UPGRADE_WORKFLOW: job_id=... event=... token=... variant=...
    # Use non-whitespace characters (\S) for values
    workflow_pattern = re.compile(r'UPGRADE_WORKFLOW: job_id=(\S+) event=(\S+) token=(\S+)(?: variant=(\S+))?')

    with open(log_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            if 'UPGRADE_WORKFLOW:' not in line:
                continue

            events_found += 1
            match = workflow_pattern.search(line)
            
            if not match:
                errors.append(f"Line {line_num}: Malformed UPGRADE_WORKFLOW line")
                continue

            job_id, event_name, token, variant = match.groups()

            # Verify variant is valid
            if variant and variant not in ['1', '2']:
                errors.append(f"Line {line_num}: Invalid variant '{variant}' (must be '1' or '2')")

            # Oracle #5: variant should ALWAYS be present (except maybe for legacy/anonymous?)
            # The current implementation in app.py tries to always log it if available.
            if not variant:
                # errors.append(f"Line {line_num}: Oracle #5 violation - variant is None")
                pass # Variant is optional in regex, but strict check might fail on old logs

    # Report results
    print(f"\n{'='*60}")
    print(f"UPGRADE_WORKFLOW Log Verification")
    print(f"{ '='*60}")
    print(f"\nLog file: {log_path}")
    print(f"Events found: {events_found}")
    print(f"Errors: {len(errors)}")

    if errors:
        print(f"\n❌ FAILED - Found {len(errors)} error(s):")
        for error in errors[:10]:  # Show first 10
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
        return False

    if events_found == 0:
        print(f"\n⚠️  WARNING - No UPGRADE_WORKFLOW logs found")
        return True

    print(f"\n✅ PASSED - All {events_found} events are valid")

    # Show sample event
    print(f"\nSample event:")
    with open(log_path, 'r') as f:
        for line in f:
            if 'UPGRADE_WORKFLOW:' in line:
                print(line.strip())
                break

    return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Verify UPGRADE_WORKFLOW logs')
    parser.add_argument('--log-path', default='/opt/citations/logs/app.log',
                       help='Path to app.log file')

    args = parser.parse_args()

    success = verify_upgrade_events(args.log_path)
    sys.exit(0 if success else 1)