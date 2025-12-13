#!/usr/bin/env python3
"""
Test that mock checkout URLs use the correct host from the request.
"""

import asyncio
import aiohttp
import json

API_BASE = "http://10.0.0.222:8000"  # Using network IP

async def test_host_aware_checkout():
    """Test that mock checkout returns correct host-based URL."""
    print("=== Testing Host-Aware Mock Checkout ===")
    print(f"Using API endpoint: {API_BASE}")

    async with aiohttp.ClientSession() as session:
        # Test with network host
        headers = {
            'Host': '10.0.0.222:5173',  # Simulate frontend proxy
            'Content-Type': 'application/json'
        }

        checkout_data = {
            "token": "test_host_" + str(asyncio.get_event_loop().time()),
            "productId": "2a3c8913-2e82-4f12-9eb7-767e4bc98089",  # 500 Credits
            "variantId": "1"
        }

        print(f"\n1. Testing with Host header: {headers['Host']}")
        print(f"   Request data: {checkout_data}")

        async with session.post(
            f"{API_BASE}/api/create-checkout",
            json=checkout_data,
            headers=headers
        ) as resp:
            if resp.status != 200:
                print(f"❌ Failed to create checkout: {resp.status}")
                text = await resp.text()
                print(f"Response: {text}")
                return False

            result = await resp.json()
            checkout_url = result.get("checkout_url")
            print(f"✅ Checkout URL: {checkout_url}")

            # Verify the URL uses the correct host
            if "10.0.0.222:5173" in checkout_url:
                print(f"✅ SUCCESS: URL uses network host (10.0.0.222:5173)")
            else:
                print(f"❌ FAILURE: URL does not use network host")
                print(f"   Expected: http://10.0.0.222:5173/success?token=...")
                print(f"   Got: {checkout_url}")
                return False

            # Also test with different host
            headers2 = {
                'Host': '100.108.210.80:5173',
                'Content-Type': 'application/json'
            }

            checkout_data2 = {
                "token": "test_host2_" + str(asyncio.get_event_loop().time()),
                "productId": "2a3c8913-2e82-4f12-9eb7-767e4bc98089",
                "variantId": "1"
            }

            print(f"\n2. Testing with different Host header: {headers2['Host']}")

            async with session.post(
                f"{API_BASE}/api/create-checkout",
                json=checkout_data2,
                headers=headers2
            ) as resp2:
                if resp2.status != 200:
                    print(f"❌ Failed to create checkout: {resp2.status}")
                    return False

                result2 = await resp2.json()
                checkout_url2 = result2.get("checkout_url")
                print(f"✅ Checkout URL: {checkout_url2}")

                if "100.108.210.80:5173" in checkout_url2:
                    print(f"✅ SUCCESS: URL uses correct host (100.108.210.80:5173)")
                else:
                    print(f"❌ FAILURE: URL does not use correct host")
                    return False

        print("\n=== Test Results ===")
        print("✅ All tests passed! Mock checkout URLs now use the request host")
        return True

async def main():
    success = await test_host_aware_checkout()
    if success:
        print("\n🎉 Host-aware mock checkout is working correctly!")
        exit(0)
    else:
        print("\n💥 Host-aware mock checkout failed!")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())