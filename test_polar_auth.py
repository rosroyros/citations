#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv
from polar_sdk import Polar

async def test_polar_auth():
    load_dotenv()  # Load environment variables
    token = os.getenv('POLAR_ACCESS_TOKEN')

    if not token:
        print('❌ POLAR_ACCESS_TOKEN not found in environment')
        return

    print(f'Token starts with: {token[:10]}...')
    print(f'Token length: {len(token)}')
    print(f'Full token for debug: {token}')

    try:
        polar = Polar(access_token=token)
        print('✅ Polar client created successfully')

        # Test basic API call - get products
        print('Testing products list...')
        products = polar.products.list()
        print(f'✅ Products list works: response type {type(products)}')
        print(f'✅ Products attributes: {[attr for attr in dir(products) if not attr.startswith("_")]}')
        # Try to get items - could be .items, .products, or direct iteration
        if hasattr(products, 'items'):
            print(f'✅ Products list works: found {len(products.items)} products')
        elif hasattr(products, 'products'):
            print(f'✅ Products list works: found {len(products.products)} products')
        else:
            print(f'✅ Products list works: got response {products}')

        # Test checkout creation with our exact data
        print('Testing checkout creation...')
        checkout_request = {
            "products": [os.getenv('POLAR_PRODUCT_ID')],
            "success_url": f"{os.getenv('FRONTEND_URL')}/success?token=test-123",
            "metadata": {"token": "test-123"}
        }

        checkout = polar.checkouts.create(request=checkout_request)
        print(f'✅ Checkout created successfully: {checkout.url}')

    except Exception as e:
        print(f'❌ Error: {e}')
        print(f'❌ Error type: {type(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_polar_auth())