# Pricing Model A/B Test - Complete Implementation Plan

**Date:** 2025-12-10
**Status:** Design Complete - Oracle Reviewed - Ready for Implementation
**Oracle Review:** Incorporated all critical feedback and simplifications

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Business Context & Goals](#business-context--goals)
3. [System Architecture](#system-architecture)
4. [Database Design](#database-design)
5. [API Changes](#api-changes)
6. [Frontend Components](#frontend-components)
7. [Implementation Phases](#implementation-phases)
8. [Testing Strategy](#testing-strategy)
9. [Deployment & Rollback](#deployment--rollback)
10. [Oracle Feedback Integration](#oracle-feedback-integration)

---

## Executive Summary

### What We're Building
Replace single $8.99/1000-credits pricing with A/B test of two models:
- **Variant 1 (Credits):** Pay-per-citation in 3 tiers (100/$1.99, 500/$4.99, 2000/$9.99)
- **Variant 2 (Passes):** Time-based access in 3 tiers (1-day/$1.99, 7-day/$4.99, 30-day/$9.99)

### Why We're Doing This
**Goal:** Optimize for conversion rate (% of users who purchase)
**Hypothesis:** Lower price points + multiple tiers will increase conversion vs. single $8.99 option
**Key Metric:** Conversions by variant (tracked via upgrade funnel in dashboard)

### Success Criteria
- Both variants fully functional in production
- A/B test tracking shows which variant users saw
- Can measure conversion rate by variant in dashboard
- Pass system enforces 1000 citations/day limit
- Existing $8.99 users unaffected during rollout

### Implementation Timeline
6 phases over ~2-3 weeks:
1. Database foundation (1 day)
2. Frontend components (2 days)
3. Tracking infrastructure (1 day)
4. Multi-product checkout (2 days)
5. Access control & messaging (2 days)
6. UI polish (1 day)

---

## Business Context & Goals

### Current State
- **Pricing:** Single option: $8.99 for 1000 credits
- **Conversion Rate:** Unknown (no A/B testing infrastructure)
- **User Feedback:** Some users want cheaper options for occasional use
- **Revenue Model:** One-time purchases (no subscriptions)

### Strategic Intent
1. **Lower barriers to entry:** $1.99 entry point vs. $8.99
2. **Price discrimination:** Heavy users pay more ($9.99 for 2000 credits or 30-day pass)
3. **Data-driven pricing:** A/B test to find optimal model
4. **Future flexibility:** Infrastructure supports adding more tiers/models

### Key Assumptions
- Users in Variant 1 (Credits) value predictability (know exactly how many citations they get)
- Users in Variant 2 (Passes) value unlimited access within time window
- 1000 citations/day limit on passes prevents abuse while feeling "unlimited" to most users
- Credits and passes serve different user personas (occasional vs. power users)

### Out of Scope
- Subscription/recurring billing (future enhancement)
- Team/institutional pricing (future enhancement)
- Dynamic pricing based on usage (future enhancement)
- Refunds/cancellations (handled via Polar support)

---

## System Architecture

### High-Level Flow

```
User → Validation → Hits Limit → Upgrade Modal → Pricing Table (Variant) → Checkout → Webhook → Grant Access
```

**Detailed Flow:**

1. **User validates citations** → `POST /api/validate/async`
   - Backend checks access (pass → credits → free tier)
   - Returns results or partial results with `limit_type`

2. **User clicks "Upgrade"** → Frontend determines variant
   - Check localStorage for `experiment_v1`
   - If not set: randomly assign '1' or '2', store in localStorage
   - Open UpgradeModal with appropriate pricing table

3. **User selects product** → `POST /api/create-checkout`
   - Frontend sends: `{token, product_id, experiment_variant}`
   - Backend validates product_id, creates Polar checkout
   - Returns checkout URL
   - Logs: `UPGRADE_WORKFLOW | event=checkout_created | experiment_variant=X | product_id=Y`

4. **User completes purchase** → Polar webhook → `POST /api/polar-webhook`
   - Backend extracts product_id from webhook
   - Looks up in PRODUCT_CONFIG
   - Routes to `add_credits()` or `add_pass()` based on type
   - Logs grant with revenue data

5. **User returns to site** → Access granted
   - If credits: Deduct per citation as before
   - If pass: Check expiration + daily limit, then allow

### Data Flow Diagram

```
┌─────────────────┐
│   localStorage  │  experiment_v1 = '1' or '2'
│   (Frontend)    │  (Sticky variant assignment)
└────────┬────────┘
         │
         ├─────► UpgradeModal → PricingTableCredits (variant 1)
         └─────► UpgradeModal → PricingTablePasses  (variant 2)
                        │
                        v
                 /api/create-checkout {product_id, experiment_variant}
                        │
                        v
                 Polar Checkout
                        │
                        v
                 /api/polar-webhook {product_id, order_id, amount}
                        │
                 ┌──────┴──────┐
                 v             v
           add_credits()   add_pass()
                 │             │
                 v             v
           credits.db    user_passes.db
```

### Component Responsibilities

**Frontend:**
- Variant assignment (random, sticky)
- Pricing table display based on variant
- Passing variant through upgrade funnel
- Limit messaging UI

**Backend:**
- Product validation
- Access control (pass → credits → free)
- Webhook processing (idempotent grants)
- Logging for analytics

**Database:**
- Credits tracking (existing)
- Pass expiration (new)
- Daily usage limits (new)
- Experiment tracking (new columns)

**Dashboard:**
- Parse logs for experiment data
- Display variant and product in table
- Enable conversion analysis

---

## Database Design

### Schema Changes

```sql
-- New table: Time-based pass access
CREATE TABLE user_passes (
    token TEXT PRIMARY KEY,
    expiration_timestamp INTEGER NOT NULL,  -- Unix timestamp
    pass_type TEXT NOT NULL,                -- '1day', '7day', '30day'
    purchase_date INTEGER NOT NULL,
    order_id TEXT UNIQUE NOT NULL           -- For idempotency
);

-- New table: Daily rate limiting for pass users
CREATE TABLE daily_usage (
    token TEXT NOT NULL,
    reset_timestamp INTEGER NOT NULL,      -- Unix timestamp of next UTC midnight
    citations_count INTEGER DEFAULT 0,
    PRIMARY KEY (token, reset_timestamp)
);

-- Tracking columns for A/B test
ALTER TABLE validations ADD COLUMN experiment_variant TEXT;
ALTER TABLE validations ADD COLUMN product_id TEXT;
```

### Design Decisions & Rationale

**Why Unix timestamps instead of dates?**
- Oracle feedback: Date strings cause timezone confusion
- Users see "Resets at midnight UTC (in X hours)" but storing '2025-12-10' doesn't capture when midnight is
- Solution: Store `reset_timestamp` = Unix timestamp of next UTC midnight
- Easier to calculate "hours until reset" for UI
- No ambiguity about timezone

**Why token as PRIMARY KEY on user_passes?**
- One active pass per user
- When user buys new pass, UPDATE existing row (extends or replaces)
- Simple query: `SELECT * FROM user_passes WHERE token=? AND expiration_timestamp > now()`

**Why reset_timestamp in daily_usage instead of date?**
- Each row represents a 24-hour window from midnight UTC to midnight UTC
- Query: `SELECT citations_count WHERE token=? AND reset_timestamp > now()`
- Automatically "expires" old records (reset_timestamp in past)
- No need for daily cleanup job

**Why experiment_variant on validations table?**
- Enables analysis: "How many validations did each variant users perform before converting?"
- Nullable column (backward compatible)
- Populated from upgrade funnel logs during parsing

### Access Control Algorithm

```python
def check_user_access(token: str, citation_count: int) -> dict:
    """
    Check user access in priority order: pass > credits > free tier

    Returns:
    {
        'allowed': int,           # How many citations can be processed (0 to citation_count)
        'limit_type': str,        # 'none', 'daily_limit', 'credits_exhausted', 'pass_expired', 'free_limit'
        'credits_remaining': int, # For UI display
        'pass_info': dict,        # {expiration_timestamp, pass_type} if active pass
        'daily_remaining': int    # Citations left in today's window (if pass user)
    }
    """

    # 1. Check for active pass
    pass_info = get_active_pass(token)
    if pass_info:
        # Has active pass - check daily limit
        daily_used = get_daily_usage_for_current_window(token)
        daily_remaining = 1000 - daily_used

        if daily_remaining >= citation_count:
            # Can process all
            return {
                'allowed': citation_count,
                'limit_type': 'none',
                'pass_info': pass_info,
                'daily_remaining': daily_remaining - citation_count
            }
        elif daily_remaining > 0:
            # Can process partial - BUT we reject all per Oracle feedback #2
            # Message: "You have X citations left today. Please reduce your request."
            return {
                'allowed': 0,  # Reject entire request
                'limit_type': 'daily_limit_insufficient',
                'pass_info': pass_info,
                'daily_remaining': daily_remaining,
                'requested': citation_count
            }
        else:
            # Daily limit exhausted
            return {
                'allowed': 0,
                'limit_type': 'daily_limit',
                'pass_info': pass_info,
                'daily_remaining': 0
            }

    # 2. Check for credits
    credits = get_credits(token)
    if credits > 0:
        if credits >= citation_count:
            return {
                'allowed': citation_count,
                'limit_type': 'none',
                'credits_remaining': credits
            }
        else:
            # Partial results (existing behavior)
            return {
                'allowed': credits,
                'limit_type': 'credits_exhausted',
                'credits_remaining': 0
            }

    # 3. Free tier
    free_used = get_free_usage(token)
    if free_used < 5:
        allowed = min(citation_count, 5 - free_used)
        return {
            'allowed': allowed,
            'limit_type': 'free_limit' if allowed < citation_count else 'none',
            'free_remaining': 5 - free_used - allowed
        }

    # 4. No access
    return {
        'allowed': 0,
        'limit_type': 'free_limit',
        'free_remaining': 0
    }
```

**Key Principles:**
1. **Pass users take priority** - If they have active pass, don't check credits
2. **Daily limit rejection** - If request exceeds remaining daily limit, reject entire request (not partial)
3. **Credits as fallback** - Only checked if no active pass
4. **Oracle feedback #14:** Credits don't "kick in" when pass hits daily limit - user is blocked until reset

---

## API Changes

### New Configuration File

```python
# backend/pricing_config.py

"""
Pricing configuration for A/B test.

This file maps Polar product IDs to internal product types and pricing tiers.
When Polar webhooks arrive, we look up the product_id here to determine
what access to grant (credits vs. pass).

IMPORTANT: Before Phase 4 deployment, replace placeholder IDs with real Polar product IDs.
Run validation script: python3 backend/validate_polar_products.py
"""

EXPERIMENT_VARIANTS = {
    '1': 'credits',  # Variant 1: Pay-per-citation model
    '2': 'passes'    # Variant 2: Time-based unlimited access
}

PRODUCT_CONFIG = {
    # Variant 1: Credits
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

    Example: If now is 2025-12-10 14:30 UTC, returns timestamp for 2025-12-11 00:00 UTC
    """
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    return int(tomorrow.timestamp())

def get_hours_until_reset() -> int:
    """
    Returns hours until next UTC midnight (for UI display).

    Example: If now is 2025-12-10 20:00 UTC, returns 4 (hours until midnight)
    """
    import time
    now = int(time.time())
    next_reset = get_next_utc_midnight()
    return (next_reset - now) // 3600
```

### Updated Database Functions

```python
# backend/database.py

# CRITICAL: Oracle Feedback #1 - Atomic daily usage increment
def try_increment_daily_usage(token: str, citation_count: int) -> dict:
    """
    Atomically check and increment daily usage.

    Returns:
    {
        'success': bool,          # False if would exceed 1000 limit
        'used_before': int,       # Usage before this increment
        'used_after': int,        # Usage after (if success)
        'remaining': int,         # Citations left in window
        'reset_timestamp': int    # When limit resets (Unix timestamp)
    }

    IMPORTANT: Uses BEGIN IMMEDIATE to prevent race conditions.
    Without this, concurrent requests could exceed 1000/day limit.

    Example race condition (without atomic check):
    - Request A reads: 950 citations used
    - Request B reads: 950 citations used
    - Request A writes: 950 + 60 = 1010
    - Request B writes: 950 + 50 = 1000
    - Result: 1010 citations used (over limit!)

    Oracle Feedback: https://docs/plans/oracle-feedback.md#issue-1
    """
    from pricing_config import get_next_utc_midnight

    conn = sqlite3.connect(DB_PATH + '?mode=rwc&_journal_mode=WAL&_busy_timeout=5000')
    cursor = conn.cursor()

    reset_timestamp = get_next_utc_midnight()

    try:
        # CRITICAL: BEGIN IMMEDIATE acquires write lock immediately
        # Prevents race between read and write
        cursor.execute("BEGIN IMMEDIATE")

        # Get current usage for this window
        cursor.execute("""
            SELECT citations_count FROM daily_usage
            WHERE token = ? AND reset_timestamp = ?
        """, (token, reset_timestamp))

        row = cursor.fetchone()
        current_usage = row[0] if row else 0

        # Check if increment would exceed limit
        if current_usage + citation_count > 1000:
            conn.rollback()
            conn.close()
            return {
                'success': False,
                'used_before': current_usage,
                'remaining': 1000 - current_usage,
                'reset_timestamp': reset_timestamp
            }

        # Safe to increment
        new_usage = current_usage + citation_count
        cursor.execute("""
            INSERT INTO daily_usage (token, reset_timestamp, citations_count)
            VALUES (?, ?, ?)
            ON CONFLICT(token, reset_timestamp) DO UPDATE SET
            citations_count = citations_count + ?
        """, (token, reset_timestamp, citation_count, citation_count))

        conn.commit()
        conn.close()

        return {
            'success': True,
            'used_before': current_usage,
            'used_after': new_usage,
            'remaining': 1000 - new_usage,
            'reset_timestamp': reset_timestamp
        }

    except Exception as e:
        conn.rollback()
        conn.close()
        raise

# CRITICAL: Oracle Feedback #6 - Webhook idempotency
def add_pass(token: str, days: int, pass_type: str, order_id: str) -> bool:
    """
    Grant time-based pass to user (idempotent).

    Pass Extension Logic (Oracle Feedback #15):
    - If user has active pass (any type), extend expiration by adding days
    - Example: 3 days left on 7-day pass + buy 30-day pass = 33 days total
    - Rationale: User shouldn't lose remaining time when upgrading/extending

    Idempotency (Oracle Feedback #6):
    - Uses BEGIN IMMEDIATE to prevent race conditions
    - Checks order_id before processing
    - Catches IntegrityError if another thread processed concurrently

    Args:
        token: User identifier
        days: Duration to add (1, 7, or 30)
        pass_type: Display name ('1day', '7day', '30day')
        order_id: Polar order ID (for idempotency)

    Returns:
        True if pass granted (or already processed)
    """
    import time

    conn = sqlite3.connect(DB_PATH + '?mode=rwc&_journal_mode=WAL&_busy_timeout=5000')
    cursor = conn.cursor()

    try:
        # CRITICAL: Lock early to prevent race conditions
        cursor.execute("BEGIN IMMEDIATE")

        # Idempotency check - has this order been processed?
        cursor.execute("SELECT 1 FROM user_passes WHERE order_id = ?", (order_id,))
        if cursor.fetchone():
            conn.rollback()
            conn.close()
            logger.info(f"Order {order_id} already processed (idempotent)")
            return True

        # Check for existing active pass
        now = int(time.time())
        cursor.execute("""
            SELECT expiration_timestamp, pass_type
            FROM user_passes
            WHERE token = ? AND expiration_timestamp > ?
        """, (token, now))

        existing = cursor.fetchone()

        if existing:
            # Extend existing pass (add days to current expiration)
            # Oracle Feedback #15: Always extend, regardless of pass type
            current_expiration = existing[0]
            new_expiration = current_expiration + (days * 86400)
            logger.info(f"Extending pass for {token}: {existing[1]} -> {pass_type} (+{days} days)")
        else:
            # New pass (starts now)
            new_expiration = now + (days * 86400)
            logger.info(f"Granting new {pass_type} pass to {token}")

        # Insert or replace
        cursor.execute("""
            INSERT OR REPLACE INTO user_passes
            (token, expiration_timestamp, pass_type, purchase_date, order_id)
            VALUES (?, ?, ?, ?, ?)
        """, (token, new_expiration, pass_type, now, order_id))

        conn.commit()
        conn.close()
        return True

    except sqlite3.IntegrityError as e:
        # Race condition - another thread processed this order
        conn.rollback()
        conn.close()
        logger.warning(f"IntegrityError for order {order_id}: {e}")
        return True  # Treat as success (idempotent)

    except Exception as e:
        conn.rollback()
        conn.close()
        logger.error(f"Failed to add pass: {e}")
        raise

def get_active_pass(token: str) -> Optional[dict]:
    """
    Check if user has active pass.

    Returns:
    {
        'expiration_timestamp': int,  # Unix timestamp
        'pass_type': str,             # '1day', '7day', '30day'
        'purchase_date': int,
        'hours_remaining': int        # For UI display
    }
    Or None if no active pass.
    """
    import time

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = int(time.time())
    cursor.execute("""
        SELECT expiration_timestamp, pass_type, purchase_date
        FROM user_passes
        WHERE token = ? AND expiration_timestamp > ?
    """, (token, now))

    row = cursor.fetchone()
    conn.close()

    if row:
        hours_remaining = (row[0] - now) // 3600
        return {
            'expiration_timestamp': row[0],
            'pass_type': row[1],
            'purchase_date': row[2],
            'hours_remaining': hours_remaining
        }
    return None

def get_daily_usage_for_current_window(token: str) -> int:
    """
    Get citation count for current UTC day window.

    Returns citations used in current window (0 if new window or no usage).
    """
    from pricing_config import get_next_utc_midnight

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    reset_timestamp = get_next_utc_midnight()
    cursor.execute("""
        SELECT citations_count FROM daily_usage
        WHERE token = ? AND reset_timestamp = ?
    """, (token, reset_timestamp))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else 0
```

### Updated Endpoints

#### POST /api/validate/async

```python
@app.post("/api/validate/async")
async def validate_citations_async(http_request: Request, request: ValidationRequest, background_tasks: BackgroundTasks):
    """
    Create async validation job.

    Changes for A/B test:
    - Access control now checks: pass > credits > free tier
    - Returns limit_type for contextual messaging
    - Integrates with daily_usage tracking for pass users
    """

    # ... existing code for token, job creation, etc. ...

    # NEW: Check access before processing
    access = check_user_access(token, citation_count)

    if access['allowed'] == 0:
        # User has no access - return immediately with limit info
        # (Existing gating logic handles this)
        pass

    elif access['allowed'] < citation_count and access['limit_type'] == 'daily_limit_insufficient':
        # Oracle Feedback #2: Pass user requested more than daily limit allows
        # Reject entire request with helpful message
        return {
            "error": "daily_limit_insufficient",
            "message": f"You have {access['daily_remaining']} citations remaining today. Please reduce your request to {access['daily_remaining']} citations or less.",
            "daily_remaining": access['daily_remaining'],
            "requested": citation_count,
            "reset_in_hours": get_hours_until_reset()
        }

    # ... proceed with validation for access['allowed'] citations ...

    # If pass user, increment daily usage AFTER validation completes
    # (Do this in background task to avoid blocking response)
```

#### POST /api/create-checkout

```python
@app.post("/api/create-checkout")
def create_checkout(request: dict):
    """
    Create Polar checkout session.

    Changes for A/B test:
    - Accept product_id parameter (dynamic, not hardcoded env var)
    - Accept experiment_variant for tracking
    - Validate product_id exists in PRODUCT_CONFIG

    Oracle Feedback #11: Backward compatible - if product_id not provided,
    use env var POLAR_PRODUCT_ID (for existing $8.99 users).
    """
    from pricing_config import PRODUCT_CONFIG

    token = request.get('token')
    product_id = request.get('product_id')  # NEW
    experiment_variant = request.get('experiment_variant')  # NEW

    # Backward compatibility: Fall back to env var if no product_id
    if not product_id:
        product_id = os.getenv('POLAR_PRODUCT_ID')
        experiment_variant = 'not_assigned'  # Explicit marker for old flow
        logger.info(f"Checkout using legacy product_id from env var")

    # Validate product exists
    if product_id not in PRODUCT_CONFIG:
        logger.error(f"Invalid product_id: {product_id}")
        raise HTTPException(status_code=400, detail="Invalid product_id")

    # Generate token if needed
    if not token:
        token = str(uuid.uuid4())

    # Create Polar checkout
    polar = Polar(access_token=os.getenv('POLAR_ACCESS_TOKEN'))
    checkout_request = {
        "products": [product_id],
        "customer_email": None,
        "customer_metadata": {"token": token},
        "success_url": f"{BASE_URL}/success?token={token}&product_id={product_id}",  # Oracle #23: Include product_id
    }

    try:
        checkout = polar.checkouts.create(checkout_request)
    except Exception as e:
        logger.error(f"Polar checkout creation failed: {e}")
        raise HTTPException(status_code=500, detail="Checkout creation failed")

    # Log for analytics (Oracle Feedback #5: Keep variant on checkout_created for funnel analysis)
    logger.info(
        f"UPGRADE_WORKFLOW | event=checkout_created | "
        f"product_id={product_id} | experiment_variant={experiment_variant} | "
        f"token={token}"
    )

    return {"checkout_url": checkout.url, "token": token}
```

#### POST /api/polar-webhook

```python
async def handle_checkout_updated(webhook):
    """
    Process successful purchase from Polar webhook.

    Changes for A/B test:
    - Extract product_id from line items
    - Route to add_credits() or add_pass() based on PRODUCT_CONFIG
    - Log revenue data for dashboard (Oracle Feedback #16)

    Oracle Feedback #6: Idempotency handled in add_credits() and add_pass()
    """
    from pricing_config import PRODUCT_CONFIG

    if webhook.get('status') != 'completed':
        return

    # Extract metadata
    customer_metadata = webhook.get('customer_metadata', {})
    token = customer_metadata.get('token')

    if not token:
        logger.error("No token in webhook customer_metadata")
        return

    # Extract product info
    line_items = webhook.get('line_items', [])
    if not line_items:
        logger.error("No line items in webhook")
        return

    product_id = line_items[0].get('product_id')
    order_id = webhook.get('order_id')
    amount_cents = line_items[0].get('amount', 0)  # Oracle Feedback #16: Capture revenue

    # Look up product configuration
    product_config = PRODUCT_CONFIG.get(product_id)

    if not product_config:
        logger.error(f"Unknown product_id in webhook: {product_id}")
        return

    # Route based on product type
    if product_config['type'] == 'credits':
        amount = product_config['amount']
        success = add_credits(token, amount, order_id)
        logger.info(
            f"PURCHASE_COMPLETED | type=credits | product_id={product_id} | "
            f"amount={amount} | revenue=${amount_cents/100:.2f} | token={token} | order_id={order_id}"
        )

    elif product_config['type'] == 'pass':
        days = product_config['days']
        pass_type = product_config['pass_type']
        success = add_pass(token, days, pass_type, order_id)
        logger.info(
            f"PURCHASE_COMPLETED | type=pass | product_id={product_id} | "
            f"days={days} | revenue=${amount_cents/100:.2f} | token={token} | order_id={order_id}"
        )

    else:
        logger.error(f"Unknown product type: {product_config['type']}")
        return

    if not success:
        logger.error(f"Failed to grant access for order {order_id}")
```

#### POST /api/upgrade-event

```python
@app.post("/api/upgrade-event")
def upgrade_event(request: dict):
    """
    Track upgrade funnel events.

    Changes for A/B test:
    - Accept experiment_variant parameter
    - Log variant with all funnel events

    Oracle Feedback #5: Need variant on all events to measure
    "how many users saw each pricing table" for conversion analysis.
    """
    event = request.get('event')
    job_id = request.get('job_id')
    experiment_variant = request.get('experiment_variant', 'not_assigned')

    logger.info(
        f"UPGRADE_WORKFLOW | job_id={job_id} | event={event} | "
        f"experiment_variant={experiment_variant}"
    )

    return {"status": "ok"}
```

#### GET /api/validate Response Changes

```python
# Oracle Feedback #8: Don't create separate /api/user-status endpoint
# Instead, add user_status to existing validation response

# In validation response:
{
    "results": [...],
    "partial": false,
    "limit_type": "none" | "daily_limit" | "credits_exhausted" | "pass_expired" | "free_limit",

    # NEW: User status for UI display (Oracle #8)
    "user_status": {
        "type": "pass" | "credits" | "free",

        # If type=pass:
        "pass_type": "7day",
        "expiration_timestamp": 1704153600,
        "hours_remaining": 48,
        "daily_remaining": 850,  # Citations left today

        # If type=credits:
        "credits_remaining": 500,

        # If type=free:
        "free_remaining": 3
    }
}
```

---

## Frontend Components

### shadcn/ui Setup

```bash
cd frontend/frontend

# 1. Install Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 2. Configure Tailwind
# Edit tailwind.config.js:
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      // Will be populated with brand colors in Phase 2
    },
  },
  plugins: [],
}

# 3. Add Tailwind directives to src/index.css
@tailwind base;
@tailwind components;
@tailwind utilities;

# 4. Initialize shadcn/ui
npx shadcn@latest init
# Prompts:
# - Framework: React
# - Style: Default
# - Base color: Neutral (good for academic/professional tools)
# - CSS variables: Yes

# 5. Add required components
npx shadcn@latest add card button
```

### Component Structure

```
src/
  components/
    ui/                          (shadcn components)
      card.jsx
      button.jsx

    UpgradeModal.jsx             (updated - orchestrates pricing display)
    PricingTableCredits.jsx      (new - variant 1)
    PricingTablePasses.jsx       (new - variant 2)
    PartialResults.jsx           (minor update - pass limit_type)
    CreditDisplay.jsx            (updated - show pass status)

  utils/
    experimentVariant.js         (new - variant assignment)
    passStatus.js                (new - time calculations)

  lib/
    utils.js                     (shadcn helper, auto-created)
```

### Experiment Variant Utility

```javascript
// src/utils/experimentVariant.js

/**
 * A/B Test Variant Assignment
 *
 * Purpose: Randomly assign users to pricing experiment variants (Credits vs Passes)
 * Storage: localStorage for sticky assignment across sessions
 *
 * Design Decision: Assign on first upgrade click, not on validation
 * Rationale: User must express purchase intent before seeing pricing
 *
 * Oracle Feedback #5: We track variant on all upgrade funnel events to measure:
 * - How many users saw Credits pricing table
 * - How many users saw Passes pricing table
 * - Conversion rate by variant
 */

export function getExperimentVariant() {
  let variantId = localStorage.getItem('experiment_v1');

  if (!variantId) {
    // First time - randomly assign
    variantId = Math.random() < 0.5 ? '1' : '2';
    localStorage.setItem('experiment_v1', variantId);

    // Log assignment for debugging
    console.log(`[A/B Test] Assigned variant: ${variantId === '1' ? 'Credits' : 'Passes'}`);
  }

  return variantId;
}

/**
 * Get human-readable variant name for UI/debugging
 */
export function getVariantName(variantId) {
  const names = {
    '1': 'Credits',
    '2': 'Passes'
  };
  return names[variantId] || 'Unknown';
}

/**
 * Reset variant (for testing only - don't expose in production UI)
 */
export function resetExperimentVariant() {
  localStorage.removeItem('experiment_v1');
  console.log('[A/B Test] Variant reset');
}
```

### Pass Status Utility

```javascript
// src/utils/passStatus.js

/**
 * Pass Status Utilities
 *
 * Handles time calculations for pass display and messaging.
 *
 * Oracle Feedback #3: Use Unix timestamps, not date strings,
 * to avoid timezone confusion.
 */

/**
 * Format pass expiration for display
 *
 * Examples:
 * - "Expires in 2 days"
 * - "Expires in 8 hours"
 * - "Expires in 45 minutes"
 */
export function formatPassExpiration(expirationTimestamp) {
  const now = Math.floor(Date.now() / 1000);
  const secondsRemaining = expirationTimestamp - now;

  if (secondsRemaining <= 0) {
    return "Expired";
  }

  const hours = Math.floor(secondsRemaining / 3600);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `Expires in ${days} day${days > 1 ? 's' : ''}`;
  } else if (hours > 0) {
    return `Expires in ${hours} hour${hours > 1 ? 's' : ''}`;
  } else {
    const minutes = Math.floor(secondsRemaining / 60);
    return `Expires in ${minutes} minute${minutes > 1 ? 's' : ''}`;
  }
}

/**
 * Get hours until midnight UTC (for daily limit reset message)
 *
 * Oracle Feedback #3: Store reset_timestamp, calculate hours from that
 */
export function getHoursUntilReset(resetTimestamp) {
  const now = Math.floor(Date.now() / 1000);
  const secondsRemaining = resetTimestamp - now;
  return Math.ceil(secondsRemaining / 3600);
}

/**
 * Format daily limit message
 *
 * Example: "Daily limit reached. Resets at midnight UTC (in 4 hours)"
 */
export function formatDailyLimitMessage(resetTimestamp) {
  const hours = getHoursUntilReset(resetTimestamp);
  return `Daily limit of 1,000 citations reached. Resets at midnight UTC (in ${hours} hour${hours > 1 ? 's' : ''}).`;
}
```

### Pricing Table Components

```jsx
// src/components/PricingTableCredits.jsx

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

/**
 * Pricing Table for Credits Variant (Variant 1)
 *
 * Design: Pay-per-citation model
 * Positioning:
 * - 100 credits: Entry tier for occasional users
 * - 500 credits: Recommended tier (best value per citation)
 * - 2000 credits: Power user tier
 *
 * A/B Test Hypothesis: Lower price point ($1.99) converts better than single $8.99 option
 */
export function PricingTableCredits({ onSelectProduct, experimentVariant }) {
  const products = [
    {
      id: 'prod_credits_100',  // Placeholder - replace with real Polar ID in Phase 4
      credits: 100,
      price: 1.99,
      pricePerCitation: 0.0199,
      recommended: false,
      benefits: [
        '100 citation validations',
        'APA / MLA / Chicago support',
        'Credits never expire',
        'Use anytime at your pace'
      ]
    },
    {
      id: 'prod_credits_500',
      credits: 500,
      price: 4.99,
      pricePerCitation: 0.00998,  // ~50% cheaper per citation
      recommended: true,
      benefits: [
        '500 citation validations',
        'Best value ($0.01/citation)',
        'APA / MLA / Chicago support',
        'Export to BibTeX / RIS'
      ]
    },
    {
      id: 'prod_credits_2000',
      credits: 2000,
      price: 9.99,
      pricePerCitation: 0.004995,  // ~75% cheaper per citation
      recommended: false,
      benefits: [
        '2,000 citation validations',
        'For heavy academic writing',
        'Lowest per-citation cost',
        'Priority support'
      ]
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto p-4">
      {products.map(product => (
        <Card
          key={product.id}
          className={product.recommended ? 'border-blue-600 border-2 shadow-lg relative' : 'relative'}
        >
          {product.recommended && (
            <div className="absolute top-0 right-0 bg-blue-600 text-white text-xs px-3 py-1 rounded-bl-lg rounded-tr-lg">
              Best Value
            </div>
          )}

          <CardHeader>
            <CardTitle className="text-2xl">{product.credits} Credits</CardTitle>
            <CardDescription className="text-sm text-gray-600">
              ${product.pricePerCitation.toFixed(3)} per citation
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="mb-6">
              <span className="text-4xl font-bold">${product.price}</span>
              <span className="text-gray-500 ml-2">one-time</span>
            </div>

            <ul className="space-y-3 text-sm">
              {product.benefits.map((benefit, idx) => (
                <li key={idx} className="flex items-start">
                  <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>{benefit}</span>
                </li>
              ))}
            </ul>
          </CardContent>

          <CardFooter>
            <Button
              onClick={() => onSelectProduct(product.id, experimentVariant)}
              className="w-full"
              variant={product.recommended ? "default" : "outline"}
            >
              Buy {product.credits} Credits
            </Button>
          </CardFooter>
        </Card>
      ))}
    </div>
  )
}
```

```jsx
// src/components/PricingTablePasses.jsx

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

/**
 * Pricing Table for Passes Variant (Variant 2)
 *
 * Design: Time-based unlimited access (with 1000/day fair use limit)
 * Positioning:
 * - 1-day pass: Quick validation needs (e.g., finishing a paper)
 * - 7-day pass: Recommended for most users (best $/day value)
 * - 30-day pass: Power users, ongoing research projects
 *
 * A/B Test Hypothesis: "Unlimited" messaging converts better than per-citation
 *
 * Oracle Feedback #14: Credits don't kick in when pass hits daily limit
 * (user is blocked until reset - this prevents confusion)
 */
export function PricingTablePasses({ onSelectProduct, experimentVariant }) {
  const products = [
    {
      id: 'prod_pass_1day',  // Placeholder - replace with real Polar ID in Phase 4
      days: 1,
      price: 1.99,
      pricePerDay: 1.99,
      recommended: false,
      benefits: [
        'Unlimited validations for 24 hours',
        'Up to 1,000 citations per day',
        'APA / MLA / Chicago support',
        'Perfect for finishing a paper'
      ]
    },
    {
      id: 'prod_pass_7day',
      days: 7,
      price: 4.99,
      pricePerDay: 0.71,
      recommended: true,
      benefits: [
        '7 days of unlimited access',
        'Best value ($0.71/day)',
        'Up to 1,000 citations per day',
        'Export to BibTeX / RIS'
      ]
    },
    {
      id: 'prod_pass_30day',
      days: 30,
      price: 9.99,
      pricePerDay: 0.33,
      recommended: false,
      benefits: [
        '30 days of unlimited access',
        'Lowest daily cost ($0.33/day)',
        'Perfect for ongoing research',
        'Priority support'
      ]
    }
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto p-4">
      {products.map(product => (
        <Card
          key={product.id}
          className={product.recommended ? 'border-blue-600 border-2 shadow-lg relative' : 'relative'}
        >
          {product.recommended && (
            <div className="absolute top-0 right-0 bg-blue-600 text-white text-xs px-3 py-1 rounded-bl-lg rounded-tr-lg">
              Recommended
            </div>
          )}

          <CardHeader>
            <CardTitle className="text-2xl">{product.days}-Day Pass</CardTitle>
            <CardDescription className="text-sm text-gray-600">
              ${product.pricePerDay.toFixed(2)} per day
            </CardDescription>
          </CardHeader>

          <CardContent>
            <div className="mb-6">
              <span className="text-4xl font-bold">${product.price}</span>
              <span className="text-gray-500 ml-2">one-time</span>
            </div>

            <ul className="space-y-3 text-sm">
              {product.benefits.map((benefit, idx) => (
                <li key={idx} className="flex items-start">
                  <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <span>{benefit}</span>
                </li>
              ))}
            </ul>
          </CardContent>

          <CardFooter>
            <Button
              onClick={() => onSelectProduct(product.id, experimentVariant)}
              className="w-full"
              variant={product.recommended ? "default" : "outline"}
            >
              Buy {product.days}-Day Pass
            </Button>
          </CardFooter>
        </Card>
      ))}

      <div className="col-span-full text-center text-sm text-gray-500 mt-4">
        Fair use: 1,000 citations per day. Passes can be extended anytime.
      </div>
    </div>
  )
}
```

### Updated UpgradeModal

```jsx
// src/components/UpgradeModal.jsx (updated)

import React, { useState, useEffect } from 'react';
import { getExperimentVariant } from '../utils/experimentVariant';
import { formatDailyLimitMessage } from '../utils/passStatus';
import { trackEvent } from '../utils/analytics';
import { PricingTableCredits } from './PricingTableCredits';
import { PricingTablePasses } from './PricingTablePasses';
import './UpgradeModal.css';

/**
 * Upgrade Modal - Orchestrates pricing display based on limit type and variant
 *
 * Props:
 * - limitType: 'credits_exhausted' | 'pass_expired' | 'daily_limit' | 'daily_limit_insufficient' | 'free_limit'
 * - passInfo: {pass_type, expiration_timestamp} if user had pass that expired
 * - resetTimestamp: Unix timestamp of next reset (for daily limit messaging)
 * - dailyRemaining: Citations left in window (for insufficient message)
 * - requestedCitations: How many user tried to validate (for insufficient message)
 *
 * Oracle Feedback #2: Show helpful message for daily_limit_insufficient
 * Oracle Feedback #5: Track variant on clicked_upgrade for conversion analysis
 */
export const UpgradeModal = ({
  isOpen,
  onClose,
  limitType,
  passInfo,
  resetTimestamp,
  dailyRemaining,
  requestedCitations
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [variant, setVariant] = useState(null);

  useEffect(() => {
    if (isOpen) {
      // Determine variant when modal opens
      const variantId = getExperimentVariant();
      setVariant(variantId);

      // Track modal shown with variant (Oracle #5)
      trackEvent('upgrade_modal_shown', {
        experiment_variant: variantId,
        limit_type: limitType
      });
    }
  }, [isOpen, limitType]);

  const handleSelectProduct = async (productId, experimentVariant) => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('userToken');

      // Track product selection
      trackEvent('product_selected', {
        product_id: productId,
        experiment_variant: experimentVariant
      });

      // Create checkout
      const response = await fetch('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          product_id: productId,
          experiment_variant: experimentVariant
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const { checkout_url } = await response.json();

      if (!checkout_url) {
        throw new Error('No checkout URL received');
      }

      // Redirect to checkout
      window.location.href = checkout_url;

    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  };

  if (!isOpen || !variant) {
    return null;
  }

  // Render content based on limit type
  const renderContent = () => {
    // Oracle Feedback #2: Daily limit insufficient - show helpful message, no pricing
    if (limitType === 'daily_limit_insufficient') {
      return (
        <div className="upgrade-modal-content-centered">
          <h2 className="upgrade-modal-title">Request Too Large</h2>
          <p className="upgrade-modal-message">
            You have {dailyRemaining} citations remaining in your daily limit.
          </p>
          <p className="upgrade-modal-submessage">
            Please reduce your request to {dailyRemaining} citations or less,
            or wait until {formatDailyLimitMessage(resetTimestamp)}.
          </p>
          <button className="upgrade-modal-close-button" onClick={onClose}>
            Close
          </button>
        </div>
      );
    }

    // Daily limit hit - show reset message, no pricing
    if (limitType === 'daily_limit') {
      return (
        <div className="upgrade-modal-content-centered">
          <h2 className="upgrade-modal-title">Daily Limit Reached</h2>
          <p className="upgrade-modal-message">
            {formatDailyLimitMessage(resetTimestamp)}
          </p>
          <p className="upgrade-modal-submessage">
            Your pass will allow up to 1,000 citations again after reset.
          </p>
          <button className="upgrade-modal-close-button" onClick={onClose}>
            Close
          </button>
        </div>
      );
    }

    // Pass expired - show passes table (match what they had)
    if (limitType === 'pass_expired' && passInfo) {
      return (
        <div className="upgrade-modal-content-wide">
          <h2 className="upgrade-modal-title">Your Pass Has Expired</h2>
          <p className="upgrade-modal-message">
            Your {passInfo.pass_type} pass has expired. Renew to continue validating.
          </p>
          <PricingTablePasses
            onSelectProduct={handleSelectProduct}
            experimentVariant="2"  // Always show passes if they had a pass
          />
        </div>
      );
    }

    // Credits exhausted or free limit - show pricing based on variant
    return (
      <div className="upgrade-modal-content-wide">
        <h2 className="upgrade-modal-title">
          {limitType === 'credits_exhausted' ? 'Out of Credits' : 'Upgrade for More Access'}
        </h2>
        <p className="upgrade-modal-message">
          {limitType === 'credits_exhausted'
            ? "You've used all your credits. Purchase more to continue."
            : "Get unlimited citation validations with our affordable pricing."}
        </p>

        {variant === '1' ? (
          <PricingTableCredits
            onSelectProduct={handleSelectProduct}
            experimentVariant={variant}
          />
        ) : (
          <PricingTablePasses
            onSelectProduct={handleSelectProduct}
            experimentVariant={variant}
          />
        )}
      </div>
    );
  };

  return (
    <div className="upgrade-modal-overlay" onClick={onClose}>
      <div className="upgrade-modal-container" onClick={(e) => e.stopPropagation()}>
        <button className="upgrade-modal-close-x" onClick={onClose}>×</button>

        {error && (
          <div className="upgrade-modal-error">
            {error}
          </div>
        )}

        {renderContent()}
      </div>
    </div>
  );
};
```

### Updated CreditDisplay

```jsx
// src/components/CreditDisplay.jsx (updated)

import React, { useEffect, useState } from 'react';
import { formatPassExpiration } from '../utils/passStatus';

/**
 * Credit Display Component
 *
 * Oracle Feedback #8: Don't create separate /api/user-status endpoint.
 * Instead, get user_status from /api/validate response.
 *
 * Oracle Feedback #7: Show pass expiration details, not just "Active Pass"
 *
 * Displays:
 * - For pass users: "Pass expires in X days" or "Pass expires in X hours"
 * - For credit users: "X credits remaining"
 * - For free users: "X free validations left"
 */
export function CreditDisplay({ userStatus }) {
  if (!userStatus) {
    return null;
  }

  if (userStatus.type === 'pass') {
    return (
      <div className="credit-display">
        <div className="credit-count">
          {formatPassExpiration(userStatus.expiration_timestamp)}
        </div>
        <div className="credit-label">
          {userStatus.pass_type} • {userStatus.daily_remaining}/1000 today
        </div>
      </div>
    );
  }

  if (userStatus.type === 'credits') {
    return (
      <div className="credit-display">
        <div className="credit-count">{userStatus.credits_remaining}</div>
        <div className="credit-label">Credits Remaining</div>
      </div>
    );
  }

  if (userStatus.type === 'free') {
    return (
      <div className="credit-display">
        <div className="credit-count">{userStatus.free_remaining}/5</div>
        <div className="credit-label">Free Validations</div>
      </div>
    );
  }

  return null;
}
```

---

## Implementation Phases

### Phase 1: Database Foundation

**Goal:** Create database tables and functions, no user-facing changes

**Duration:** 1 day

**Critical Oracle Feedback Addressed:**
- #1: Atomic daily usage increment (race condition prevention)
- #6: Webhook idempotency (double-charge prevention)
- #3: Timezone handling (use Unix timestamps, not date strings)

**Steps:**

1. **Create pricing_config.py** (30 min)
   - Add PRODUCT_CONFIG with placeholder IDs
   - Add EXPERIMENT_VARIANTS mapping
   - Add get_next_utc_midnight() utility
   - Add get_hours_until_reset() utility

2. **Write migration script** (1 hour)
   ```python
   # backend/migrations/add_pricing_tables.py
   import sqlite3
   import sys
   from pathlib import Path

   DB_PATH = Path(__file__).parent.parent / 'credits.db'

   def migrate():
       conn = sqlite3.connect(DB_PATH)
       cursor = conn.cursor()

       try:
           # Create user_passes table
           cursor.execute("""
               CREATE TABLE IF NOT EXISTS user_passes (
                   token TEXT PRIMARY KEY,
                   expiration_timestamp INTEGER NOT NULL,
                   pass_type TEXT NOT NULL,
                   purchase_date INTEGER NOT NULL,
                   order_id TEXT UNIQUE NOT NULL
               )
           """)

           # Create daily_usage table
           cursor.execute("""
               CREATE TABLE IF NOT EXISTS daily_usage (
                   token TEXT NOT NULL,
                   reset_timestamp INTEGER NOT NULL,
                   citations_count INTEGER DEFAULT 0,
                   PRIMARY KEY (token, reset_timestamp)
               )
           """)

           # Add tracking columns to validations
           # Use ALTER TABLE ADD COLUMN (safe - nullable columns)
           try:
               cursor.execute("ALTER TABLE validations ADD COLUMN experiment_variant TEXT")
           except sqlite3.OperationalError:
               print("Column experiment_variant already exists")

           try:
               cursor.execute("ALTER TABLE validations ADD COLUMN product_id TEXT")
           except sqlite3.OperationalError:
               print("Column product_id already exists")

           conn.commit()
           print("✓ Migration complete")

       except Exception as e:
           conn.rollback()
           print(f"✗ Migration failed: {e}")
           sys.exit(1)
       finally:
           conn.close()

   if __name__ == '__main__':
       migrate()
   ```

3. **Add database functions to database.py** (2 hours)
   - `try_increment_daily_usage()` with BEGIN IMMEDIATE
   - `get_daily_usage_for_current_window()`
   - `add_pass()` with idempotency + extension logic
   - `get_active_pass()`
   - Update `add_credits()` with idempotency (if not already present)

4. **Write comprehensive unit tests** (3 hours)
   ```python
   # backend/tests/test_database_passes.py

   def test_pass_expiration_calculation_1day():
       # Given: Current time
       now = int(time.time())

       # When: Grant 1-day pass
       add_pass('user1', 1, '1day', 'order1')

       # Then: Expiration = now + 86400
       pass_info = get_active_pass('user1')
       assert pass_info['expiration_timestamp'] == now + 86400

   def test_pass_extension_same_type():
       # Given: User has 7-day pass with 3 days remaining
       now = int(time.time())
       expiration = now + (3 * 86400)
       # ... insert pass manually with this expiration ...

       # When: Buy another 7-day pass
       add_pass('user1', 7, '7day', 'order2')

       # Then: Expiration extended by 7 days (10 days total)
       pass_info = get_active_pass('user1')
       assert pass_info['expiration_timestamp'] == now + (10 * 86400)

   def test_pass_extension_different_type():
       # Given: User has 7-day pass with 3 days remaining
       # When: Buy 30-day pass
       # Then: Expiration extended by 30 days (33 days total)
       # Oracle Feedback #15: Always extend, regardless of type

   def test_webhook_idempotency():
       # Given: Order already processed
       add_pass('user1', 7, '7day', 'order1')
       initial_expiration = get_active_pass('user1')['expiration_timestamp']

       # When: Webhook delivered again (same order_id)
       add_pass('user1', 7, '7day', 'order1')

       # Then: Expiration unchanged (idempotent)
       pass_info = get_active_pass('user1')
       assert pass_info['expiration_timestamp'] == initial_expiration

   def test_daily_usage_atomic_increment():
       # Given: User has 950 citations used today
       # ... setup initial usage ...

       # When: Two concurrent requests for 60 citations each
       import threading
       results = []

       def request(citations):
           result = try_increment_daily_usage('user1', citations)
           results.append(result)

       t1 = threading.Thread(target=request, args=(60,))
       t2 = threading.Thread(target=request, args=(60,))

       t1.start()
       t2.start()
       t1.join()
       t2.join()

       # Then: One succeeds, one fails (not both)
       successes = [r for r in results if r['success']]
       failures = [r for r in results if not r['success']]
       assert len(successes) == 1
       assert len(failures) == 1

       # And: Total usage = 1010 (not 1070)
       final_usage = get_daily_usage_for_current_window('user1')
       assert final_usage == 1010

   def test_daily_usage_resets_next_window():
       # Given: User used 800 citations yesterday
       yesterday_reset = get_next_utc_midnight() - 86400
       # ... insert usage with yesterday's reset_timestamp ...

       # When: Check usage today
       current_usage = get_daily_usage_for_current_window('user1')

       # Then: Usage = 0 (new window)
       assert current_usage == 0

   @patch('time.time')
   @patch('datetime.datetime')
   def test_pass_expiration_after_24_hours(mock_datetime, mock_time):
       # Oracle Feedback #10: Fast-forward clock test
       now = 1704067200  # Jan 1, 2024 00:00 UTC
       mock_time.return_value = now

       # Grant 1-day pass
       add_pass('user1', 1, '1day', 'order1')
       assert get_active_pass('user1') is not None

       # Fast-forward 25 hours
       mock_time.return_value = now + (25 * 3600)

       # Verify expired
       assert get_active_pass('user1') is None
   ```

**Deployment:**

1. Run migration locally:
   ```bash
   cd backend
   python3 migrations/add_pricing_tables.py
   sqlite3 credits.db ".schema user_passes"
   sqlite3 credits.db ".schema daily_usage"
   ```

2. Run tests:
   ```bash
   python3 -m pytest tests/test_database_passes.py -v
   ```

3. **Ask user for production migration approval:**
   "Ready to run migration in production? This adds new tables (user_passes, daily_usage) and columns (experiment_variant, product_id to validations). No data will be lost and existing functionality is unaffected."

4. SSH to production and run migration:
   ```bash
   ssh deploy@178.156.161.140
   cd /opt/citations/backend
   python3 migrations/add_pricing_tables.py
   ```

5. Verify tables created:
   ```bash
   sqlite3 credits.db ".schema" | grep -A 10 "user_passes\|daily_usage"
   ```

6. **DO NOT deploy code changes yet** - tables exist but are unused

**Success Criteria:**
- ✅ Migration runs without errors locally and in production
- ✅ All unit tests pass
- ✅ New tables and columns exist in database
- ✅ Existing functionality unchanged (no code deployed)

---

### Phase 2: Frontend Foundation

**Goal:** Install shadcn/ui, build pricing components (not wired up yet)

**Duration:** 2 days

**Steps:**

1. **Install Tailwind + shadcn** (1 hour)
   ```bash
   cd frontend/frontend
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   npx shadcn@latest init
   npx shadcn@latest add card button
   ```

2. **Ask user for brand colors/fonts** (blocked - wait for user input)
   "What brand colors should I use for the pricing tables? Please provide:
   - Primary color (for recommended tier border/button): [hex]
   - Success color (for checkmarks): [hex]
   - Text colors (heading, body): [hex, hex]
   - Font family (if different from system default)"

   *Store response in tailwind.config.js theme.extend*

3. **Create pricing table components** (4 hours)
   - `src/components/PricingTableCredits.jsx` (full implementation above)
   - `src/components/PricingTablePasses.jsx` (full implementation above)
   - Style with shadcn Card + Button components
   - Apply brand colors from step 2

4. **Create utility files** (1 hour)
   - `src/utils/experimentVariant.js` (full implementation above)
   - `src/utils/passStatus.js` (full implementation above)

5. **Write component tests** (3 hours)
   ```javascript
   // src/components/PricingTableCredits.test.jsx
   import { render, screen, fireEvent } from '@testing-library/react'
   import { PricingTableCredits } from './PricingTableCredits'

   test('renders three pricing tiers', () => {
     const mockSelect = jest.fn()
     render(<PricingTableCredits onSelectProduct={mockSelect} experimentVariant="1" />)

     expect(screen.getByText('100 Credits')).toBeInTheDocument()
     expect(screen.getByText('500 Credits')).toBeInTheDocument()
     expect(screen.getByText('2000 Credits')).toBeInTheDocument()
   })

   test('middle tier marked as recommended', () => {
     const mockSelect = jest.fn()
     render(<PricingTableCredits onSelectProduct={mockSelect} experimentVariant="1" />)

     const middleCard = screen.getByText('500 Credits').closest('.card')
     expect(middleCard).toHaveClass('border-2')  // Recommended styling
   })

   test('calls onSelectProduct with correct product_id and variant', () => {
     const mockSelect = jest.fn()
     render(<PricingTableCredits onSelectProduct={mockSelect} experimentVariant="1" />)

     fireEvent.click(screen.getByText('Buy 100 Credits'))

     expect(mockSelect).toHaveBeenCalledWith('prod_credits_100', '1')
   })
   ```

6. **Visual regression tests** (2 hours)
   ```javascript
   // e2e/pricing-visual.spec.js
   import { test, expect } from '@playwright/test'

   test('pricing table credits matches design', async ({ page }) => {
     // Create test page that renders pricing table
     await page.goto('/test/pricing-credits')

     // Take screenshot
     await expect(page).toHaveScreenshot('pricing-credits.png')
   })

   test('pricing table passes matches design', async ({ page }) => {
     await page.goto('/test/pricing-passes')
     await expect(page).toHaveScreenshot('pricing-passes.png')
   })
   ```

**Deployment:**
- Build locally: `npm run build`
- Verify no errors
- **DO NOT deploy yet** - components exist but not used in production code

**Success Criteria:**
- ✅ Tailwind + shadcn installed without conflicts
- ✅ All component tests pass
- ✅ Visual regression screenshots generated
- ✅ Build succeeds with no errors
- ✅ Components ready for integration in Phase 3

---

### Phase 3: Tracking Infrastructure

**Goal:** Wire up variant assignment and logging (backward compatible with existing $8.99 flow)

**Duration:** 1 day

**Oracle Feedback Addressed:**
- #11: Backend backward compatible (accepts missing experiment_variant)
- #5: Track variant on all upgrade events for funnel analysis

**Steps:**

1. **Update backend endpoints** (2 hours)
   - `POST /api/upgrade-event`: Accept `experiment_variant` parameter (default 'not_assigned')
   - `POST /api/create-checkout`: Accept `experiment_variant` and `product_id` (fall back to env var if missing)
   - Ensure backward compatibility with old frontend

2. **Update frontend UpgradeModal** (2 hours)
   - Import `getExperimentVariant()`
   - Determine variant on modal open
   - Pass variant to all `/api/upgrade-event` calls
   - Pass variant to `/api/create-checkout`
   - **Don't show pricing tables yet** - keep existing $8.99 modal for now

3. **Update dashboard log parser** (2 hours)
   ```python
   # backend/dashboard/log_parser.py

   # Add regex patterns:
   EXPERIMENT_VARIANT_PATTERN = r'experiment_variant=([12]|not_assigned)'
   PRODUCT_ID_PATTERN = r'product_id=(prod_\w+)'

   # Extract in parse_upgrade_workflow():
   experiment_variant = re.search(EXPERIMENT_VARIANT_PATTERN, line)
   product_id = re.search(PRODUCT_ID_PATTERN, line)

   # Update database INSERT:
   cursor.execute("""
       UPDATE validations
       SET experiment_variant = ?, product_id = ?
       WHERE job_id = ?
   """, (experiment_variant, product_id, job_id))
   ```

4. **Update dashboard UI** (2 hours)
   ```javascript
   // backend/dashboard/static/index.html

   // Add display mappings:
   const VARIANT_DISPLAY = {
       '1': 'Credits',
       '2': 'Passes',
       'not_assigned': 'Not Assigned',
       null: 'N/A'
   };

   const PRODUCT_DISPLAY = {
       'prod_credits_100': '100 Credits ($1.99)',
       'prod_credits_500': '500 Credits ($4.99)',
       'prod_credits_2000': '2000 Credits ($9.99)',
       'prod_pass_1day': '1-Day Pass ($1.99)',
       'prod_pass_7day': '7-Day Pass ($4.99)',
       'prod_pass_30day': '30-Day Pass ($9.99)',
   };

   // Add columns to table:
   <th>Experiment Variant</th>
   <th>Product</th>

   // In table rendering:
   <td>${VARIANT_DISPLAY[row.experiment_variant] || 'N/A'}</td>
   <td>${PRODUCT_DISPLAY[row.product_id] || 'N/A'}</td>
   ```

5. **Write E2E test for tracking** (2 hours)
   ```javascript
   // e2e/upgrade-tracking.spec.js
   import { test, expect } from '@playwright/test'

   test('upgrade click logs experiment variant', async ({ page }) => {
     // Clear localStorage
     await page.goto('/')
     await page.evaluate(() => localStorage.clear())

     // Submit validation that hits limit
     await page.fill('[data-testid="citation-input"]', 'Citation text...')
     await page.click('[data-testid="validate-button"]')

     // Wait for partial results
     await page.waitForSelector('[data-testid="upgrade-button"]')

     // Click upgrade
     await page.click('[data-testid="upgrade-button"]')

     // Verify localStorage has variant
     const variant = await page.evaluate(() => localStorage.getItem('experiment_v1'))
     expect(['1', '2']).toContain(variant)

     // Verify log contains variant (would need API to check logs or mock tracking)
     // For now, check that modal opened
     await page.waitForSelector('[data-testid="upgrade-modal"]')
   })

   test('variant assignment is sticky', async ({ page }) => {
     await page.goto('/')
     await page.evaluate(() => localStorage.setItem('experiment_v1', '1'))

     // Click upgrade multiple times
     await page.click('[data-testid="upgrade-button"]')
     let variant1 = await page.evaluate(() => localStorage.getItem('experiment_v1'))

     await page.click('[data-testid="close-modal"]')
     await page.click('[data-testid="upgrade-button"]')
     let variant2 = await page.evaluate(() => localStorage.getItem('experiment_v1'))

     expect(variant1).toBe(variant2)
     expect(variant1).toBe('1')
   })
   ```

**Deployment:**

1. Deploy backend + frontend together:
   ```bash
   # Backend
   cd backend
   git add .
   git commit -m "feat: Add experiment variant tracking (backward compatible)"

   # Frontend
   cd ../frontend/frontend
   npm run build
   git add dist/
   git commit -m "feat: Wire up experiment variant assignment"

   # Push
   git push origin main

   # Deploy
   ./deploy_prod.sh
   ```

2. **Verify existing $8.99 flow still works:**
   - Test purchase with existing modal
   - Check webhook processes correctly
   - Check logs show `experiment_variant=not_assigned` for old flow

3. **Verify new tracking:**
   - Clear localStorage
   - Click upgrade button
   - Check localStorage has `experiment_v1` set
   - Check app.log shows `UPGRADE_WORKFLOW | ... | experiment_variant=1` (or 2)
   - Check dashboard shows new columns (empty for old jobs, populated for new)

**Success Criteria:**
- ✅ Existing $8.99 flow unchanged
- ✅ New upgrade clicks assign variant
- ✅ Variant logged in app.log
- ✅ Dashboard shows experiment_variant and product_id columns
- ✅ E2E tests pass

---

### Phase 4: Multi-Product Checkout

**Goal:** Enable multiple products and webhook routing

**Duration:** 2 days

**Oracle Feedback Addressed:**
- #9: Validate Polar product IDs before deployment
- #16: Log revenue data in webhook

**Steps:**

1. **Ask user for Polar product IDs** (blocked - wait for user)
   "Please provide the 6 Polar product IDs:
   - 100 credits product ID: [prod_xxx]
   - 500 credits product ID: [prod_xxx]
   - 2000 credits product ID: [prod_xxx]
   - 1-day pass product ID: [prod_xxx]
   - 7-day pass product ID: [prod_xxx]
   - 30-day pass product ID: [prod_xxx]

   Important: Name these in Polar dashboard as:
   - '100 Credits - $1.99'
   - '500 Credits - $4.99'
   - etc.

   This makes logs easier to debug."

2. **Update pricing_config.py with real IDs** (10 min)
   - Replace placeholder IDs with real ones from step 1

3. **Create product validation script** (30 min)
   ```python
   # backend/validate_polar_products.py
   import os
   import sys
   from polar_sdk import Polar
   from pricing_config import PRODUCT_CONFIG

   def validate_products():
       polar = Polar(access_token=os.getenv('POLAR_ACCESS_TOKEN'))

       print("Validating Polar product IDs...")
       print("-" * 60)

       all_valid = True

       for product_id, config in PRODUCT_CONFIG.items():
           try:
               product = polar.products.get(product_id)

               # Verify price matches
               expected_price = int(config['price'] * 100)  # Convert to cents
               actual_price = product.price_amount

               if actual_price != expected_price:
                   print(f"✗ {product_id}: Price mismatch!")
                   print(f"  Expected: ${expected_price/100:.2f}")
                   print(f"  Actual: ${actual_price/100:.2f}")
                   all_valid = False
               else:
                   print(f"✓ {product_id}: {product.name} (${config['price']})")

           except Exception as e:
               print(f"✗ {product_id}: INVALID - {e}")
               all_valid = False

       print("-" * 60)

       if all_valid:
           print("\n✅ All product IDs valid and prices match!")
           return 0
       else:
           print("\n❌ Validation failed. Fix issues before deployment.")
           return 1

   if __name__ == '__main__':
       sys.exit(validate_products())
   ```

4. **Update create-checkout endpoint** (1 hour)
   - Require `product_id` parameter (see API Changes section above)
   - Validate against PRODUCT_CONFIG
   - Use dynamic product_id for Polar API

5. **Update webhook handler** (2 hours)
   - Extract product_id from line items
   - Route to add_credits() or add_pass()
   - Log revenue data (Oracle #16)
   - (Full implementation in API Changes section above)

6. **Update UpgradeModal to show pricing tables** (2 hours)
   - Remove old $8.99 hardcoded content
   - Show PricingTableCredits or PricingTablePasses based on variant
   - Wire up onSelectProduct handler
   - (Full implementation in Frontend Components section above)

7. **Add success page logging** (30 min)
   ```javascript
   // src/pages/Success.jsx

   useEffect(() => {
     const urlParams = new URLSearchParams(window.location.search);
     const productId = urlParams.get('product_id');
     const token = urlParams.get('token');

     if (productId && token) {
       // Log success page view with product_id
       fetch('/api/upgrade-event', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify({
           event: 'success_page',
           product_id: productId,
           experiment_variant: localStorage.getItem('experiment_v1') || 'not_assigned'
         })
       });
     }
   }, []);
   ```

8. **Write comprehensive tests** (4 hours)
   ```python
   # backend/tests/test_checkout_multi_product.py

   def test_checkout_validates_product_id():
       response = client.post('/api/create-checkout', json={
           'token': 'test123',
           'product_id': 'invalid_product',
           'experiment_variant': '1'
       })
       assert response.status_code == 400

   def test_checkout_creates_link_with_correct_product(mock_polar):
       client.post('/api/create-checkout', json={
           'token': 'test123',
           'product_id': 'prod_credits_500',
           'experiment_variant': '1'
       })

       # Verify Polar called with correct product
       mock_polar.return_value.checkouts.create.assert_called_once()
       call_args = mock_polar.return_value.checkouts.create.call_args[0][0]
       assert call_args['products'] == ['prod_credits_500']

   def test_webhook_grants_credits_for_credit_product():
       webhook_payload = {
           'status': 'completed',
           'order_id': 'order_123',
           'customer_metadata': {'token': 'user_abc'},
           'line_items': [{'product_id': 'prod_credits_500', 'amount': 499}]
       }

       response = client.post('/api/polar-webhook', json=webhook_payload)

       # Verify credits added
       credits = get_credits('user_abc')
       assert credits == 500

   def test_webhook_grants_pass_for_pass_product():
       webhook_payload = {
           'status': 'completed',
           'order_id': 'order_456',
           'customer_metadata': {'token': 'user_xyz'},
           'line_items': [{'product_id': 'prod_pass_7day', 'amount': 499}]
       }

       response = client.post('/api/polar-webhook', json=webhook_payload)

       # Verify pass added
       pass_info = get_active_pass('user_xyz')
       assert pass_info is not None
       assert pass_info['pass_type'] == '7day'

   def test_webhook_idempotent():
       webhook_payload = {
           'status': 'completed',
           'order_id': 'order_789',
           'customer_metadata': {'token': 'user_123'},
           'line_items': [{'product_id': 'prod_credits_100', 'amount': 199}]
       }

       # Send twice
       client.post('/api/polar-webhook', json=webhook_payload)
       client.post('/api/polar-webhook', json=webhook_payload)

       # Verify only granted once
       credits = get_credits('user_123')
       assert credits == 100  # Not 200
   ```

   ```javascript
   // e2e/purchase-flow.spec.js

   test('credits purchase flow (mocked Polar)', async ({ page }) => {
     // Mock Polar checkout (return fake URL)
     await page.route('**/api/create-checkout', route => {
       route.fulfill({
         status: 200,
         body: JSON.stringify({
           checkout_url: 'http://localhost:5173/test/mock-checkout?product_id=prod_credits_500',
           token: 'test_user_123'
         })
       });
     });

     // Navigate and trigger upgrade
     await page.goto('/');
     await page.evaluate(() => localStorage.setItem('experiment_v1', '1'));

     // ... submit validation, hit limit ...

     await page.click('[data-testid="upgrade-button"]');

     // Should see credits pricing table
     await page.waitForSelector('text=100 Credits');
     await page.waitForSelector('text=500 Credits');

     // Click 500 credits option
     await page.click('text=Buy 500 Credits');

     // Should redirect to mock checkout
     await page.waitForURL('**/mock-checkout**');

     // Simulate webhook callback
     await page.request.post('http://localhost:8000/api/polar-webhook', {
       data: {
         status: 'completed',
         order_id: 'test_order_500',
         customer_metadata: { token: 'test_user_123' },
         line_items: [{ product_id: 'prod_credits_500', amount: 499 }]
       }
     });

     // Return to site and verify credits
     await page.goto('/');
     await page.waitForSelector('text=500 Credits');
   });
   ```

**Deployment:**

1. **Run product validation:**
   ```bash
   cd backend
   python3 validate_polar_products.py
   ```
   **Must show ✅ before proceeding**

2. **Deploy backend + frontend:**
   ```bash
   git add .
   git commit -m "feat: Enable multi-product pricing with webhook routing"
   git push origin main
   ./deploy_prod.sh
   ```

3. **Verify in production with real test purchase:**
   - Clear localStorage
   - Click upgrade → Should see pricing table (variant 1 or 2)
   - Purchase smallest tier ($1.99)
   - Check webhook log in app.log
   - Verify credits or pass granted in database:
     ```bash
     ssh deploy@178.156.161.140
     cd /opt/citations/backend
     sqlite3 credits.db "SELECT * FROM credits WHERE token='<your-test-token>';"
     sqlite3 credits.db "SELECT * FROM user_passes WHERE token='<your-test-token>';"
     ```

**Success Criteria:**
- ✅ Product validation script passes
- ✅ All unit tests pass
- ✅ E2E purchase flow tests pass
- ✅ Real test purchase succeeds in production
- ✅ Webhook logs show product_id and revenue
- ✅ Credits or pass granted correctly

---

### Phase 5: Access Control & Limit Messaging

**Goal:** Enforce pass limits, show contextual messages

**Duration:** 2 days

**Oracle Feedback Addressed:**
- #1: Atomic daily usage increment
- #2: Reject entire request if exceeds daily limit
- #14: Credits don't kick in when pass hits daily limit

**Steps:**

1. **Update validation endpoint access control** (3 hours)
   ```python
   # backend/app.py - in validate_citations_async()

   # Replace existing access check with:
   access = check_user_access(token, citation_count)

   if access['limit_type'] == 'daily_limit_insufficient':
       # Oracle Feedback #2: Reject entire request with helpful message
       return JSONResponse({
           "error": "daily_limit_insufficient",
           "message": f"You have {access['daily_remaining']} citations remaining today. Please reduce your request to {access['daily_remaining']} citations or less.",
           "daily_remaining": access['daily_remaining'],
           "requested": citation_count,
           "reset_timestamp": access['reset_timestamp']
       }, status_code=400)

   if access['allowed'] == 0:
       # No access - return partial results with limit_type
       # (Existing gating logic)
       pass

   # Process allowed citations
   # If pass user, atomically increment daily usage AFTER validation succeeds
   if access.get('pass_info'):
       increment_result = try_increment_daily_usage(token, access['allowed'])
       if not increment_result['success']:
           # Race condition - another request consumed remaining limit
           # This should be rare due to access check above
           logger.warning(f"Daily limit race condition for {token}")
           # Return partial results with what we could process
   ```

2. **Update validation response format** (1 hour)
   ```python
   # Add user_status to response (Oracle Feedback #8)

   def build_validation_response(results, access_info, token):
       response = {
           "results": results,
           "partial": len(results) < total_requested,
           "limit_type": access_info['limit_type'],

           # Oracle #8: Include user status (don't create separate endpoint)
           "user_status": {}
       }

       if access_info.get('pass_info'):
           response["user_status"] = {
               "type": "pass",
               "pass_type": access_info['pass_info']['pass_type'],
               "expiration_timestamp": access_info['pass_info']['expiration_timestamp'],
               "hours_remaining": access_info['pass_info']['hours_remaining'],
               "daily_remaining": access_info['daily_remaining']
           }
       elif access_info.get('credits_remaining') is not None:
           response["user_status"] = {
               "type": "credits",
               "credits_remaining": access_info['credits_remaining']
           }
       else:
           response["user_status"] = {
               "type": "free",
               "free_remaining": access_info.get('free_remaining', 0)
           }

       return response
   ```

3. **Update PartialResults component** (1 hour)
   ```jsx
   // src/components/PartialResults.jsx

   export function PartialResults({
     results,
     limit_type,      // NEW: From backend response
     user_status,     // NEW: For display
     reset_timestamp, // NEW: For daily limit message
     daily_remaining, // NEW: For insufficient message
     requested,       // NEW: For insufficient message
     onUpgrade
   }) {

     const handleUpgrade = () => {
       // Pass limit_type and context to UpgradeModal
       onUpgrade({
         limit_type,
         pass_info: user_status.type === 'pass' ? user_status : null,
         reset_timestamp,
         daily_remaining,
         requested
       });
     };

     // ... rest of component ...
   }
   ```

4. **Update UpgradeModal** (2 hours)
   - Implement full modal logic (see Frontend Components section)
   - Handle all limit types: credits_exhausted, pass_expired, daily_limit, daily_limit_insufficient, free_limit
   - Show appropriate pricing tables or messages

5. **Update CreditDisplay** (1 hour)
   - Use user_status from validation response
   - Show pass expiration or credits (see Frontend Components section)

6. **Write comprehensive tests** (4 hours)
   ```python
   # backend/tests/test_access_control.py

   def test_pass_user_within_daily_limit():
       # Setup: User with active 7-day pass, 500 citations used today
       token = 'user_pass_500'
       add_pass(token, 7, '7day', 'order_1')
       # ... manually insert daily_usage: 500 citations ...

       # When: Validate 100 citations
       response = client.post('/api/validate/async',
           json={'citations': '\n\n'.join(['Citation'] * 100)},
           headers={'X-User-Token': token}
       )

       # Then: Should succeed
       assert response.status_code == 200
       job_id = response.json()['job_id']

       # Wait for job completion
       time.sleep(2)
       status = client.get(f'/api/jobs/{job_id}')

       assert status.json()['status'] == 'completed'
       assert status.json()['limit_type'] == 'none'

   def test_pass_user_exceeds_daily_limit_entire_request():
       # Setup: User with active pass, 950 citations used today
       token = 'user_pass_950'
       add_pass(token, 7, '7day', 'order_2')
       # ... manually insert daily_usage: 950 citations ...

       # When: Validate 100 citations (would exceed 1000)
       response = client.post('/api/validate/async',
           json={'citations': '\n\n'.join(['Citation'] * 100)},
           headers={'X-User-Token': token}
       )

       # Then: Should reject with helpful message (Oracle #2)
       assert response.status_code == 400
       data = response.json()
       assert data['error'] == 'daily_limit_insufficient'
       assert data['daily_remaining'] == 50
       assert data['requested'] == 100
       assert 'reduce your request to 50' in data['message']

   def test_pass_user_partial_within_limit():
       # Setup: User with active pass, 980 citations used today
       token = 'user_pass_980'
       add_pass(token, 7, '7day', 'order_3')
       # ... manually insert daily_usage: 980 citations ...

       # When: Validate 30 citations (would leave 10 left)
       response = client.post('/api/validate/async',
           json={'citations': '\n\n'.join(['Citation'] * 30)},
           headers={'X-User-Token': token}
       )

       # Then: Should succeed (within limit)
       assert response.status_code == 200

   def test_expired_pass_user():
       # Setup: User with expired pass
       token = 'user_expired'
       # ... manually insert pass with expiration_timestamp in past ...

       # When: Validate citations
       response = client.post('/api/validate/async',
           json={'citations': 'Citation text'},
           headers={'X-User-Token': token}
       )

       # Then: Should treat as free user (pass not active)
       # (Verify free tier gating applies)

   def test_credits_dont_kick_in_for_pass_daily_limit():
       # Oracle Feedback #14
       # Setup: User with active pass + 500 credits, 1000 citations used today
       token = 'user_both'
       add_pass(token, 7, '7day', 'order_4')
       add_credits(token, 500, 'order_5')
       # ... manually insert daily_usage: 1000 citations ...

       # When: Validate 10 citations
       response = client.post('/api/validate/async',
           json={'citations': '\n\n'.join(['Citation'] * 10)},
           headers={'X-User-Token': token}
       )

       # Then: Should be blocked (daily limit), not fall back to credits
       job_id = response.json()['job_id']
       time.sleep(2)
       status = client.get(f'/api/jobs/{job_id}')

       assert status.json()['limit_type'] == 'daily_limit'
       # Credits should be untouched
       assert get_credits(token) == 500
   ```

   ```javascript
   // e2e/limit-messaging.spec.js

   test('daily limit insufficient shows helpful message', async ({ page }) => {
     // Setup: Create test user with pass at 980 citations today
     // (Would need test API endpoint to set up this state)

     await page.goto('/');
     // ... submit 100 citations ...

     // Should see error modal with message
     await page.waitForSelector('text=Request Too Large');
     await page.waitForSelector('text=You have 20 citations remaining');
     await page.waitForSelector('text=reduce your request to 20');
   });

   test('daily limit hit shows reset time', async ({ page }) => {
     // Setup: User with pass at 1000 citations today

     await page.goto('/');
     // ... submit validation ...

     await page.waitForSelector('text=Daily Limit Reached');
     await page.waitForSelector(/Resets at midnight UTC \(in \d+ hours\)/);

     // Should NOT see pricing table
     const buyButton = page.locator('text=Buy');
     await expect(buyButton).not.toBeVisible();
   });

   test('expired pass shows passes pricing table', async ({ page }) => {
     // Setup: User with expired 7-day pass

     await page.goto('/');
     // ... submit validation, hit limit ...

     await page.click('[data-testid="upgrade-button"]');

     // Should see passes pricing table (matching what they had)
     await page.waitForSelector('text=1-Day Pass');
     await page.waitForSelector('text=7-Day Pass');
     await page.waitForSelector('text=30-Day Pass');
   });
   ```

**Deployment:**

1. Deploy backend + frontend:
   ```bash
   git add .
   git commit -m "feat: Implement pass access control and limit messaging"
   git push origin main
   ./deploy_prod.sh
   ```

2. **Create test pass user and verify:**
   ```bash
   # SSH to prod
   ssh deploy@178.156.161.140
   cd /opt/citations/backend

   # Grant test pass
   sqlite3 credits.db "INSERT INTO user_passes (token, expiration_timestamp, pass_type, purchase_date, order_id) VALUES ('test_pass_user', $(date -d '+7 days' +%s), '7day', $(date +%s), 'manual_test_1');"

   # Verify pass active
   sqlite3 credits.db "SELECT * FROM user_passes WHERE token='test_pass_user';"
   ```

3. **Test in production:**
   - Navigate to site with `?token=test_pass_user`
   - Submit validations
   - Verify limits enforced
   - Check messaging appears correctly

**Success Criteria:**
- ✅ Pass users can validate up to 1000 citations/day
- ✅ Requests exceeding daily limit are rejected with helpful message
- ✅ Daily limit hit shows reset time, no pricing table
- ✅ Expired passes show appropriate pricing table
- ✅ Credits don't kick in when pass hits daily limit
- ✅ All tests pass

---

### Phase 6: UI Polish

**Goal:** Show pass status in header, polish UX

**Duration:** 1 day

**Oracle Feedback Addressed:**
- #7: Show "Pass expires in X days" instead of generic "Active Pass"
- #8: Don't create separate endpoint, use user_status from validation response

**Steps:**

1. **Update CreditDisplay component** (2 hours)
   - Full implementation in Frontend Components section
   - Show "Expires in X days/hours" for pass users
   - Show "X/1000 today" for daily usage
   - Show "X credits" for credit users

2. **Polish pricing table styling** (2 hours)
   - Apply final brand colors (from Phase 2)
   - Ensure responsive design (mobile, tablet, desktop)
   - Add hover states, transitions
   - Fix any alignment/spacing issues

3. **Add loading states** (1 hour)
   - Show spinner while checkout link is being created
   - Disable buttons during loading
   - Handle errors gracefully

4. **Success page improvements** (1 hour)
   ```jsx
   // src/pages/Success.jsx

   // Oracle Feedback #23: Show what was purchased
   const productId = new URLSearchParams(window.location.search).get('product_id');
   const product = PRODUCT_CONFIG[productId];

   return (
     <div>
       <h1>Purchase Successful!</h1>
       {product && (
         <p className="success-message">
           ✓ {product.display_name} added to your account!
         </p>
       )}
       <a href="/">Start validating citations →</a>
     </div>
   );
   ```

5. **Final E2E tests** (2 hours)
   - Complete purchase flows (both variants)
   - All limit scenarios
   - Mobile responsive tests

**Deployment:**

```bash
git add .
git commit -m "feat: Polish UI and complete pricing model A/B test"
git push origin main
./deploy_prod.sh
```

**Success Criteria:**
- ✅ Pass users see expiration countdown
- ✅ Pricing tables look polished on all screen sizes
- ✅ Success page shows what was purchased
- ✅ All E2E tests pass
- ✅ A/B test fully functional in production

---

## Testing Strategy

### Unit Tests

**Coverage Requirements:**
- Database functions: 100% (critical for data integrity)
- Access control logic: 100%
- Webhook handlers: 100% (idempotency critical)
- Frontend utilities: 90%

**Key Test Categories:**

1. **Time-based logic:**
   - Pass expiration calculations (1, 7, 30 days)
   - Pass extension (same type, different type)
   - Daily usage reset (midnight UTC boundary)
   - Fast-forward clock tests (Oracle #10)

2. **Concurrency:**
   - Atomic daily usage increment
   - Webhook idempotency (duplicate delivery)
   - Multiple concurrent validations

3. **Edge cases:**
   - User has both pass and credits
   - Pass expires mid-session
   - Daily limit hit exactly at 1000
   - Order already processed (idempotency)

### Integration Tests

**Scope:** Test full flows without mocking internal components (only mock Polar API)

1. **Purchase flows:**
   - Credits purchase → webhook → credits granted
   - Pass purchase → webhook → pass granted + expiration set
   - Duplicate webhook → idempotent (no double grant)

2. **Access control:**
   - Pass user validates within daily limit
   - Pass user exceeds daily limit
   - Pass user after expiration
   - Credit user runs out mid-request (partial results)

3. **Tracking:**
   - Variant assignment
   - Upgrade funnel events logged
   - Dashboard parsing and display

### E2E Tests (Playwright)

**Scope:** Full user journeys in browser

1. **Happy paths:**
   - Free user → hit limit → see pricing (variant 1) → purchase credits
   - Free user → hit limit → see pricing (variant 2) → purchase pass
   - Pass user → use within limit → success
   - Pass user → renew before expiration

2. **Error paths:**
   - Pass user → exceed daily limit → see rejection message
   - Pass user → request more than daily limit allows → see helpful message
   - Expired pass → see pricing table

3. **Visual regression:**
   - Pricing tables (both variants)
   - Upgrade modal (all limit types)
   - Success page

### Load Testing (Oracle Feedback #10)

**Before Phase 5 production deploy:**

```python
# locustfile.py
from locust import HttpUser, task, between

class PassUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Create test pass user
        self.token = f"load_test_{random.randint(1000, 9999)}"
        # ... grant pass via direct DB insert ...

    @task
    def validate_citations(self):
        # Submit validation request
        response = self.client.post('/api/validate/async',
            json={'citations': 'Citation text...'},
            headers={'X-User-Token': self.token}
        )

        if response.status_code == 200:
            job_id = response.json()['job_id']
            # Poll for results
            self.client.get(f'/api/jobs/{job_id}')
```

**Run load test:**
```bash
locust -f locustfile.py --host=http://localhost:8000 --users=100 --spawn-rate=10
```

**Monitor:**
- SQLite BUSY errors (should be zero with WAL mode + busy_timeout)
- Daily usage increment failures (should be zero with atomic transactions)
- Response times (should stay under 2s for 100 concurrent users)

---

## Deployment & Rollback

### Deployment Checklist

**Pre-Deployment:**
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Product IDs validated (Phase 4)
- [ ] Migration tested locally and in staging
- [ ] Load test completed (Phase 5)
- [ ] Rollback plan reviewed

**Deployment Steps:**

1. **Run migration in production** (Phase 1)
2. **Deploy code with feature flags OFF** (Oracle #12 - Phases 4-5)
3. **Verify in production with test purchases**
4. **Enable feature flags** (turn on multi-product)
5. **Monitor logs and dashboard**
6. **Gradual rollout** (optional: A/B test 10% of traffic first)

### Feature Flags (Oracle Feedback #12)

```python
# backend/config.py

ENABLE_MULTI_PRODUCT = os.getenv('ENABLE_MULTI_PRODUCT', 'false').lower() == 'true'
ENABLE_PASS_ACCESS_CONTROL = os.getenv('ENABLE_PASS_ACCESS_CONTROL', 'false').lower() == 'true'

# In create-checkout:
if not ENABLE_MULTI_PRODUCT:
    # Fall back to single product
    product_id = os.getenv('POLAR_PRODUCT_ID')
    experiment_variant = 'not_assigned'

# In access control:
if not ENABLE_PASS_ACCESS_CONTROL:
    # Skip pass checking, fall through to credits
    pass
```

**Deployment with flags:**
```bash
# 1. Deploy code with flags OFF
./deploy_prod.sh

# 2. Verify existing flow works
# ... test purchases ...

# 3. Enable multi-product
ssh deploy@178.156.161.140
echo "ENABLE_MULTI_PRODUCT=true" >> /opt/citations/backend/.env
sudo systemctl restart citations

# 4. Test new flow
# ... test multi-product purchases ...

# 5. Enable pass access control
echo "ENABLE_PASS_ACCESS_CONTROL=true" >> /opt/citations/backend/.env
sudo systemctl restart citations

# 6. Test pass limits
# ... create test pass user, verify limits ...
```

### Rollback Plan

**Phase 3-4 (Tracking/Multi-Product):**

1. **Immediate rollback (code):**
   ```bash
   git revert HEAD~1  # Revert last commit
   git push origin main
   ./deploy_prod.sh
   ```

2. **Feature flag rollback (no deploy):**
   ```bash
   ssh deploy@178.156.161.140
   echo "ENABLE_MULTI_PRODUCT=false" >> /opt/citations/backend/.env
   sudo systemctl restart citations
   ```

3. **Keep database tables** (no data loss)

**Phase 5 (Access Control):**

1. **Disable pass checking:**
   ```bash
   echo "ENABLE_PASS_ACCESS_CONTROL=false" >> /opt/citations/backend/.env
   sudo systemctl restart citations
   ```

2. **Users with passes** → System ignores passes, checks credits instead
3. **Passes remain in database** (can re-enable later)

**Nuclear Option (Full Rollback):**

```sql
-- Migrate active passes to credits before dropping
INSERT INTO credits (token, credits, source)
SELECT token, 1000, 'pass_migration_rollback'
FROM user_passes
WHERE expiration_timestamp > strftime('%s', 'now');

-- Drop new tables
DROP TABLE user_passes;
DROP TABLE daily_usage;

-- Remove tracking columns (optional - loses experiment data)
-- SQLite doesn't support DROP COLUMN easily, so leave them NULL
```

### Monitoring

**Week 1 (Critical):**
- Check dashboard daily for experiment data
- Monitor webhook logs for grant failures
- Verify both variants receiving traffic (~50/50 split)
- Check for user-reported payment issues
- Monitor SQLite performance (BUSY errors)

**Week 2-4 (Analysis):**
- Analyze conversion rates by variant
- Identify most popular product tiers
- Monitor pass renewal behavior
- Check daily limit enforcement (abuse patterns?)
- Calculate revenue by variant (Oracle #16)

**Alerts to Set Up:**
- Webhook processing failures (order granted but credits/pass not added)
- SQLite BUSY errors (concurrency issues)
- Unexpected daily usage spikes (potential abuse)
- Product ID mismatches (Polar product doesn't exist)

---

## Oracle Feedback Integration

### Critical Fixes Implemented

1. **Race Condition - Daily Usage (#1)**
   - **Problem:** Concurrent requests could exceed 1000/day limit
   - **Solution:** Atomic `try_increment_daily_usage()` with BEGIN IMMEDIATE
   - **Impact:** Prevents data corruption, ensures fair use enforcement

2. **Partial Results Logic (#2)**
   - **Problem:** Undefined behavior when pass user requests more citations than daily limit allows
   - **Solution:** Reject entire request with message: "You have X citations remaining"
   - **Impact:** Clear UX, no confusion about partial processing

3. **Timezone Handling (#3)**
   - **Problem:** Storing dates as strings ('2025-12-10') causes confusion about when reset occurs
   - **Solution:** Store `reset_timestamp` (Unix timestamp of next UTC midnight)
   - **Impact:** Unambiguous reset time, easier "hours until reset" calculation

4. **Webhook Idempotency (#6)**
   - **Problem:** Race between idempotency check and insert could allow double-grant
   - **Solution:** BEGIN IMMEDIATE + try/catch IntegrityError
   - **Impact:** Prevents double-charging users

### Simplifications Applied

5. **Experiment Variant Tracking (#5)**
   - **Oracle suggested:** Remove variant from early events
   - **Our decision:** Keep variant on all events for funnel analysis
   - **Rationale:** Need to measure "pricing table shown → conversion" for both variants

6. **User Status Endpoint (#8)**
   - **Oracle suggested:** Don't create separate `/api/user-status`
   - **Solution:** Return `user_status` in existing `/api/validate` response
   - **Impact:** One fewer API call, faster UI updates

7. **Pass Display (#7)**
   - **Oracle suggested:** Show detailed expiration ("Expires in 2 days")
   - **Solution:** Implemented in `formatPassExpiration()` utility
   - **Impact:** More informative than generic "Active Pass"

### Technical Improvements

8. **SQLite Concurrency (#10)**
   - **Added:** WAL mode + busy_timeout=5000 in connection string
   - **Added:** Load testing requirement before Phase 5 deploy
   - **Impact:** Handles 100+ concurrent requests without BUSY errors

9. **Product Validation (#9)**
   - **Added:** `validate_polar_products.py` script
   - **Requirement:** Must pass before Phase 4 deploy
   - **Impact:** Catches typos before production (prevents silent webhook failures)

10. **Pass Expiration Test (#15)**
    - **Added:** Fast-forward clock test with time.time() mocking
    - **Impact:** Validates time-based logic works correctly

### Deployment Improvements

11. **Backward Compatibility (#11)**
    - **Backend:** Accepts missing `experiment_variant` (defaults to 'not_assigned')
    - **Impact:** Old frontend won't break if deploy fails mid-rollout

12. **Feature Flags (#12)**
    - **Added:** `ENABLE_MULTI_PRODUCT` and `ENABLE_PASS_ACCESS_CONTROL`
    - **Impact:** Can deploy code with features OFF, test in prod, then enable

13. **Health Check (#13)**
    - **Oracle suggested:** Admin endpoint for pass system health
    - **Our decision:** Skip for MVP, query DB directly if needed
    - **Rationale:** Adds complexity, manual queries sufficient for now

### Business Logic Clarifications

14. **Pass + Credits Behavior (#14)**
    - **Clarified:** Credits DON'T kick in when pass hits daily limit
    - **Rationale:** Prevents confusion, simpler logic
    - **Impact:** User blocked until reset (clear expectation)

15. **Pass Extension Logic (#15)**
    - **Clarified:** Always extend expiration by adding days (regardless of pass type)
    - **Example:** 3 days left + buy 30-day pass = 33 days total
    - **Rationale:** User shouldn't lose remaining time

16. **Revenue Tracking (#16)**
    - **Added:** Log `amount_cents` from Polar webhook
    - **Impact:** Can calculate revenue by variant without manual price lookups
    - **Future:** Enables revenue dashboards

### Minor Improvements

17. **Success Page (#23)**
    - **Added:** Show which product was purchased ("✓ 500 Credits added!")
    - **Impact:** Better UX confirmation

18. **Consistent Naming**
    - **Standardized:** "1day" / "7day" / "30day" across DB, config, display
    - **Impact:** Easier debugging

---

## Future Enhancements (Not in Scope)

- **Dynamic pricing** based on user behavior
- **Subscription model** (recurring passes)
- **Team/institutional pricing**
- **Volume discounts** (buy 5000 credits, get 10% off)
- **Referral credits** (invite friends, get bonus)
- **Pass gifting** (send pass to colleague)
- **Annual passes** (365 days for $99)
- **API access** (pay-per-API-call model)
- **White-label** (allow institutions to customize pricing)

---

**End of Implementation Plan**
