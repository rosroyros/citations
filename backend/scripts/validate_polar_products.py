#!/usr/bin/env python3
"""
Polar Product Validation Script

Validates all product IDs in PRODUCT_CONFIG against Polar API to ensure:
1. Product exists in Polar
2. Price matches configured price
3. Product is active (not archived)
4. Currency is USD

Usage:
    export POLAR_ACCESS_TOKEN="your_token_here"
    python3 backend/scripts/validate_polar_products.py

Exit codes:
    0: All products valid
    1: Validation errors found
    2: Configuration or environment errors
"""

import os
import sys
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

# Add backend to path so we can import pricing_config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from pricing_config import PRODUCT_CONFIG
except ImportError as e:
    print(f"❌ Error importing pricing_config.py: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(2)


@dataclass
class ValidationResult:
    """Stores validation result for a single product"""
    product_id: str
    is_valid: bool
    errors: List[str]
    polar_data: Optional[Dict[str, Any]] = None
    config_data: Optional[Dict[str, Any]] = None


class PolarAPIError(Exception):
    """Custom exception for Polar API errors"""
    pass


class PolarProductValidator:
    """Validates product IDs against Polar API"""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.polar.sh"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_product(self, product_id: str) -> Dict[str, Any]:
        """Fetch product from Polar API"""
        url = f"{self.base_url}/v1/products/{product_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 404:
                raise PolarAPIError(f"Product {product_id} not found (404)")
            elif response.status_code == 401:
                raise PolarAPIError("Invalid or expired POLAR_ACCESS_TOKEN")
            elif response.status_code == 403:
                raise PolarAPIError("Access denied - check token permissions")
            elif response.status_code != 200:
                raise PolarAPIError(f"Polar API error: HTTP {response.status_code}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise PolarAPIError(f"Network error fetching product {product_id}: {e}")

    def validate_price(self, polar_price: int, config_price: float) -> bool:
        """
        Validate price matches.

        Note: Polar returns prices in cents (int), while config uses dollars (float)
        """
        polar_price_dollars = polar_price / 100
        return abs(polar_price_dollars - config_price) < 0.01  # Allow 1 cent rounding

    def validate_product(self, product_id: str, config: Dict[str, Any]) -> ValidationResult:
        """Validate a single product against Polar API"""
        result = ValidationResult(
            product_id=product_id,
            is_valid=True,
            errors=[],
            config_data=config
        )

        try:
            # Fetch product from Polar
            polar_product = self.get_product(product_id)
            result.polar_data = polar_product

            # Check if product is archived
            if polar_product.get('is_archived', False):
                result.is_valid = False
                result.errors.append("Product is archived in Polar")

            # Validate price
            expected_price = int(config['price'] * 100)  # Convert to cents
            actual_price = polar_product.get('price_amount')

            if actual_price is None:
                result.is_valid = False
                result.errors.append("Product has no price in Polar")
            elif not self.validate_price(actual_price, config['price']):
                result.is_valid = False
                result.errors.append(
                    f"Price mismatch: expected ${config['price']:.2f}, "
                    f"got ${actual_price/100:.2f}"
                )

            # Validate currency
            currency = polar_product.get('price_currency', 'USD').upper()
            if currency != 'USD':
                result.is_valid = False
                result.errors.append(f"Invalid currency: {currency} (expected USD)")

            # Check product status
            status = polar_product.get('status', 'active').lower()
            if status not in ['active', 'draft']:  # Draft is acceptable for testing
                result.is_valid = False
                result.errors.append(f"Invalid product status: {status}")

            # Verify product type matches
            product_name = polar_product.get('name', '')
            config_display = config.get('display_name', '')

            # Basic sanity check - names should be similar
            if not self._names_are_similar(product_name, config_display):
                result.is_valid = False
                result.errors.append(
                    f"Product name mismatch: Polar='{product_name}', Config='{config_display}'"
                )

        except PolarAPIError as e:
            result.is_valid = False
            result.errors.append(str(e))

        return result

    def _names_are_similar(self, polar_name: str, config_name: str) -> bool:
        """Check if product names are reasonably similar"""
        # Extract key terms: credits amount, pass duration
        polar_lower = polar_name.lower()
        config_lower = config_name.lower()

        # Check for common terms
        credit_terms = ['100 credits', '500 credits', '2000 credits']
        pass_terms = ['1-day', '7-day', '30-day', '1 day', '7 days', '30 days']

        for term in credit_terms + pass_terms:
            if term in polar_lower and term in config_lower:
                return True

        # Fallback: check if main numeric identifier matches
        import re
        polar_nums = re.findall(r'\d+', polar_name)
        config_nums = re.findall(r'\d+', config_name)

        if polar_nums and config_nums:
            return polar_nums[0] == config_nums[0]

        return False


def print_validation_results(results: List[ValidationResult]) -> None:
    """Print formatted validation results"""
    print("\n" + "="*80)
    print("🔍 POLAR PRODUCT VALIDATION RESULTS")
    print("="*80)

    all_valid = True

    for result in results:
        status_icon = "✅" if result.is_valid else "❌"
        display_name = result.config_data.get('display_name', 'Unknown') if result.config_data else 'Unknown'

        print(f"\n{status_icon} {result.product_id}")
        print(f"   Display: {display_name}")

        if result.is_valid:
            price = result.config_data.get('price', 0)
            print(f"   Status: Valid (${price:.2f})")
        else:
            print(f"   Status: INVALID")
            print(f"   Errors:")
            for error in result.errors:
                print(f"     • {error}")

    print("\n" + "="*80)

    # Summary
    total = len(results)
    valid = sum(1 for r in results if r.is_valid)
    invalid = total - valid

    if invalid == 0:
        print(f"✅ SUCCESS: All {total} products are valid!")
    else:
        print(f"❌ FAILURE: {invalid} of {total} products have errors")
        all_valid = False

    print("="*80)

    return all_valid


def main():
    """Main validation function"""
    print("🚀 Starting Polar product validation...")
    print(f"   Time: {datetime.now().isoformat()}")

    # Check environment
    token = os.getenv('POLAR_ACCESS_TOKEN')
    if not token:
        print("❌ Error: POLAR_ACCESS_TOKEN environment variable not set")
        print("\nGet your token from: https://polar.sh/settings/api-keys")
        print("Then run: export POLAR_ACCESS_TOKEN='your_token_here'")
        sys.exit(2)

    # Check product config
    if not PRODUCT_CONFIG:
        print("❌ Error: PRODUCT_CONFIG is empty")
        sys.exit(2)

    print(f"\n📊 Found {len(PRODUCT_CONFIG)} products to validate")

    # Initialize validator
    validator = PolarProductValidator(token)
    results = []

    # Validate each product
    for product_id, config in PRODUCT_CONFIG.items():
        print(f"\n🔍 Validating: {config.get('display_name', product_id)}")
        result = validator.validate_product(product_id, config)
        results.append(result)

    # Print results
    all_valid = print_validation_results(results)

    # Exit with appropriate code
    if all_valid:
        print("\n🎉 All products validated successfully!")
        sys.exit(0)
    else:
        print("\n💥 Validation failed! Fix errors before deploying.")
        sys.exit(1)


if __name__ == "__main__":
    main()