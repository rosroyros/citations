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

### Analytics Capabilities

After implementation, dashboard can answer:
- Conversion rate by experiment variant
- Most popular product tiers within each variant
- Revenue by variant (requires price lookup)

---

## Design Section 6: Implementation Plan

### Test Environment Setup

**Local Test Database:**
```bash
# Copy schema to test database
sqlite3 backend/credits.test.db < backend/migrations/add_pricing_tables.sql

# Seed test data
python3 backend/test_data_seed.py
# Creates:
# - User with 100 credits
# - User with active 7-day pass
# - User with expired pass
# - User with pass at 999 citations today (near daily limit)
# - Free user with 4 validations used
```

**Polar Test Setup:**
- Use Polar test mode products
- Create 6 test product IDs (will be provided by user)
- Configure webhook endpoint for local testing (ngrok or similar)

**Test Strategy:**
- ✅ Unit tests: Mock nothing except external Polar API
- ✅ E2E tests: Mock Polar checkout creation, directly POST to webhook handler
- ✅ Manual verification: Real Polar test purchase before production launch

---

### Phase 1: Database Foundation

**What:** Schema changes, no user-facing changes

**Steps:**
1. Create `backend/pricing_config.py` with placeholder product IDs
2. Write migration script: `backend/migrations/add_pricing_tables.py`
3. Add database functions to `backend/database.py`:
   - `add_pass()`
   - `get_active_pass()`
   - `get_daily_usage()`
   - `increment_daily_usage()`

**Tests:**
```python
# test_database_passes.py
def test_add_pass_creates_expiration():
    # Given: Fresh token
    # When: Grant 7-day pass
    # Then: Expiration = now + (7 * 86400)

def test_add_pass_extends_existing():
    # Given: Token with 3 days remaining on 7-day pass
    # When: Grant another 7-day pass
    # Then: Expiration extended by 7 more days (10 total)

def test_add_pass_idempotent():
    # Given: Pass already granted for order_id
    # When: Webhook fires again with same order_id
    # Then: No duplicate pass, returns success

def test_daily_usage_increments_by_citation_count():
    # Given: Token with 50 citations today
    # When: Validate 30 more citations
    # Then: Daily usage = 80

def test_daily_usage_resets_next_day():
    # Given: Token with 500 citations yesterday
    # When: Check usage today
    # Then: Daily usage = 0
```

**Deployment:**
1. Run migration locally: `python3 backend/migrations/add_pricing_tables.py`
2. Verify tables created: `sqlite3 credits.db ".schema"`
3. **ASK USER**: "Ready to run migration in production? This adds new tables but doesn't affect existing data."
4. After approval: SSH to prod, run migration
5. Verify: `ssh deploy@178.156.161.140 "cd /opt/citations/backend && sqlite3 credits.db '.schema user_passes'"`
6. **DO NOT deploy code yet** (tables exist but unused)

---

### Phase 2: Frontend Foundation

**What:** Install shadcn, build pricing components (not wired up)

**Steps:**
1. Install Tailwind + shadcn:
   ```bash
   cd frontend/frontend
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   npx shadcn@latest init
   npx shadcn@latest add card button
   ```

2. **ASK USER**: "Please provide brand colors and fonts for pricing table styling"

3. Create components:
   - `src/components/PricingTableCredits.jsx`
   - `src/components/PricingTablePasses.jsx`
   - `src/utils/experimentVariant.js`
   - `src/utils/passStatus.js`

4. Style components to match brand

**Tests:**
```javascript
// PricingTableCredits.test.jsx
test('renders three pricing tiers', () => {
  render(<PricingTableCredits onSelectProduct={jest.fn()} />)
  expect(screen.getByText('100 Credits')).toBeInTheDocument()
  expect(screen.getByText('500 Credits')).toBeInTheDocument()
  expect(screen.getByText('2000 Credits')).toBeInTheDocument()
})

test('calls onSelectProduct with correct product_id', () => {
  const mockSelect = jest.fn()
  render(<PricingTableCredits onSelectProduct={mockSelect} experimentVariant="1" />)

  fireEvent.click(screen.getByText('Buy 100 Credits'))
  expect(mockSelect).toHaveBeenCalledWith('prod_credits_100', '1')
})

// Visual regression with Playwright
test('pricing table matches design', async ({ page }) => {
  await page.goto('/pricing-preview')
  await expect(page).toHaveScreenshot('pricing-credits.png')
})
```

**Deployment:**
- Build locally: `npm run build`
- Verify no errors
- **DO NOT deploy yet** (components exist but not used)

---

### Phase 3: Experiment Tracking Infrastructure

**What:** Wire up variant assignment and logging (backward compatible)

**Steps:**
1. Update backend endpoints:
   - `POST /api/upgrade-event`: Accept `experiment_variant`
   - `POST /api/create-checkout`: Accept `experiment_variant` and `product_id` (keep backward compatible - if not provided, use env var)

2. Update frontend:
   - `UpgradeModal.jsx`: Determine variant on open, pass to all API calls
   - `PartialResults.jsx`: Pass variant when calling `onUpgrade()`

3. Update dashboard:
   - `log_parser.py`: Extract `experiment_variant` and `product_id`
   - `static/index.html`: Add two new columns with display mappings

**Tests:**
```javascript
// experimentVariant.test.js
test('assigns variant on first call', () => {
  localStorage.clear()
  const variant = getExperimentVariant()
  expect(['1', '2']).toContain(variant)
})

test('variant is sticky across calls', () => {
  localStorage.clear()
  const variant1 = getExperimentVariant()
  const variant2 = getExperimentVariant()
  expect(variant1).toBe(variant2)
})

// E2E test
test('upgrade flow logs experiment variant', async ({ page }) => {
  await page.goto('/')
  // Submit validation that hits limit
  await page.fill('[data-testid="citation-input"]', 'Smith, J. (2020)...')
  await page.click('[data-testid="validate-button"]')

  // Click upgrade
  await page.click('[data-testid="upgrade-button"]')

  // Verify log contains experiment_variant
  // (Check app.log or dashboard API)
})
```

**Deployment:**
1. Deploy backend + frontend together
2. **VERIFY**: Existing $8.99 flow still works
   - Test purchase with old flow
   - Check webhook processes correctly
3. Check dashboard shows new columns (empty for old jobs - expected)
4. Check new upgrade clicks log experiment_variant

---

### Phase 4: Multi-Product Checkout

**What:** Enable multiple products and webhook routing

**Steps:**
1. **ASK USER**: "Please provide 6 Polar product IDs:
   - 100 credits product ID
   - 500 credits product ID
   - 2000 credits product ID
   - 1-day pass product ID
   - 7-day pass product ID
   - 30-day pass product ID"

2. Update `pricing_config.py` with real product IDs

3. Update `POST /api/create-checkout`:
   - Require `product_id` parameter
   - Validate against `PRODUCT_CONFIG`
   - Use dynamic product_id for Polar API

4. Update webhook handler:
   - Extract `product_id` from line items
   - Route to `add_credits()` or `add_pass()`

5. Update `UpgradeModal.jsx`:
   - Show pricing table based on variant
   - Wire up product selection → checkout

6. Add success page logging:
   - Update success page to log with `product_id`

**Tests:**
```python
# test_checkout_multi_product.py
def test_checkout_validates_product_id():
    response = client.post('/api/create-checkout', json={
        'token': 'test123',
        'product_id': 'invalid_product',
        'experiment_variant': '1'
    })
    assert response.status_code == 400

def test_checkout_creates_link_with_correct_product():
    with patch('polar_sdk.Polar') as mock_polar:
        client.post('/api/create-checkout', json={
            'token': 'test123',
            'product_id': 'prod_credits_500',
            'experiment_variant': '1'
        })

        # Verify Polar called with correct product
        mock_polar.return_value.checkouts.create.assert_called_once()
        call_args = mock_polar.return_value.checkouts.create.call_args[0][0]
        assert call_args['products'] == ['prod_credits_500']

# test_webhook_routing.py
def test_webhook_grants_credits_for_credit_product():
    webhook_payload = {
        'status': 'completed',
        'order_id': 'order_123',
        'customer_metadata': {'token': 'user_abc'},
        'line_items': [{'product_id': 'prod_credits_500'}]
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
        'line_items': [{'product_id': 'prod_pass_7day'}]
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
        'line_items': [{'product_id': 'prod_credits_100'}]
    }

    # Send twice
    client.post('/api/polar-webhook', json=webhook_payload)
    client.post('/api/polar-webhook', json=webhook_payload)

    # Verify only granted once
    credits = get_credits('user_123')
    assert credits == 100  # Not 200

# E2E test (mocked Polar)
@pytest.mark.playwright
def test_purchase_flow_credits(page):
    # Navigate to site
    page.goto('http://localhost:5173')

    # Submit validation
    page.fill('[data-testid="citation-input"]', TEST_CITATIONS)
    page.click('[data-testid="validate-button"]')

    # Wait for results
    page.wait_for_selector('[data-testid="partial-results"]')

    # Click upgrade
    page.click('[data-testid="upgrade-button"]')

    # Should see pricing table
    page.wait_for_selector('text=100 Credits')
    page.wait_for_selector('text=500 Credits')

    # Click 500 credits option (mock checkout link)
    with page.expect_navigation():
        page.click('text=Buy 500 Credits')

    # Simulate webhook callback
    requests.post('http://localhost:8000/api/polar-webhook', json={
        'status': 'completed',
        'order_id': 'test_order',
        'customer_metadata': {'token': page.evaluate('() => localStorage.getItem("userToken")')},
        'line_items': [{'product_id': 'prod_credits_500'}]
    })

    # Navigate back and verify credits
    page.goto('http://localhost:5173')
    page.wait_for_selector('text=500 Credits')
```

**Deployment:**
1. Deploy backend + frontend together
2. **VERIFY IN PROD:**
   - Make real test purchase (smallest tier: $1.99)
   - Check webhook log in app.log
   - Verify credits or pass granted in database
   - Check success page logs product_id

---

### Phase 5: Access Control & Limit Messaging

**What:** Enforce pass limits, show contextual messages

**Steps:**
1. Update validation endpoint access control:
   - Check active pass + daily limit before credits
   - Return `limit_type` in response

2. Update `PartialResults.jsx`:
   - Extract `limit_type` from response
   - Pass to `UpgradeModal`

3. Update `UpgradeModal.jsx`:
   - Accept `limitType` prop
   - Render contextual message
   - Show/hide pricing table based on scenario

4. Create `utils/passStatus.js`:
   - `getHoursUntilMidnightUTC()`: Calculate time until reset
   - `formatPassExpiration()`: Human-readable expiration

**Tests:**
```python
# test_access_control.py
def test_pass_user_within_daily_limit():
    # Given: User with active pass, 500 citations today
    token = 'user_with_pass'
    add_pass(token, 7, '7day', 'order_123')
    increment_daily_usage(token, 500)

    # When: Validate 100 citations
    response = client.post('/api/validate/async', json={
        'citations': '\n\n'.join(['Citation text'] * 100)
    }, headers={'X-User-Token': token})

    # Then: Should succeed
    assert response.status_code == 200

def test_pass_user_exceeds_daily_limit():
    # Given: User with active pass, 950 citations today
    token = 'user_with_pass'
    add_pass(token, 7, '7day', 'order_123')
    increment_daily_usage(token, 950)

    # When: Validate 100 citations (would exceed 1000)
    response = client.post('/api/validate/async', json={
        'citations': '\n\n'.join(['Citation text'] * 100)
    }, headers={'X-User-Token': token})

    # Then: Should return partial results
    # Job completes, then check status
    job_id = response.json()['job_id']
    status_response = client.get(f'/api/jobs/{job_id}')

    assert status_response.json()['partial'] == True
    assert status_response.json()['limit_type'] == 'daily_limit'

def test_expired_pass_user():
    # Given: User with expired pass
    token = 'user_expired'
    # Create pass that expired 1 day ago
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    expired_timestamp = int(time.time()) - 86400
    cursor.execute("""
        INSERT INTO user_passes (token, expiration_timestamp, pass_type, purchase_date, order_id)
        VALUES (?, ?, ?, ?, ?)
    """, (token, expired_timestamp, '1day', expired_timestamp - 86400, 'order_old'))
    conn.commit()
    conn.close()

    # When: Validate citations
    response = client.post('/api/validate/async', json={
        'citations': 'Citation text'
    }, headers={'X-User-Token': token})

    # Then: Should treat as free user
    # (No active pass found)

# E2E test
@pytest.mark.playwright
def test_daily_limit_message(page):
    # Setup: Create user at 999 citations today
    token = setup_user_with_daily_usage(999)

    page.goto(f'http://localhost:5173?token={token}')
    page.fill('[data-testid="citation-input"]', TEST_CITATIONS * 10)
    page.click('[data-testid="validate-button"]')

    # Wait for partial results
    page.wait_for_selector('[data-testid="partial-results"]')
    page.click('[data-testid="upgrade-button"]')

    # Should see daily limit message
    page.wait_for_selector('text=You\'ve reached today\'s limit')
    page.wait_for_selector('text=midnight UTC')

    # Should NOT see pricing table
    expect(page.locator('text=Buy 100 Credits')).not_to_be_visible()
```

**Deployment:**
1. Deploy backend + frontend together
2. **VERIFY IN PROD:**
   - Create test pass user (direct DB insert or test purchase)
   - Submit validations up to limit
   - Verify correct messaging appears

---

### Phase 6: Counter Display Update

**What:** Show "Active Pass" for pass users instead of credit count

**Steps:**
1. Create `GET /api/user-status`:
   ```python
   @app.get("/api/user-status")
   def user_status(token: str):
       # Check for active pass
       pass_info = get_active_pass(token)
       if pass_info:
           return {
               'type': 'pass',
               'pass_type': pass_info['pass_type'],
               'expiration': pass_info['expiration_timestamp']
           }

       # Otherwise return credits
       credits = get_credits(token)
       return {
           'type': 'credits',
           'credits': credits
       }
   ```

2. Update `CreditDisplay.jsx`:
   ```jsx
   const { data } = useFetch('/api/user-status', { token })

   return (
     <div>
       {data.type === 'pass' ? (
         <span>Active Pass</span>
       ) : (
         <span>{data.credits} Credits</span>
       )}
     </div>
   )
   ```

**Tests:**
```javascript
test('displays Active Pass for pass users', async () => {
  // Mock API
  global.fetch = jest.fn(() =>
    Promise.resolve({
      json: () => Promise.resolve({ type: 'pass', pass_type: '7day' })
    })
  )

  render(<CreditDisplay token="test_token" />)

  await waitFor(() => {
    expect(screen.getByText('Active Pass')).toBeInTheDocument()
  })
})

test('displays credit count for credit users', async () => {
  global.fetch = jest.fn(() =>
    Promise.resolve({
      json: () => Promise.resolve({ type: 'credits', credits: 500 })
    })
  )

  render(<CreditDisplay token="test_token" />)

  await waitFor(() => {
    expect(screen.getByText('500 Credits')).toBeInTheDocument()
  })
})
```

**Deployment:**
- Deploy backend + frontend together
- Verify pass users see "Active Pass"
- Verify credit users see credit count

---

## Pre-Implementation Checklist

Before starting Phase 1, ensure:

- [ ] 6 Polar product IDs ready (will request during Phase 4)
- [ ] Brand colors/fonts for pricing tables (will request during Phase 2)
- [ ] SSH access to production server for migration
- [ ] Test Polar account configured (optional - can mock instead)
- [ ] All team members aware of phased rollout plan

---

## Success Criteria

**Technical:**
- [ ] All tests passing (unit + E2E)
- [ ] Both variants purchasable in production
- [ ] Webhook correctly grants credits/passes
- [ ] Dashboard shows experiment data
- [ ] No impact to existing $8.99 users during rollout

**Business:**
- [ ] A/B test tracking functional
- [ ] Conversion rates measurable by variant
- [ ] Product tier popularity visible in dashboard
- [ ] Can easily switch "winner" after test concludes

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| **Pass expiration calculation bug** | Comprehensive unit tests for all duration scenarios (1, 7, 30 days) |
| **Daily limit reset timing issues** | Use UTC consistently, test midnight boundary conditions |
| **Webhook idempotency failure** | Test duplicate webhook delivery, verify order_id checking |
| **Variant assignment inconsistent** | Test localStorage persistence, edge cases (cleared storage) |
| **Polar product ID mismatch** | Validate all product IDs exist before deployment |
| **Dashboard columns break existing queries** | Backward compatible schema (nullable columns), test dashboard loads |
| **Users can't purchase with active pass** | Implement pass extension logic (Phase 4) |
| **Rate limit conflicts with free tier** | Separate daily_usage table, test both limits independently |

---

## Rollback Plan

If issues arise after deployment:

**Phase 3-4 (Tracking/Multi-Product):**
- Revert to single $8.99 product
- Keep database tables (no data loss)
- Disable variant assignment (all users see original modal)

**Phase 5 (Access Control):**
- Disable pass checking in validation endpoint
- Fall back to credits-only logic
- Passes remain in database but unused

**Database Rollback:**
```sql
-- If needed, remove new tables (loses pass data)
DROP TABLE user_passes;
DROP TABLE daily_usage;

-- Remove tracking columns (loses experiment data)
ALTER TABLE validations DROP COLUMN experiment_variant;
ALTER TABLE validations DROP COLUMN product_id;
```

---

## Post-Launch Monitoring

**Week 1:**
- Check dashboard daily for experiment data
- Monitor webhook logs for grant failures
- Verify both variants receiving traffic (roughly 50/50)
- Check for any user-reported payment issues

**Week 2-4:**
- Analyze conversion rates by variant
- Identify most popular product tiers
- Monitor pass renewal behavior (extensions)
- Check daily limit enforcement (any abuse?)

**Success Metrics:**
- Conversion rate increase vs. original $8.99 offer
- Average revenue per user by variant
- Purchase frequency (multiple purchases per user)

---

## Future Enhancements (Not in Scope)

- Dynamic pricing based on user behavior
- Subscription model (recurring passes)
- Team/institution pricing
- Volume discounts
- Referral credits
- Pass gifting

---

**End of Design Document**
