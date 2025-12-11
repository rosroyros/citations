You are conducting a code review.

## Task Context

### Beads Issue ID: q2y5

citations-q2y5: P3.1: Add upgrade event logging to backend
Status: in_progress
Priority: P1
Type: task
Created: 2025-12-10 22:11
Updated: 2025-12-11 17:44

Description:
## Overview

Create centralized upgrade event logging function in backend. This function will be called throughout the upgrade funnel to track user behavior.

**File to modify:** `backend/app.py`

**Why this is needed:** To measure A/B test success, we need to track the complete upgrade funnel: pricing_table_shown → product_selected → checkout_started → purchase_completed. Without this data, we can't determine which variant converts better.

**Oracle Feedback #5:** Track experiment_variant on ALL events, not just purchase. This lets us measure "how many users saw each pricing table" which is critical for conversion rate calculation.

## Important Context

**What is the upgrade funnel?**

The sequence of events a user goes through from seeing pricing to completing purchase:

```
User has 0 credits
  ↓
clicks "Upgrade" → [pricing_table_shown] (assigned variant here)
  ↓
sees pricing table (Credits OR Passes)
  ↓
clicks "Buy 500 Credits" → [product_selected]
  ↓
redirected to Polar checkout → [checkout_started]
  ↓
completes purchase → [purchase_completed] (webhook)
  ↓
credits/pass granted → [credits_applied]
```

**Why track each step?**
- Identify where users drop off
- Calculate conversion rates per variant
- Measure effectiveness of pricing messaging
- Optimize funnel weak points

**Example analysis questions this enables:**
- "How many users saw Credits vs Passes pricing?"
- "Which variant has better click-through from table to checkout?"
- "What's the completion rate once checkout starts?"
- "Does one variant have more checkout abandonment?"

## Event Types

These 6 events cover the complete funnel:

| Event Name | When Triggered | Who Calls It | Data Included |
|------------|----------------|--------------|---------------|
| pricing_table_shown | User clicks upgrade, pricing modal opens | Frontend validation handler | token, variant |
| product_selected | User clicks buy button on pricing card | Frontend pricing table | token, variant, product_id |
| checkout_started | Polar checkout URL generated | Backend create-checkout endpoint | token, variant, product_id |
| purchase_completed | Polar webhook confirms payment | Backend webhook handler | token, variant, product_id, amount |
| purchase_failed | Polar webhook reports failure | Backend webhook handler | token, variant, product_id, error |
| credits_applied | Credits/pass successfully granted to DB | Backend after add_credits/add_pass | token, variant, product_id, amount |

**Note:** All events include `experiment_variant` per Oracle #5.

## Complete Implementation

Add this function to `backend/app.py`:

```python
import json
import time

def log_upgrade_event(event_name: str, token: str, experiment_variant: str = None,
                      product_id: str = None, amount_cents: int = None,
                      error: str = None, metadata: dict = None):
    """
    Log upgrade funnel event to app.log for analytics.

    Purpose: Track A/B test conversion funnel to determine which pricing variant
    converts better. All events include experiment_variant for cohort analysis.

    Oracle Feedback #5: We track variant on all events (not just purchase) to measure:
    - How many users saw each pricing table
    - Drop-off rates at each funnel stage
    - Conversion rates by variant

    Log Format: JSON structure for easy parsing by dashboard
    Prefix: "UPGRADE_EVENT:" for easy filtering

    Args:
        event_name: One of: pricing_table_shown, product_selected, checkout_started,
                    purchase_completed, purchase_failed, credits_applied
        token: User token (first 8 chars for privacy)
        experiment_variant: '1' (credits) or '2' (passes) - ALWAYS include per Oracle #5
        product_id: Polar product ID (e.g., 'prod_credits_500')
        amount_cents: Purchase amount in cents (for revenue tracking)
        error: Error message (for failed events)
        metadata: Additional event-specific data

    Example log entries:
        UPGRADE_EVENT: {"timestamp": 1704067200, "event": "pricing_table_shown",
                       "token": "abc12345", "experiment_variant": "1"}

        UPGRADE_EVENT: {"timestamp": 1704067205, "event": "product_selected",
                       "token": "abc12345", "experiment_variant": "1",
                       "product_id": "prod_credits_500"}

        UPGRADE_EVENT: {"timestamp": 1704067210, "event": "purchase_completed",
                       "token": "abc12345", "experiment_variant": "1",
                       "product_id": "prod_credits_500", "amount_cents": 499}

    Usage:
        # When pricing table shown
        log_upgrade_event('pricing_table_shown', token, experiment_variant='1')

        # When user clicks buy button
        log_upgrade_event('product_selected', token,
                         experiment_variant='1', product_id='prod_credits_500')

        # When checkout URL generated
        log_upgrade_event('checkout_started', token,
                         experiment_variant='1', product_id='prod_credits_500')

        # When webhook confirms purchase
        log_upgrade_event('purchase_completed', token,
                         experiment_variant='1', product_id='prod_credits_500',
                         amount_cents=499)

        # When credits/pass granted
        log_upgrade_event('credits_applied', token,
                         experiment_variant='1', product_id='prod_credits_500',
                         metadata={'amount': 500, 'type': 'credits'})
    """
    # Build event payload
    payload = {
        'timestamp': int(time.time()),  # Unix timestamp
        'event': event_name,
        'token': token[:8] if token else None,  # Privacy: only log first 8 chars
        'experiment_variant': experiment_variant  # CRITICAL: Always include (Oracle #5)
    }

    # Add optional fields if provided
    if product_id:
        payload['product_id'] = product_id

    if amount_cents is not None:
        payload['amount_cents'] = amount_cents
        payload['amount_dollars'] = amount_cents / 100  # For readability

    if error:
        payload['error'] = error

    if metadata:
        payload['metadata'] = metadata

    # Log as JSON for easy parsing
    app.logger.info(f"UPGRADE_EVENT: {json.dumps(payload)}")

    # Also log human-readable version for debugging
    app.logger.debug(
        f"Upgrade funnel: {event_name} | "
        f"token={token[:8]} | variant={experiment_variant} | "
        f"product={product_id or 'n/a'}"
    )
```

## Where to Place in app.py

Add the function near other utility functions, before the route handlers:

```python
# backend/app.py

from flask import Flask, request, jsonify
import json
import time
# ... other imports ...

app = Flask(__name__)

# ... existing helper functions (get_credits, add_credits, etc.) ...

# ADD log_upgrade_event() HERE (after helpers, before routes)
def log_upgrade_event(...):
    # ... function code above ...

# ... route handlers (@app.route) below ...
```

## Step-by-Step Implementation

### Step 1: Locate app.py and Backup

```bash
cd backend
cp app.py app.py.backup
ls -la app.py app.py.backup
```

Expected: Both files exist

### Step 2: Find Insertion Point

```bash
# Find where helper functions end and routes begin
grep -n "^@app.route" app.py | head -5
```

Expected output shows line numbers of first few routes (e.g., line 150, 175, etc.)

**Insert the log_upgrade_event() function BEFORE the first @app.route line.**

### Step 3: Add Required Imports

Check if these imports exist at top of app.py:

```bash
grep "^import json" app.py
grep "^import time" app.py
```

If either is missing, add to imports section:

```python
import json  # For JSON encoding events
import time  # For Unix timestamps
```

### Step 4: Add the Function

Insert complete log_upgrade_event() function from above.

### Step 5: Verify Syntax

```bash
python3 -m py_compile app.py
```

Expected: No output (successful compilation)

If syntax error:
```bash
python3 app.py
```

Will show exact line number of error.

### Step 6: Test the Function

Create a test script `test_log_upgrade_event.py`:

```python
#!/usr/bin/env python3
"""
Test script for log_upgrade_event function.

Run this to verify logging works before integrating into routes.
"""

import sys
import logging
from flask import Flask

# Create minimal Flask app for testing
app = Flask(__name__)

# Configure logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Import/paste the log_upgrade_event function here
# (or import from app if structured as module)
def log_upgrade_event(event_name, token, experiment_variant=None,
                      product_id=None, amount_cents=None,
                      error=None, metadata=None):
    import json
    import time

    payload = {
        'timestamp': int(time.time()),
        'event': event_name,
        'token': token[:8] if token else None,
        'experiment_variant': experiment_variant
    }

    if product_id:
        payload['product_id'] = product_id
    if amount_cents is not None:
        payload['amount_cents'] = amount_cents
        payload['amount_dollars'] = amount_cents / 100
    if error:
        payload['error'] = error
    if metadata:
        payload['metadata'] = metadata

    app.logger.info(f"UPGRADE_EVENT: {json.dumps(payload)}")
    app.logger.debug(
        f"Upgrade funnel: {event_name} | token={token[:8]} | "
        f"variant={experiment_variant} | product={product_id or 'n/a'}"
    )

# Run with Flask app context
with app.app_context():
    print("Testing log_upgrade_event()...")
    print("-" * 60)

    # Test 1: pricing_table_shown
    print("\n1. Pricing table shown (variant 1)")
    log_upgrade_event('pricing_table_shown', 'abc123def456', experiment_variant='1')

    # Test 2: product_selected
    print("\n2. Product selected")
    log_upgrade_event('product_selected', 'abc123def456',
                     experiment_variant='1', product_id='prod_credits_500')

    # Test 3: checkout_started
    print("\n3. Checkout started")
    log_upgrade_event('checkout_started', 'abc123def456',
                     experiment_variant='1', product_id='prod_credits_500')

    # Test 4: purchase_completed with revenue
    print("\n4. Purchase completed")
    log_upgrade_event('purchase_completed', 'abc123def456',
                     experiment_variant='1', product_id='prod_credits_500',
                     amount_cents=499)

    # Test 5: credits_applied with metadata
    print("\n5. Credits applied")
    log_upgrade_event('credits_applied', 'abc123def456',
                     experiment_variant='1', product_id='prod_credits_500',
                     metadata={'amount': 500, 'type': 'credits'})

    # Test 6: purchase_failed
    print("\n6. Purchase failed")
    log_upgrade_event('purchase_failed', 'abc123def456',
                     experiment_variant='2', product_id='prod_pass_7day',
                     error='Payment declined')

    print("\n" + "-" * 60)
    print("✓ All tests completed. Check output above for UPGRADE_EVENT logs.")
    print("Each test should show:")
    print("  - INFO level: JSON payload")
    print("  - DEBUG level: Human-readable summary")
```

**Run the test:**

```bash
cd backend
python3 test_log_upgrade_event.py
```

**Expected output:**

```
Testing log_upgrade_event()...
------------------------------------------------------------

1. Pricing table shown (variant 1)
2024-12-10 22:00:00 - INFO - UPGRADE_EVENT: {"timestamp": 1702252800, "event": "pricing_table_shown", "token": "abc123de", "experiment_variant": "1"}

2. Product selected
2024-12-10 22:00:00 - INFO - UPGRADE_EVENT: {"timestamp": 1702252800, "event": "product_selected", "token": "abc123de", "experiment_variant": "1", "product_id": "prod_credits_500"}

... (rest of tests)

✓ All tests completed. Check output above for UPGRADE_EVENT logs.
```

**Verify each log entry:**
- ✅ Has "UPGRADE_EVENT:" prefix
- ✅ Is valid JSON
- ✅ Includes timestamp
- ✅ Includes event name
- ✅ Token truncated to 8 chars
- ✅ experiment_variant present on all events

### Step 7: Verify Function is Callable from Routes

Test importing in Python interactive shell:

```bash
cd backend
python3
```

```python
>>> from app import log_upgrade_event
>>> log_upgrade_event('test_event', 'test_token_12345', experiment_variant='1')
>>> # Should print log entry
>>> exit()
```

Expected: Function imports successfully, logs appear.

### Step 8: Check app.log Location

```bash
# Find where Flask logs to
grep -r "app.log" . | head -5
```

Or check Flask logging configuration in app.py:

```python
# Usually configured near top of app.py
import logging
logging.basicConfig(filename='app.log', level=logging.INFO)
```

**If logging not configured, add it:**

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
if not app.debug:
    file_handler = RotatingFileHandler('app.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Citations app startup')
```

## Verification Checklist

```bash
cd backend

# 1. Function exists in app.py
grep -c "def log_upgrade_event" app.py
# Should output: 1

# 2. Function has correct signature
grep "def log_upgrade_event" app.py

# 3. All 6 event types mentioned in docstring
grep -c "pricing_table_shown\|product_selected\|checkout_started\|purchase_completed\|purchase_failed\|credits_applied" app.py
# Should be at least 6 (in docstring)

# 4. Required imports present
grep "import json" app.py
grep "import time" app.py

# 5. Test script runs successfully
python3 test_log_upgrade_event.py

# 6. Syntax check passes
python3 -m py_compile app.py && echo "✓ Syntax OK"
```

## Common Issues and Fixes

### Issue 1: "NameError: name 'app' is not defined"
**Cause:** Function defined before Flask app instantiation
**Fix:** Move function AFTER `app = Flask(__name__)` line

### Issue 2: Logs not appearing
**Cause:** Logging not configured or log level too high
**Fix:** Add logging configuration (see Step 8 above)
**Verify:** Check app.log file exists and is writable

### Issue 3: "TypeError: Object of type datetime is not JSON serializable"
**Cause:** Trying to serialize datetime objects
**Fix:** Use `int(time.time())` for Unix timestamps (already in code)

### Issue 4: Token not truncated
**Cause:** Missing `[:8]` slice
**Fix:** Verify line: `'token': token[:8] if token else None`

### Issue 5: experiment_variant missing from logs
**Cause:** Forgot to pass parameter in function call
**Fix:** Always include: `log_upgrade_event('event', token, experiment_variant='1')`
**Oracle #5:** This is CRITICAL - never omit experiment_variant

## Success Criteria

- ✅ Function added to `backend/app.py`
- ✅ Function has complete docstring with examples
- ✅ All 6 event types documented
- ✅ Required imports (json, time) present
- ✅ Test script runs successfully
- ✅ Logs include "UPGRADE_EVENT:" prefix
- ✅ Logs are valid JSON
- ✅ Token truncated to 8 chars (privacy)
- ✅ experiment_variant included on all events (Oracle #5)
- ✅ amount_cents and amount_dollars calculated correctly
- ✅ Function callable from routes
- ✅ No syntax errors

## What NOT to Do

- ❌ Don't call this function yet (that's P3.2, P3.3)
- ❌ Don't log full tokens (privacy concern)
- ❌ Don't skip experiment_variant (breaks conversion analysis)
- ❌ Don't use datetime objects (use Unix timestamps)
- ❌ Don't forget to test before proceeding

## Time Estimate

1 hour (including testing and verification)

## Dependencies

- **Depends on:** Phase 2 complete (need variant utility defined, though not used in this task)
- **Blocks:** P3.2, P3.3, P3.4 (all call this function)

## Next Steps

After this function is complete and tested, move to P3.2 to add tracking to the validation endpoint (first place function gets called), then P3.3 for webhook tracking.

## Progress - 2025-12-11

Successfully implemented the log_upgrade_event function in backend/app.py:

### Completed Tasks:
1. ✅ Created backup of app.py
2. ✅ Verified required imports (json, time) already exist
3. ✅ Added log_upgrade_event function with complete documentation
4. ✅ Function supports all 6 event types:
   - pricing_table_shown
   - product_selected
   - checkout_started
   - purchase_completed
   - purchase_failed
   - credits_applied
5. ✅ All events include experiment_variant (Oracle #5 requirement)
6. ✅ Logs use JSON format with UPGRADE_EVENT: prefix for easy parsing
7. ✅ Token truncated to 8 chars for privacy
8. ✅ Function imports and runs successfully
9. ✅ Logging configured to write to ../logs/app.log
10. ✅ Created and ran test script verifying all functionality

### Key Implementation Details:
- Function placed before first route handler (line 405-475)
- Uses existing logger instance configured in logger.py
- Logs both JSON (INFO level) and human-readable (DEBUG level) formats
- Includes optional fields: product_id, amount_cents, error, metadata
- Calculates amount_dollars from amount_cents for readability

### Test Results:
- All 6 event types tested successfully
- JSON logs valid and parseable
- experiment_variant included on all events
- app.log receiving events correctly

### What Was Implemented

Added a centralized `log_upgrade_event` function to backend/app.py that logs A/B test funnel events in JSON format. The function supports all 6 required event types (pricing_table_shown, product_selected, checkout_started, purchase_completed, purchase_failed, credits_applied), includes experiment_variant on all events per Oracle feedback #5, and truncates tokens to 8 characters for privacy.

### Requirements/Plan

Key requirements from task description:
- Add log_upgrade_event function to backend/app.py ✅
- Support all 6 funnel event types ✅
- Include experiment_variant on ALL events (Oracle #5) ✅
- Use JSON format with "UPGRADE_EVENT:" prefix ✅
- Truncate tokens to 8 chars for privacy ✅
- Function must be callable from routes ✅
- Log to app.log file ✅

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: 0ebf41d4f5522d1d3a0f27b0427e30e4f7cc7a35
- HEAD_SHA: 1b843adb868a1f205bc5595d4cb247f34e841a87

Use git commands (git diff, git show, git log, etc.) to examine the changes.

## Review Criteria

Evaluate the implementation against these criteria:

**Adherence to Task:**
- Does implementation match task requirements?
- Were all requirements addressed?
- Any scope creep or missing functionality?

**Security:**
- SQL injection, XSS, command injection vulnerabilities
- Hardcoded secrets or credentials
- Input validation and sanitization

**Code Quality:**
- Follows project standards and patterns
- Clear naming and structure
- Appropriate error handling
- Edge cases covered

**Testing:**
- Tests written and passing
- Coverage adequate
- Tests verify actual behavior
- **Frontend visual/UX changes: Playwright tests REQUIRED for any visual or user interaction changes**

**Performance & Documentation:**
- No obvious performance issues
- Code is self-documenting or commented

## Required Output Format

Provide structured feedback in these categories:

1. **Critical**: Must fix immediately (security, broken functionality, data loss)
2. **Important**: Should fix before merge (bugs, missing requirements, poor patterns)
3. **Minor**: Nice to have (style, naming, optimization opportunities)
4. **Strengths**: What was done well

**IMPORTANT**: Verify implementation matches task requirements above.

Be specific with file:line references for all issues.