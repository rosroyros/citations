You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-h62h

**Title:** Implement pricing model A/B test (Credits vs Day Passes)
**Status:** open
**Priority:** P1
**Type:** feature

## Current Status

We've completed the design phase for implementing an A/B test of two pricing models:
- **Variant 1 (Credits):** Pay-per-citation model (100/$1.99, 500/$4.99, 2000/$9.99)
- **Variant 2 (Day Passes):** Time-based access (1-day/$1.99, 7-day/$4.99, 30-day/$9.99)

The complete design document has been written to `docs/plans/2025-12-10-pricing-model-ab-test-design.md`.

## The Question

User wants to focus on: "share the plan and ask for concrete feedback"

We need your review of the complete design document to identify:
1. **Potential implementation risks or gotchas** we may have missed
2. **Simplifications** - areas where we might be overcomplicating things
3. **Technical concerns** - database design, API design, race conditions, edge cases
4. **Testing gaps** - areas that need more robust testing
5. **Deployment risks** - phasing strategy, rollback concerns, migration issues
6. **Any critical oversights** in the architecture or implementation plan

Please provide concrete, actionable feedback on the design.

## Design Document

Below is the complete design document for your review:

---

# Pricing Model A/B Test Design

**Date:** 2025-12-10
**Status:** Design Complete - Ready for Implementation

## Overview

Implement A/B test comparing two pricing models:
- **Variant 1 (Credits):** Pay per citation (100/$1.99, 500/$4.99, 2000/$9.99)
- **Variant 2 (Passes):** Time-based access (1-day/$1.99, 7-day/$4.99, 30-day/$9.99)

**Goal:** Optimize for conversion rate (percentage of users who purchase)

## System Requirements

### Current State
- Single pricing option: 1000 credits for $8.99
- Credits stored in `credits.db`, deducted per citation
- Polar integration for checkout/webhooks
- Upgrade modal triggered on limit reached
- Free tier: 5 validations, then locked results

### New Capabilities
1. Multiple product tiers (3 per variant)
2. A/B test infrastructure with obfuscated variant assignment
3. Time-based pass system with daily rate limits
4. Contextual limit messaging
5. Full tracking through upgrade funnel and dashboard

---

## Design Section 1: A/B Test Architecture

### Variant Assignment

**Timing:** Variant determined when user first clicks "Upgrade" button or sees pricing table (not on validation)

**Storage:** localStorage as `experiment_v1` with values `1` or `2`

**Backend Mapping:**
```python
# backend/pricing_config.py
EXPERIMENT_VARIANTS = {
    '1': 'credits',
    '2': 'passes'
}

PRODUCT_CONFIG = {
    # Variant 1: Credits (placeholder IDs - will be replaced with real Polar IDs)
    'prod_credits_100': {
        'variant': '1',
        'type': 'credits',
        'amount': 100,
        'price': 1.99
    },
    'prod_credits_500': {
        'variant': '1',
        'type': 'credits',
        'amount': 500,
        'price': 4.99
    },
    'prod_credits_2000': {
        'variant': '1',
        'type': 'credits',
        'amount': 2000,
        'price': 9.99
    },

    # Variant 2: Passes (placeholder IDs)
    'prod_pass_1day': {
        'variant': '2',
        'type': 'pass',
        'days': 1,
        'price': 1.99,
        'daily_limit': 1000  # citations per day
    },
    'prod_pass_7day': {
        'variant': '2',
        'type': 'pass',
        'days': 7,
        'price': 4.99,
        'daily_limit': 1000
    },
    'prod_pass_30day': {
        'variant': '2',
        'type': 'pass',
        'days': 30,
        'price': 9.99,
        'daily_limit': 1000
    }
}
```

### Tracking Integration

**Frontend:**
```javascript
// utils/experimentVariant.js
export function getExperimentVariant() {
  let variantId = localStorage.getItem('experiment_v1');
  if (!variantId) {
    variantId = Math.random() < 0.5 ? '1' : '2';
    localStorage.setItem('experiment_v1', variantId);
  }
  return variantId;
}
```

**Logging:** Add `experiment_variant` attribute to upgrade funnel events:
```
UPGRADE_WORKFLOW | job_id=xxx | event=clicked_upgrade | experiment_variant=1
UPGRADE_WORKFLOW | job_id=xxx | event=modal_proceed | experiment_variant=1 | product_id=prod_credits_500
UPGRADE_WORKFLOW | job_id=xxx | event=checkout_created | experiment_variant=1 | product_id=prod_credits_500
UPGRADE_WORKFLOW | job_id=xxx | event=success_page | experiment_variant=1 | product_id=prod_credits_500
```

**API Changes:**
- `POST /api/upgrade-event`: Accept `experiment_variant` in payload
- `POST /api/create-checkout`: Accept `experiment_variant` and `product_id`

**Edge Cases:**
- User clears localStorage → gets new variant on next upgrade click
- One job can have multiple variants if localStorage cleared mid-session
- Parser stores whatever variant appears in logs (no conflict resolution)

---

## Design Section 2: Database Schema & Access Control

### New Database Tables

```sql
-- Time-based pass access
CREATE TABLE user_passes (
    token TEXT PRIMARY KEY,
    expiration_timestamp INTEGER NOT NULL,  -- Unix timestamp (purchase_time + days * 86400)
    pass_type TEXT NOT NULL,                -- '1day', '7day', '30day'
    purchase_date INTEGER NOT NULL,
    order_id TEXT UNIQUE NOT NULL           -- For idempotency
);

-- Daily rate limiting for pass users
CREATE TABLE daily_usage (
    token TEXT NOT NULL,
    date TEXT NOT NULL,                     -- YYYY-MM-DD format
    citations_count INTEGER DEFAULT 0,      -- Counts citations, not jobs
    PRIMARY KEY (token, date)
);

-- Tracking columns
ALTER TABLE validations ADD COLUMN experiment_variant TEXT;
ALTER TABLE validations ADD COLUMN product_id TEXT;
```

### Access Control Logic (Per Citation)

On each validation request, check access based on `citation_count`:

1. **Active pass check:**
   - Query: `SELECT * FROM user_passes WHERE token=? AND expiration_timestamp > now()`
   - If found: Check daily usage
   - Query: `SELECT citations_count FROM daily_usage WHERE token=? AND date=today()`
   - If `citations_count + request_citation_count <= 1000`: Allow + increment by citation_count
   - If exceeds 1000: Return partial results + `limit_type='daily_limit'`

2. **Credits check (existing logic):**
   - If `credits >= citation_count`: Allow + deduct citation_count
   - If `credits < citation_count`: Partial results + `limit_type='credits_exhausted'`

3. **Free tier (existing):**
   - 5 free validations, then locked results + `limit_type='free_limit'`

### Pass Extension Logic

When user purchases pass while already having active pass of same type:
- New expiration = current expiration + (days * 86400)
- Example: 3 days remaining on 7-day pass + buy 7-day pass = 10 days total

### User Messages by Limit Type

| Scenario | PartialResults Banner | UpgradeModal Content |
|----------|----------------------|---------------------|
| **credits_exhausted** | "🔒 {N} more citations available" | "You've used all your credits." + Credits pricing table |
| **pass_expired** | "🔒 {N} more citations available" | "Your {X}-day pass has expired." + Passes pricing table (match their previous purchase) |
| **daily_limit** | "🔒 {N} more citations available" | "You've reached today's limit of 1,000 citations. Resets at midnight UTC (in {X} hours)." + Close button only (no pricing table) |
| **free_limit** | "🔒 {N} more citations available" | Show pricing table based on assigned experiment variant |

**Implementation:**
- Backend returns `limit_type` in partial results response
- Frontend passes to `UpgradeModal` as prop
- Modal renders appropriate message + pricing table

---

## Design Section 3: Frontend Components

### shadcn/ui Setup

```bash
cd frontend/frontend

# Install Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# Update tailwind.config.js content paths:
# ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"]

# Create/update src/index.css:
# @tailwind base;
# @tailwind components;
# @tailwind utilities;

# Initialize shadcn/ui
npx shadcn@latest init
# Select: React, Tailwind CSS, CSS variables: yes, base color: neutral

# Add components
npx shadcn@latest add card button
```

### Component Structure

```
src/
  components/
    ui/                          (new - shadcn components)
      card.jsx
      button.jsx
    UpgradeModal.jsx             (update)
    PricingTableCredits.jsx      (new)
    PricingTablePasses.jsx       (new)
    PartialResults.jsx           (minor update)
    CreditDisplay.jsx            (update - show "Active Pass" for pass users)
  utils/
    experimentVariant.js         (new)
    passStatus.js                (new - time calculations)
  lib/
    utils.js                     (new - shadcn helper)
```

### PricingTableCredits.jsx

```jsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export function PricingTableCredits({ onSelectProduct, token, experimentVariant }) {
  const products = [
    {
      id: 'prod_credits_100',  // Replace with real Polar ID
      credits: 100,
      price: 1.99,
      recommended: false,
      description: "For occasional users"
    },
    {
      id: 'prod_credits_500',
      credits: 500,
      price: 4.99,
      recommended: true,
      description: "Best balance of price & usage"
    },
    {
      id: 'prod_credits_2000',
      credits: 2000,
      price: 9.99,
      recommended: false,
      description: "For frequent academic writing"
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
      {products.map(product => (
        <Card
          key={product.id}
          className={product.recommended ? 'border-blue-600 border-2 shadow-lg' : ''}
        >
          <CardHeader>
            <CardTitle>{product.credits} Credits</CardTitle>
            <CardDescription>{product.description}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold mb-4">${product.price}</p>
            <ul className="space-y-2 text-sm">
              <li>✓ {product.credits} citation validations</li>
              <li>✓ APA / MLA / Chicago support</li>
              <li>✓ Credits never expire</li>
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

### PricingTablePasses.jsx

Similar structure, but with:
- `days` instead of `credits`
- "X-Day Pass" instead of "X Credits"
- Benefits: "Unlimited validations during pass period", "Up to 1,000 citations per day", etc.

### Updated UpgradeModal.jsx

**Props:**
- `limitType`: 'credits_exhausted' | 'pass_expired' | 'daily_limit' | 'free_limit'
- `variant`: '1' | '2' (experiment variant)
- `passType`: '1day' | '7day' | '30day' (if applicable)
- `hoursUntilReset`: number (for daily_limit scenario)

**Behavior:**
1. Render contextual message based on `limitType`
2. Show `PricingTableCredits` or `PricingTablePasses` based on `variant`
3. If `limitType='daily_limit'`: Show message only, no pricing table
4. If `limitType='pass_expired'`: Show variant matching their previous purchase (not experiment variant)
5. Handle product selection → call `/api/create-checkout` with `{token, product_id, experiment_variant}`

### CreditDisplay Update

Instead of showing credit count for pass users, show:
```jsx
{hasActivePass ? (
  <div>Active Pass</div>
) : (
  <div>{credits} Credits</div>
)}
```

---

## Design Section 4: Backend Implementation

### New Database Functions

```python
# backend/database.py

def add_pass(token: str, days: int, pass_type: str, order_id: str) -> bool:
    """
    Grant time-based pass to user (idempotent).

    If user already has active pass of same type, extend expiration.
    If different type, replace with new pass.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if order already processed (idempotency)
        cursor.execute("SELECT token FROM user_passes WHERE order_id = ?", (order_id,))
        if cursor.fetchone():
            return True  # Already processed

        # Check for existing active pass
        now = int(time.time())
        cursor.execute(
            "SELECT expiration_timestamp, pass_type FROM user_passes WHERE token = ? AND expiration_timestamp > ?",
            (token, now)
        )
        existing = cursor.fetchone()

        if existing and existing[1] == pass_type:
            # Extend existing pass
            new_expiration = existing[0] + (days * 86400)
        else:
            # New pass (starts now)
            new_expiration = now + (days * 86400)

        # Insert or replace
        cursor.execute("""
            INSERT OR REPLACE INTO user_passes
            (token, expiration_timestamp, pass_type, purchase_date, order_id)
            VALUES (?, ?, ?, ?, ?)
        """, (token, new_expiration, pass_type, now, order_id))

        conn.commit()
        return True
    finally:
        conn.close()

def get_active_pass(token: str) -> Optional[dict]:
    """Check if user has active pass. Returns pass details or None."""
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
        return {
            'expiration_timestamp': row[0],
            'pass_type': row[1],
            'purchase_date': row[2]
        }
    return None

def get_daily_usage(token: str) -> int:
    """Get today's citation count for user."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = datetime.utcnow().strftime('%Y-%m-%d')
    cursor.execute(
        "SELECT citations_count FROM daily_usage WHERE token = ? AND date = ?",
        (token, today)
    )

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else 0

def increment_daily_usage(token: str, citation_count: int):
    """Increment today's usage counter."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = datetime.utcnow().strftime('%Y-%m-%d')
    cursor.execute("""
        INSERT INTO daily_usage (token, date, citations_count)
        VALUES (?, ?, ?)
        ON CONFLICT(token, date) DO UPDATE SET
        citations_count = citations_count + excluded.citations_count
    """, (token, today, citation_count))

    conn.commit()
    conn.close()
```

### Updated Endpoints

#### `POST /api/upgrade-event`
```python
@app.post("/api/upgrade-event")
def upgrade_event(request: dict):
    event = request.get('event')
    job_id = request.get('job_id')
    experiment_variant = request.get('experiment_variant')  # NEW

    logger.info(
        f"UPGRADE_WORKFLOW | job_id={job_id} | event={event} | "
        f"experiment_variant={experiment_variant}"
    )

    return {"status": "ok"}
```

#### `POST /api/create-checkout`
```python
@app.post("/api/create-checkout")
def create_checkout(request: dict):
    token = request.get('token')
    product_id = request.get('product_id')  # NEW (dynamic)
    experiment_variant = request.get('experiment_variant')  # NEW

    # Validate product exists
    from pricing_config import PRODUCT_CONFIG
    if product_id not in PRODUCT_CONFIG:
        raise HTTPException(status_code=400, detail="Invalid product_id")

    # Generate token if needed
    if not token:
        token = str(uuid.uuid4())

    # Create Polar checkout with dynamic product_id
    polar = Polar(access_token=os.getenv('POLAR_ACCESS_TOKEN'))
    checkout_request = {
        "products": [product_id],  # Use dynamic product_id
        "customer_email": None,
        "customer_metadata": {"token": token},
        "success_url": f"{BASE_URL}/success?token={token}",
    }

    checkout = polar.checkouts.create(checkout_request)

    # Log checkout created
    logger.info(
        f"UPGRADE_WORKFLOW | event=checkout_created | "
        f"product_id={product_id} | experiment_variant={experiment_variant} | "
        f"token={token}"
    )

    return {"checkout_url": checkout.url, "token": token}
```

#### `POST /api/polar-webhook` (Updated Handler)
```python
async def handle_checkout_updated(webhook):
    """Handle successful purchase - route to credits or pass grant."""
    if webhook.get('status') != 'completed':
        return

    # Extract customer metadata
    customer_metadata = webhook.get('customer_metadata', {})
    token = customer_metadata.get('token')

    if not token:
        logger.error("No token in webhook customer_metadata")
        return

    # Extract product_id from line items
    line_items = webhook.get('line_items', [])
    if not line_items:
        logger.error("No line items in webhook")
        return

    product_id = line_items[0].get('product_id')
    order_id = webhook.get('order_id')

    # Look up product config
    from pricing_config import PRODUCT_CONFIG
    product_config = PRODUCT_CONFIG.get(product_id)

    if not product_config:
        logger.error(f"Unknown product_id in webhook: {product_id}")
        return

    # Route based on product type
    if product_config['type'] == 'credits':
        amount = product_config['amount']
        success = add_credits(token, amount, order_id)
        logger.info(f"Granted {amount} credits to {token} (order: {order_id})")

    elif product_config['type'] == 'pass':
        days = product_config['days']
        pass_type = f"{days}day"
        success = add_pass(token, days, pass_type, order_id)
        logger.info(f"Granted {days}-day pass to {token} (order: {order_id})")

    else:
        logger.error(f"Unknown product type: {product_config['type']}")
        return

    if not success:
        logger.error(f"Failed to grant access for order {order_id}")
```

---

## Design Section 5: Dashboard Updates

### Files to Modify

1. **`backend/dashboard/log_parser.py`**
   - Add regex patterns to extract `experiment_variant` and `product_id` from logs
   - Update database INSERT to include new columns

2. **`backend/dashboard/static/index.html`**
   - Add two new columns to validations table
   - Add display mappings for human-readable values
   - Update job detail modal to show new fields

### Display Mappings (JavaScript)

```javascript
const VARIANT_DISPLAY = {
    '1': 'Credits',
    '2': 'Passes',
    null: 'Not Assigned'
};

const PRODUCT_DISPLAY = {
    'prod_credits_100': '100 Credits ($1.99)',
    'prod_credits_500': '500 Credits ($4.99)',
    'prod_credits_2000': '2000 Credits ($9.99)',
    'prod_pass_1day': '1-Day Pass ($1.99)',
    'prod_pass_7day': '7-Day Pass ($4.99)',
    'prod_pass_30day': '30-Day Pass ($9.99)',
};

// In table rendering:
<td>${VARIANT_DISPLAY[row.experiment_variant] || 'N/A'}</td>
<td>${PRODUCT_DISPLAY[row.product_id] || 'N/A'}</td>
```

---

## Design Section 6: Implementation Plan

### Phase 1: Database Foundation

**What:** Schema changes, no user-facing changes

**Steps:**
1. Create `backend/pricing_config.py` with placeholder product IDs
2. Write migration script: `backend/migrations/add_pricing_tables.py`
3. Add database functions to `backend/database.py`

**Tests:**
- Pass expiration calculations
- Pass extension logic
- Daily usage increments
- Idempotency

**Deployment:**
1. Run migration locally
2. Ask user to approve production migration
3. SSH to prod, run migration
4. DO NOT deploy code yet

---

### Phase 2: Frontend Foundation

**What:** Install shadcn, build pricing components (not wired up)

**Steps:**
1. Install Tailwind + shadcn
2. Ask user for brand colors/fonts
3. Create pricing table components
4. Style components

**Tests:**
- Component rendering
- Button click handlers
- Visual regression

**Deployment:**
- Build locally
- DO NOT deploy yet

---

### Phase 3: Experiment Tracking Infrastructure

**What:** Wire up variant assignment and logging (backward compatible)

**Steps:**
1. Update backend endpoints to accept experiment_variant
2. Update frontend to determine variant and pass to API calls
3. Update dashboard parsing and display

**Tests:**
- Variant assignment is sticky
- Log parser extracts fields
- E2E test: Upgrade flow logs variant
- Dashboard shows new columns

**Deployment:**
- Deploy backend + frontend together
- Verify existing $8.99 flow still works

---

### Phase 4: Multi-Product Checkout

**What:** Enable multiple products and webhook routing

**Steps:**
1. Ask user for 6 Polar product IDs
2. Update pricing_config.py with real IDs
3. Update create-checkout endpoint to accept product_id
4. Update webhook to route based on product type
5. Update UpgradeModal to show pricing tables
6. Add success page logging

**Tests:**
- Checkout validates product_id
- Webhook routes correctly (credits vs pass)
- Idempotency
- E2E purchase flows (mocked Polar)

**Deployment:**
- Deploy backend + frontend together
- Verify with real test purchase

---

### Phase 5: Access Control & Limit Messaging

**What:** Enforce pass limits, show contextual messages

**Steps:**
1. Update validation endpoint access control
2. Update PartialResults to pass limit_type
3. Update UpgradeModal with contextual messages
4. Create pass status utilities

**Tests:**
- Pass users within daily limit
- Pass users exceeding daily limit
- Expired pass users
- E2E daily limit messaging

**Deployment:**
- Deploy backend + frontend together
- Create test pass user and verify

---

### Phase 6: Counter Display Update

**What:** Show "Active Pass" for pass users

**Steps:**
1. Create GET /api/user-status endpoint
2. Update CreditDisplay component

**Tests:**
- Pass users see "Active Pass"
- Credit users see credit count

**Deployment:**
- Deploy backend + frontend together

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| **Pass expiration calculation bug** | Comprehensive unit tests for all duration scenarios |
| **Daily limit reset timing issues** | Use UTC consistently, test midnight boundary |
| **Webhook idempotency failure** | Test duplicate delivery, verify order_id checking |
| **Variant assignment inconsistent** | Test localStorage persistence and edge cases |
| **Polar product ID mismatch** | Validate all IDs before deployment |

---

## Rollback Plan

**Phase 3-4 (Tracking/Multi-Product):**
- Revert to single $8.99 product
- Keep database tables (no data loss)
- Disable variant assignment

**Phase 5 (Access Control):**
- Disable pass checking
- Fall back to credits-only

**Database Rollback:**
```sql
DROP TABLE user_passes;
DROP TABLE daily_usage;
ALTER TABLE validations DROP COLUMN experiment_variant;
ALTER TABLE validations DROP COLUMN product_id;
```

---

**End of Design Document**

## Relevant Context

**Tech Stack:**
- Backend: Python 3.x, FastAPI, SQLite
- Frontend: React 19, Vite 7
- Payments: Polar SDK
- Current pricing: Single $8.99/1000 credits option

**Current Architecture:**
- Async polling for validations (job-based)
- In-memory job storage (30min TTL)
- Credits stored in SQLite, deducted per citation
- Upgrade funnel tracking via app.log parsing → dashboard

**Constraints:**
- Must maintain backward compatibility during rollout
- Phased deployment (6 phases)
- Test environment uses Polar webhook mocking
- Production has single VPS, systemd services

## Supporting Information

The design went through collaborative brainstorming with the following key decisions:
1. Variant assignment timing: On upgrade click (not validation)
2. Pass + credits behavior: Pass checked first, credits as fallback
3. Pass renewal: Extend expiration for same type
4. Daily limit: 1000 citations/day for pass users
5. Polar testing: Mock checkout creation, real webhook handler testing
6. Counter display: Simple "Active Pass" text (not countdown timer)

Please provide your concrete feedback on this design.
