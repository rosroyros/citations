#!/usr/bin/env python3
"""
Test script to verify reveal event parsing functionality
"""
import sys
import os

# Add dashboard directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from log_parser import extract_reveal_event

def test_reveal_event_extraction():
    """Test reveal event extraction"""
    print("Testing reveal event extraction...")

    test_cases = [
        {
            "name": "Standard reveal event",
            "input": "2025-12-02 22:30:15,123 - citation_validator - INFO - REVEAL_EVENT: job_id=8a7d7d5a-4f8d-4a2c-9a8c-9a1b8e8b1b8e outcome=revealed",
            "expected_job_id": "8a7d7d5a-4f8d-4a2c-9a8c-9a1b8e8b1b8e",
            "expected_outcome": "revealed"
        },
        {
            "name": "Dismissed outcome",
            "input": "2025-12-02 22:31:20,456 - citation_validator - INFO - REVEAL_EVENT: job_id=abc-123-def outcome=dismissed",
            "expected_job_id": "abc-123-def",
            "expected_outcome": "dismissed"
        },
        {
            "name": "Non-matching line",
            "input": "This is just a regular log line with no reveal info",
            "expected": None
        }
    ]

    passed = 0
    total = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        result = extract_reveal_event(test_case["input"])

        if "expected_job_id" not in test_case:
            # This test expects None
            if result is None:
                print(f"✅ Test {i} ({test_case['name']}): PASSED")
                passed += 1
            else:
                print(f"❌ Test {i} ({test_case['name']}): FAILED - Expected None but got {result}")
        else:
            # This test expects a specific tuple
            expected_tuple = (
                test_case["expected_job_id"],
                test_case["expected_outcome"]
            )

            if result == expected_tuple:
                print(f"✅ Test {i} ({test_case['name']}): PASSED")
                passed += 1
            else:
                print(f"❌ Test {i} ({test_case['name']}): FAILED")
                print(f"   Expected: {expected_tuple}")
                print(f"   Got: {result}")

    print(f"\nResults: {passed}/{total} tests passed")
    return passed == total

def main():
    """Run the test"""
    print("=== Testing Reveal Event Extraction ===\n")

    success = test_reveal_event_extraction()

    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())