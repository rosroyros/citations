#!/usr/bin/env python3
"""
Test the mock checkout flow to ensure credits are added after mock purchase.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

API_BASE = "http://localhost:8000"

async def test_mock_checkout():
    """Test the complete mock checkout flow."""
    async with aiohttp.ClientSession() as session:
        print("=== Testing Mock Checkout Flow ===")
        print(f"Timestamp: {datetime.now()}")

        # Step 1: Create a mock checkout
        print("\n1. Creating mock checkout...")
        token = "test_token_" + datetime.now().strftime("%Y%m%d%H%M%S")

        checkout_data = {
            "token": token,
            "productId": "2a3c8913-2e82-4f12-9eb7-767e4bc98089",  # 500 Credits
            "variantId": "1"
        }

        async with session.post(f"{API_BASE}/api/create-checkout", json=checkout_data) as resp:
            if resp.status != 200:
                print(f"❌ Failed to create checkout: {resp.status}")
                text = await resp.text()
                print(f"Response: {text}")
                return

            result = await resp.json()
            checkout_url = result.get("checkout_url")
            print(f"✅ Checkout created: {checkout_url}")

        # Step 2: Check initial credits (should be 0)
        print("\n2. Checking initial credits...")
        async with session.get(f"{API_BASE}/api/credits?token={token}") as resp:
            if resp.status != 200:
                print(f"❌ Failed to get credits: {resp.status}")
                return

            credits_data = await resp.json()
            initial_credits = credits_data.get("credits", 0)
            print(f"   Initial credits: {initial_credits}")

        # Step 3: Wait for mock webhook to process (background task with 1s delay)
        print("\n3. Waiting for mock webhook to process...")
        await asyncio.sleep(2)

        # Step 4: Check credits again (should have increased)
        print("\n4. Checking credits after mock webhook...")
        async with session.get(f"{API_BASE}/api/credits?token={token}") as resp:
            if resp.status != 200:
                print(f"❌ Failed to get credits: {resp.status}")
                return

            credits_data = await resp.json()
            final_credits = credits_data.get("credits", 0)
            active_pass = credits_data.get("active_pass")
            print(f"   Final credits: {final_credits}")
            print(f"   Active pass: {active_pass}")

        # Step 5: Verify the test passed
        print("\n=== Test Results ===")
        if final_credits > initial_credits:
            print(f"✅ SUCCESS: Credits added! ({initial_credits} → {final_credits})")
            return True
        else:
            print(f"❌ FAILURE: Credits not added ({initial_credits} → {final_credits})")
            return False

async def main():
    print("Starting mock checkout test...")
    success = await test_mock_checkout()

    if success:
        print("\n🎉 Mock checkout flow is working correctly!")
        exit(0)
    else:
        print("\n💥 Mock checkout flow failed!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())