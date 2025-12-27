#!/usr/bin/env python3
"""
Test script to verify gating log parsing functionality
"""
import sys
import os
from datetime import datetime

# Add dashboard directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from log_parser import extract_gating_decision, parse_logs

def test_extract_gating_decision():
    """Test the extract_gating_decision function with sample log lines"""
    print("Testing extract_gating_decision function...")

    test_cases = [
        {
            "input": "2025-11-30 22:00:05,456 - gating - INFO - GATING_DECISION: job_id=8a7d7d5a-4f8d-4a2c-9a8c-9a1b8e8b1b8e user_type=free results_gated=True reason='Free tier limit reached'",
            "expected": ("8a7d7d5a-4f8d-4a2c-9a8c-9a1b8e8b1b8e", True, "Free tier limit reached")
        },
        {
            "input": "2025-11-30 22:01:15,123 - gating - INFO - GATING_DECISION: job_id=abc-123-def user_type=paid results_gated=False reason='Paid user bypasses gating'",
            "expected": ("abc-123-def", False, "Paid user bypasses gating")
        },
        {
            "input": "2025-11-30 22:02:30,789 - gating - INFO - GATING_DECISION: job_id=xyz-789-uvw user_type=anonymous results_gated=True reason=Anonymous user limit",
            "expected": ("xyz-789-uvw", True, "Anonymous user limit")
        },
        {
            # New: Early return path logs from citation_validator logger instead of gating
            "input": "2025-12-27 10:00:00 - citation_validator - INFO - GATING_DECISION: job_id=abc-def-123 user_type=free results_gated=True reason='Free tier limit exceeded'",
            "expected": ("abc-def-123", True, "Free tier limit exceeded")
        },
        {
            "input": "This is not a gating decision log line",
            "expected": None
        }
    ]

    passed = 0
    total = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        result = extract_gating_decision(test_case["input"])
        expected = test_case["expected"]

        if result == expected:
            print(f"✅ Test {i}: PASSED")
            passed += 1
        else:
            print(f"❌ Test {i}: FAILED")
            print(f"   Input: {test_case['input']}")
            print(f"   Expected: {expected}")
            print(f"   Got: {result}")

    print(f"\nExtract function: {passed}/{total} tests passed")
    return passed == total

def test_log_parsing_integration():
    """Test the integration with the full log parser"""
    print("\nTesting integration with full log parser...")

    # Create sample log content
    sample_log = [
        "2025-11-30 22:00:00,000 - citation_validator - INFO - Creating async job 8a7d7d5a-4f8d-4a2c-9a8c-9a1b8e8b1b8e for free user",
        "2025-11-30 22:00:05,456 - gating - INFO - GATING_DECISION: job_id=8a7d7d5a-4f8d-4a2c-9a8c-9a1b8e8b1b8e user_type=free results_gated=True reason='Free tier limit reached'",
        "2025-11-30 22:00:10,123 - citation_validator - INFO - Job 8a7d7d5a-4f8d-4a2c-9a8c-9a1b8e8b1b8e: Completed successfully",
    ]

    # Test the parsing
    from log_parser import extract_creation_from_lines, extract_completion_and_duration_from_lines, extract_citations_from_all_lines

    jobs = {}

    # Parse creation
    jobs = extract_creation_from_lines(sample_log, jobs)

    # Parse gating decisions (using our new function integrated in the main parser)
    for line in sample_log:
        gating_result = extract_gating_decision(line)
        if gating_result:
            job_id, results_gated, reason = gating_result
            if job_id in jobs:
                jobs[job_id]["results_gated"] = results_gated

    # Parse completion
    jobs = extract_completion_and_duration_from_lines(sample_log, jobs)

    # Check results
    expected_job_id = "8a7d7d5a-4f8d-4a2c-9a8c-9a1b8e8b1b8e"

    if expected_job_id in jobs:
        job = jobs[expected_job_id]
        print(f"✅ Job found: {job['job_id']}")
        print(f"   User type: {job.get('user_type', 'N/A')}")
        print(f"   Status: {job.get('status', 'N/A')}")
        print(f"   Results gated: {job.get('results_gated', 'N/A')}")

        # Check if gating was parsed correctly
        if job.get('results_gated') == True:
            print("✅ Gating information parsed correctly")
            return True
        else:
            print("❌ Gating information not parsed correctly")
            return False
    else:
        print("❌ Job not found in parsed results")
        return False

def main():
    """Run all tests"""
    print("=== Testing Gating Log Parsing ===\n")

    test1_passed = test_extract_gating_decision()
    test2_passed = test_log_parsing_integration()

    print(f"\n=== Test Results ===")
    print(f"Extract function test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"Integration test: {'PASSED' if test2_passed else 'FAILED'}")

    if test1_passed and test2_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())