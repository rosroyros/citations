# backend/pricing_config.py

"""
Pricing configuration for A/B test.

This file maps Polar product IDs to internal product types and pricing tiers.
When Polar webhooks arrive, we look up the product_id here to determine
what access to grant (credits vs. pass).

IMPORTANT: Product IDs below are PLACEHOLDERS. In Phase 4, these will be
replaced with real Polar product IDs from user.

Oracle Feedback #3: Use Unix timestamps (not date strings) to avoid timezone issues.
"""

# Variant mapping - obfuscated IDs for localStorage
# '1' = credits variant, '2' = passes variant
EXPERIMENT_VARIANTS = {
    '1': 'credits',  # Variant 1: Pay-per-citation model
    '2': 'passes'    # Variant 2: Time-based unlimited access
}

# Product configuration
# Maps Polar product_id -> internal product details
PRODUCT_CONFIG = {
    # Variant 1: Credits (pay-per-citation)
    # User pays per citation, credits never expire
    'prod_credits_100': {
        'variant': '1',
        'type': 'credits',
        'amount': 100,
        'price': 1.99,
        'display_name': '100 Credits ($1.99)'
    },
    'prod_credits_500': {
        'variant': '1',
        'type': 'credits',
        'amount': 500,
        'price': 4.99,
        'display_name': '500 Credits ($4.99)'
    },
    'prod_credits_2000': {
        'variant': '1',
        'type': 'credits',
        'amount': 2000,
        'price': 9.99,
        'display_name': '2000 Credits ($9.99)'
    },

    # Variant 2: Time-based passes
    # User gets unlimited access (1000 citations/day) for duration
    'prod_pass_1day': {
        'variant': '2',
        'type': 'pass',
        'days': 1,
        'price': 1.99,
        'daily_limit': 1000,
        'display_name': '1-Day Pass ($1.99)'
    },
    'prod_pass_7day': {
        'variant': '2',
        'type': 'pass',
        'days': 7,
        'price': 4.99,
        'daily_limit': 1000,
        'display_name': '7-Day Pass ($4.99)'
    },
    'prod_pass_30day': {
        'variant': '2',
        'type': 'pass',
        'days': 30,
        'price': 9.99,
        'daily_limit': 1000,
        'display_name': '30-Day Pass ($9.99)'
    }
}

def get_next_utc_midnight() -> int:
    """
    Returns Unix timestamp of next UTC midnight.
    Used for daily_usage table reset_timestamp.

    Oracle Feedback #3: Use Unix timestamps (not date strings) to avoid
    timezone confusion. This function is timezone-agnostic.

    Example: If now is 2025-12-10 14:30 UTC, returns timestamp for 2025-12-11 00:00 UTC

    Returns:
        int: Unix timestamp (seconds since epoch) of next UTC midnight
    """
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return int(tomorrow.timestamp())

def get_hours_until_reset() -> int:
    """
    Returns hours until next UTC midnight (for UI display).

    Example: If now is 2025-12-10 20:00 UTC, returns 4 (hours until midnight)

    Returns:
        int: Hours until next UTC midnight (rounded down)
    """
    import time
    now = int(time.time())
    next_reset = get_next_utc_midnight()
    return (next_reset - now) // 3600
