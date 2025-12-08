#!/usr/bin/env python3
"""
Test script to verify provider routing implementation.
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_provider_routing():
    """Test the provider routing with different headers."""

    test_citation = "Smith, J. (2023). Test citation. Journal of Testing, 15(2), 123-145."

    test_cases = [
        {
            "name": "Default (no header) - should use OpenAI",
            "headers": {},
            "expected_provider": "model_a"
        },
        {
            "name": "model_a header - should use OpenAI",
            "headers": {"X-Model-Preference": "model_a"},
            "expected_provider": "model_a"
        },
        {
            "name": "model_b header - should use Gemini",
            "headers": {"X-Model-Preference": "model_b"},
            "expected_provider": "model_b"
        },
        {
            "name": "invalid header - should fallback to OpenAI",
            "headers": {"X-Model-Preference": "invalid"},
            "expected_provider": "model_a"
        }
    ]

    for test_case in test_cases:
        print(f"\n--- Testing: {test_case['name']} ---")

        payload = {
            "citations": test_citation,
            "style": "apa7"
        }

        try:
            response = requests.post(
                f"{BASE_URL}/api/validate",
                json=payload,
                headers=test_case["headers"]
            )

            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success - Status: {response.status_code}")
                print(f"   Results count: {len(result.get('results', []))}")

                # Check dashboard to see provider info
                time.sleep(0.5)  # Give time for job to be stored
                dashboard_response = requests.get(f"{BASE_URL}/api/dashboard")
                if dashboard_response.status_code == 200:
                    dashboard_data = dashboard_response.json()
                    if dashboard_data.get("jobs"):
                        latest_job = dashboard_data["jobs"][0]
                        actual_provider = latest_job.get("provider", "unknown")
                        print(f"   Provider used: {actual_provider}")
                        if actual_provider == test_case["expected_provider"]:
                            print(f"   ✅ Provider routing correct!")
                        else:
                            print(f"   ❌ Expected {test_case['expected_provider']}, got {actual_provider}")

            else:
                print(f"❌ Failed - Status: {response.status_code}")
                print(f"   Error: {response.text}")

        except Exception as e:
            print(f"❌ Exception: {str(e)}")

def test_async_provider_routing():
    """Test provider routing for async endpoint."""
    print(f"\n--- Testing Async Provider Routing ---")

    test_citation = "Smith, J. (2023). Test citation. Journal of Testing, 15(2), 123-145."

    payload = {
        "citations": test_citation,
        "style": "apa7"
    }

    headers = {"X-Model-Preference": "model_b"}

    try:
        # Create async job
        response = requests.post(
            f"{BASE_URL}/api/validate/async",
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data["job_id"]
            print(f"✅ Async job created: {job_id}")

            # Check job status
            time.sleep(2)  # Give time for job to start
            status_response = requests.get(f"{BASE_URL}/api/jobs/{job_id}")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"   Job status: {status_data['status']}")

                # Check dashboard for provider info
                dashboard_response = requests.get(f"{BASE_URL}/api/dashboard")
                if dashboard_response.status_code == 200:
                    dashboard_data = dashboard_response.json()
                    jobs = dashboard_data.get("jobs", [])
                    job = next((j for j in jobs if j["id"] == job_id), None)
                    if job:
                        provider = job.get("provider", "unknown")
                        print(f"   Provider used: {provider}")
        else:
            print(f"❌ Failed to create async job - Status: {response.status_code}")

    except Exception as e:
        print(f"❌ Exception: {str(e)}")

if __name__ == "__main__":
    print("Testing Provider Routing Implementation")
    print("=" * 50)

    test_provider_routing()
    test_async_provider_routing()

    print(f"\n" + "=" * 50)
    print("Test completed!")