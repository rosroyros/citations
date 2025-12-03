#!/usr/bin/env python3
"""
Simple test for gating log parsing
"""
import sys
import os

# Add dashboard directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from log_parser import extract_gating_decision

def test_gating_extraction():
    """Test gating decision extraction"""
    print("Testing gating decision extraction...")

    test_cases = [
        {
            "name": "Quoted reason",
            "input": "2025-11-30 22:00:05,456 - gating - INFO - GATING_DECISION: job_id=8a7d7d5a-4f8d-4a2c-9a8c-9a1b8e8b1b8e user_type=free results_gated=True reason='Free tier limit reached'",
            "expected_job_id": "8a7d7d5a-4f8d-4a2c-9a8c-9a1b8e8b1b8e",
            "expected_gated": True,
            "expected_reason": "Free tier limit reached"
        },
        {
            "name": "Paid user (not gated)",
            "input": "2025-11-30 22:01:15,123 - gating - INFO - GATING_DECISION: job_id=abc-123-def user_type=paid results_gated=False reason='Paid user bypasses gating'",
            "expected_job_id": "abc-123-def",
            "expected_gated": False,
            "expected_reason": "Paid user bypasses gating"
        },
        {
            "name": "Non-matching line",
            "input": "This is just a regular log line with no gating info",
            "expected": None
        }
    ]

    passed = 0
    total = len(test_cases)

    for i, test_case in enumerate(test_cases, 1):
        result = extract_gating_decision(test_case["input"])

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
                test_case["expected_gated"],
                test_case["expected_reason"]
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
    print("=== Testing Gating Decision Extraction ===\n")

    success = test_gating_extraction()

    if success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())