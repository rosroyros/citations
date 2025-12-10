# Beads Issue Structure - Phases 2-6

**Created:** 2025-12-10
**Status:** Implementation Guide
**Parent Epic:** citations-z6w3
**Phase 1 (Complete):** citations-69b7

---

## Overview

This document provides the complete beads issue structure for Phases 2-6 of the Pricing Model A/B Test implementation.

**Rationale for Document Instead of Script:**
Due to the comprehensive nature (50+ tasks with detailed descriptions, dependencies, and context), creating all issues via script would be:
1. Time-consuming to execute
2. Harder to review before creation
3. Risk of errors requiring cleanup

**Usage:**
Use this as a reference to create issues on-demand as you progress through phases. Each phase can be created when the previous phase nears completion.

---

## Phase 2: Frontend Foundation (shadcn/ui + Components)

**Phase Issue:** citations-XXXX (create with bd)
**Duration:** 2 days
**Blocks:** Phase 1 complete (citations-69b7)
**Success Criteria:**
- Tailwind + shadcn installed
- All component tests pass
- Visual regression screenshots generated
- Build succeeds, components ready for Phase 3

### Phase 2 Tasks

#### P2.1: Install Tailwind CSS and shadcn/ui
```bash
bd create "P2.1: Install Tailwind CSS and shadcn/ui" -t task -p 1 -d "..."
```

**Description:**
```
## What
Install and configure Tailwind CSS + shadcn/ui in frontend/frontend.

## Steps
cd frontend/frontend
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
# Edit tailwind.config.js: content paths
# Add @tailwind directives to src/index.css
npx shadcn@latest init
npx shadcn@latest add card button

## Verification
- npm run build succeeds
- shadcn components in src/components/ui/

## Time: 1 hour
## Dependencies: None
```

#### P2.2: Get brand colors/fonts from user
```
## What
Ask user for brand colors to apply to pricing tables.

## Question
"What brand colors should I use for pricing tables?
- Primary color (recommended tier border/button): [hex]
- Success color (checkmarks): [hex]
- Text colors (heading, body): [hex, hex]
- Font family (optional)"

## Output
Store in tailwind.config.js theme.extend

## Time: Blocked until user responds
## Dependencies: P2.1 (shadcn installed)
```

#### P2.3: Create PricingTableCredits and PricingTablePasses
```
## What
Build two pricing table components using shadcn Card + Button.

## PricingTableCredits (Variant 1)
- 3 tiers: 100/$1.99, 500/$4.99, 2000/$9.99
- Middle tier "Best Value"
- Price per citation shown
- Benefits list with checkmarks
- "Buy X Credits" button

## PricingTablePasses (Variant 2)
- 3 tiers: 1-day/$1.99, 7-day/$4.99, 30-day/$9.99
- Middle tier "Recommended"
- Price per day shown
- "Unlimited validations" messaging
- "Up to 1,000 citations/day" fair use notice
- "Buy X-Day Pass" button

## Props
Both accept:
- onSelectProduct(product_id, experiment_variant)
- experimentVariant ('1' or '2')

## Design
- Responsive grid (1 col mobile, 3 desktop)
- Recommended tier: blue border + shadow
- Green checkmarks for benefits
- Brand colors applied

## Full code in design doc

## Time: 4 hours
## Dependencies: P2.2 (brand colors obtained)
```

#### P2.4: Create experimentVariant.js and passStatus.js utilities
```
## What
Frontend utilities for variant assignment and time calculations.

## experimentVariant.js
- getExperimentVariant() - returns '1' or '2', sticky via localStorage
- getVariantName(variantId) - human-readable name
- resetExperimentVariant() - for testing

Oracle #5: Assign on upgrade click (not validation) to measure
"pricing table shown → conversion" for both variants.

## passStatus.js
- formatPassExpiration(timestamp) - "Expires in 2 days"
- getHoursUntilReset(timestamp) - hours until midnight UTC
- formatDailyLimitMessage(timestamp) - full message

Oracle #3: Use Unix timestamps everywhere (no date strings).

## Time: 1 hour
## Dependencies: None
```

#### P2.5: Write component and visual regression tests
```
## What
Unit tests (Vitest) + visual regression (Playwright).

## Unit Tests
- PricingTableCredits.test.jsx: renders tiers, calls handler correctly
- PricingTablePasses.test.jsx: similar coverage
- experimentVariant.test.js: sticky assignment, returns '1' or '2'
- passStatus.test.js: time formatting works

## Visual Regression
Create test pages: /test/pricing-credits, /test/pricing-passes
Take screenshots with Playwright:
await expect(page).toHaveScreenshot('pricing-credits.png')

## Coverage
- Components: 90%
- Utils: 100%

## Time: 3 hours
## Dependencies: P2.3, P2.4 (components + utils created)
```

#### P2.6: Verify frontend build (do not deploy)
```
## What
Run production build locally. Verify no errors.

## Commands
cd frontend/frontend
npm run build

## Verify
- Build completes
- No TypeScript warnings
- dist/ created
- Components unused in production (not deployed yet)

## Time: 15 min
## Dependencies: P2.5 (all tests passing)
```

---

## Phase 3: Tracking Infrastructure

**Phase Issue:** citations-YYYY
**Duration:** 1 day
**Blocks:** Phase 2 complete
**Success Criteria:**
- Existing $8.99 flow unchanged
- New upgrade clicks assign variant
- Variant logged in app.log
- Dashboard shows new columns
- E2E tests pass

### Phase 3 Tasks

#### P3.1: Update backend endpoints for experiment tracking
```
## What
Update endpoints to accept experiment_variant parameter.

## Changes
POST /api/upgrade-event:
  - Accept experiment_variant (default 'not_assigned')
  - Log: UPGRADE_WORKFLOW | ... | experiment_variant=X

POST /api/create-checkout:
  - Accept experiment_variant and product_id
  - Fall back to env var POLAR_PRODUCT_ID if not provided
  - Log checkout_created event

Oracle #11: Backward compatible - old frontend won't break.

## Time: 2 hours
## Dependencies: None (backend-only)
```

#### P3.2: Wire up variant assignment in UpgradeModal
```
## What
Update frontend UpgradeModal to determine variant and pass to API calls.

## Changes
- Import getExperimentVariant()
- Determine variant when modal opens
- Pass variant to all /api/upgrade-event calls
- Pass variant to /api/create-checkout

## Important
Don't show pricing tables yet - keep existing $8.99 modal.
This phase only adds tracking.

## Time: 2 hours
## Dependencies: P2.4 (experimentVariant.js created)
```

#### P3.3: Update dashboard log parser
```
## What
Extend dashboard/log_parser.py to extract new fields.

## Add regex patterns
- EXPERIMENT_VARIANT_PATTERN = r'experiment_variant=([12]|not_assigned)'
- PRODUCT_ID_PATTERN = r'product_id=(prod_\w+)'

## Update parsing
Extract from UPGRADE_WORKFLOW logs, store in validations table.

## Time: 2 hours
## Dependencies: None
```

#### P3.4: Update dashboard UI with new columns
```
## What
Add columns to dashboard/static/index.html.

## Display mappings
VARIANT_DISPLAY = {
    '1': 'Credits',
    '2': 'Passes',
    'not_assigned': 'Not Assigned',
    null: 'N/A'
};

PRODUCT_DISPLAY = {
    'prod_credits_100': '100 Credits ($1.99)',
    // ... etc
};

## Add columns
<th>Experiment Variant</th>
<th>Product</th>

In rendering:
<td>${VARIANT_DISPLAY[row.experiment_variant]}</td>
<td>${PRODUCT_DISPLAY[row.product_id]}</td>

## Time: 2 hours
## Dependencies: None
```

#### P3.5: Write E2E test for variant tracking
```
## What
Playwright test: upgrade click → variant assigned → logged.

## Test
1. Clear localStorage
2. Submit validation → hit limit
3. Click upgrade button
4. Verify localStorage has experiment_v1 = '1' or '2'
5. Verify modal opened
6. Verify variant sticky across multiple opens

## Time: 2 hours
## Dependencies: P3.2 (frontend changes)
```

#### P3.6: Deploy Phase 3 (backend + frontend together)
```
## What
Deploy tracking infrastructure.

## Steps
1. Commit backend + frontend changes
2. git push origin main
3. ./deploy_prod.sh

## Verify in Production
- Test existing $8.99 purchase (should still work)
- Check logs show experiment_variant=not_assigned for old flow
- Clear localStorage, click upgrade
- Check localStorage has experiment_v1
- Check app.log shows experiment_variant=1 or 2
- Check dashboard shows new columns (empty for old jobs)

## Time: 1 hour
## Dependencies: P3.5 (tests passing)
```

---

## Phase 4: Multi-Product Checkout

**Phase Issue:** citations-ZZZZ
**Duration:** 2 days
**Blocks:** Phase 3 complete
**Success Criteria:**
- Product validation script passes
- All unit tests pass
- E2E purchase flows work
- Real test purchase succeeds in prod
- Webhook logs show product_id + revenue

### Phase 4 Tasks

#### P4.1: Ask user for 6 Polar product IDs
```
## What
Request real Polar product IDs from user.

## Message to User
"Please provide the 6 Polar product IDs:
- 100 credits: [prod_xxx]
- 500 credits: [prod_xxx]
- 2000 credits: [prod_xxx]
- 1-day pass: [prod_xxx]
- 7-day pass: [prod_xxx]
- 30-day pass: [prod_xxx]

Important: Name these in Polar dashboard as:
- '100 Credits - $1.99'
- '500 Credits - $4.99'
etc. for easier debugging."

## Time: Blocked until user responds
## Dependencies: None
```

#### P4.2: Update pricing_config.py with real Polar IDs
```
## What
Replace placeholder product IDs with real ones from P4.1.

## Time: 10 min
## Dependencies: P4.1
```

#### P4.3: Create product validation script
```
## What
Create backend/validate_polar_products.py

## Script Purpose
Verify all product IDs exist in Polar + prices match.

## Implementation
For each product in PRODUCT_CONFIG:
  - Call polar.products.get(product_id)
  - Verify price matches config
  - Print success/failure

Exit code 1 if any invalid.

Oracle #9: Must run and pass before Phase 4 deployment.

## Time: 30 min
## Dependencies: P4.2
```

#### P4.4: Update create-checkout endpoint
```
## What
Modify POST /api/create-checkout to accept dynamic product_id.

## Changes
- Require product_id parameter
- Validate against PRODUCT_CONFIG
- Use dynamic product_id for Polar API (not env var)
- Backward compatible: fall back to env var if missing

## Time: 1 hour
## Dependencies: None
```

#### P4.5: Update webhook handler for routing
```
## What
Modify handle_checkout_updated() to route based on product type.

## Logic
1. Extract product_id from line_items
2. Look up in PRODUCT_CONFIG
3. Route: type='credits' → add_credits(), type='pass' → add_pass()
4. Log revenue (Oracle #16): amount_cents from webhook

## Oracle #16: Revenue Tracking
Log amount_cents for future revenue dashboards:
logger.info(f"PURCHASE_COMPLETED | ... | revenue=${amount_cents/100:.2f}")

## Time: 2 hours
## Dependencies: None
```

#### P4.6: Update UpgradeModal to show pricing tables
```
## What
Replace hardcoded $8.99 content with dynamic pricing tables.

## Changes
- Remove old content
- Show PricingTableCredits if variant='1'
- Show PricingTablePasses if variant='2'
- Wire up onSelectProduct handler → calls /api/create-checkout

## Time: 2 hours
## Dependencies: P2.3 (pricing tables created)
```

#### P4.7: Add success page logging with product_id
```
## What
Update src/pages/Success.jsx to log success_page event.

## Implementation
useEffect(() => {
  const params = new URLSearchParams(window.location.search);
  const product_id = params.get('product_id');
  const variant = localStorage.getItem('experiment_v1');

  fetch('/api/upgrade-event', {
    method: 'POST',
    body: JSON.stringify({
      event: 'success_page',
      product_id,
      experiment_variant: variant
    })
  });
}, []);

## Time: 30 min
## Dependencies: None
```

#### P4.8: Write webhook and checkout tests
```
## What
Unit tests for webhook routing and checkout validation.

## Tests
- Checkout validates product_id (400 if invalid)
- Checkout creates Polar link with correct product
- Webhook routes credits products → add_credits()
- Webhook routes pass products → add_pass()
- Webhook idempotent (same order_id twice = single grant)

## Time: 4 hours
## Dependencies: P4.4, P4.5
```

#### P4.9: Write E2E purchase flow tests
```
## What
Playwright tests for complete purchase flows (mocked Polar).

## Tests
1. Credits purchase: upgrade → see credits table → select 500 → checkout
2. Passes purchase: upgrade → see passes table → select 7-day → checkout
3. Mock webhook → verify credits/pass granted

## Time: 3 hours
## Dependencies: P4.6
```

#### P4.10: Run product validation, deploy Phase 4
```
## What
Validate products, deploy, test in production.

## Pre-Flight
1. python3 backend/validate_polar_products.py
   Must show ✅ for all products
2. All tests pass

## Deploy
git push origin main
./deploy_prod.sh

## Verify in Production
- Clear localStorage
- Click upgrade → should see pricing table
- Purchase smallest tier ($1.99)
- Check webhook log in app.log
- Verify credits or pass granted:
  ssh deploy@178.156.161.140
  sqlite3 credits.db "SELECT * FROM credits WHERE token='test_token';"
  sqlite3 credits.db "SELECT * FROM user_passes WHERE token='test_token';"

## Time: 2 hours
## Dependencies: P4.3, P4.8, P4.9 (validation + tests passing)
```

---

## Phase 5: Access Control & Limit Messaging

**Phase Issue:** citations-AAAA
**Duration:** 2 days
**Blocks:** Phase 4 complete
**Success Criteria:**
- Pass users validate up to 1000/day
- Daily limit rejection shows helpful message
- Expired passes trigger appropriate modal
- Credits don't kick in when pass hits limit
- All tests pass

### Phase 5 Tasks

#### P5.1: Implement check_user_access() function
```
## What
Create backend function to check access in priority order: pass > credits > free.

## Returns
{
    'allowed': int,  # 0 to citation_count
    'limit_type': str,
    'daily_remaining': int,
    'pass_info': dict,
    'credits_remaining': int
}

## Oracle #2: Reject if request exceeds daily remaining
If pass user has 50 citations left but requests 100:
- Return allowed=0, limit_type='daily_limit_insufficient'
- Don't process partial (reject entire request)

## Oracle #14: Credits don't kick in
If pass user hits daily limit, they're blocked (no fallback to credits).

## Time: 2 hours
## Dependencies: P1.3 (DB functions exist)
```

#### P5.2: Update validation endpoint access control
```
## What
Integrate check_user_access() into POST /api/validate/async.

## Logic
1. Call check_user_access(token, citation_count)
2. If limit_type='daily_limit_insufficient':
   Return 400 with helpful message
3. Process access['allowed'] citations
4. If pass user: atomically increment daily usage after success

## Time: 3 hours
## Dependencies: P5.1
```

#### P5.3: Update validation response with user_status
```
## What
Add user_status to response (Oracle #8: don't create separate endpoint).

## Response Format
{
    "results": [...],
    "limit_type": "none" | "daily_limit" | "credits_exhausted" | ...,
    "user_status": {
        "type": "pass" | "credits" | "free",
        // If pass:
        "pass_type": "7day",
        "expiration_timestamp": 1234567890,
        "hours_remaining": 48,
        "daily_remaining": 850,
        // If credits:
        "credits_remaining": 500
    }
}

## Time: 1 hour
## Dependencies: P5.2
```

#### P5.4: Update PartialResults to pass limit context
```
## What
Update PartialResults component to extract and pass limit info.

## Changes
Extract from response:
- limit_type
- user_status
- reset_timestamp (if daily_limit)
- daily_remaining (if insufficient)

Pass to onUpgrade() handler.

## Time: 1 hour
## Dependencies: None (frontend-only)
```

#### P5.5: Update UpgradeModal with contextual messaging
```
## What
Implement full modal logic for all limit types.

## Scenarios
1. daily_limit_insufficient: Message + close button (no pricing)
2. daily_limit: Reset time message + close button (no pricing)
3. pass_expired: Message + passes pricing table
4. credits_exhausted: Message + variant pricing table
5. free_limit: Variant pricing table

## Oracle #2: Helpful message
"You have 50 citations remaining today. Please reduce your request to 50 citations or less."

## Time: 2 hours
## Dependencies: P5.4
```

#### P5.6: Update CreditDisplay with user_status
```
## What
Use user_status from validation response to show pass/credits info.

## Oracle #7: Show detailed expiration
- Pass users: "Expires in 2 days" + "850/1000 today"
- Credit users: "500 Credits"
- Free users: "3/5 Free Validations"

## Time: 1 hour
## Dependencies: P2.4 (passStatus.js)
```

#### P5.7: Write access control tests
```
## What
Unit tests for all access scenarios.

## Tests
- Pass user within daily limit → succeeds
- Pass user exceeds daily limit → entire request rejected
- Pass user requests more than remaining → rejected with message
- Expired pass → treated as free user
- Pass + credits: daily limit hit → credits NOT used

## Time: 4 hours
## Dependencies: P5.2
```

#### P5.8: Write E2E limit messaging tests
```
## What
Playwright tests for UI messaging.

## Tests
- Daily limit insufficient → shows message with remaining count
- Daily limit hit → shows reset time, no pricing
- Expired pass → shows passes pricing table

## Time: 2 hours
## Dependencies: P5.5
```

#### P5.9: Load test SQLite concurrency (Oracle #10)
```
## What
Load test with 100 concurrent requests before prod deploy.

## Setup
Create locustfile.py:
- 100 virtual users
- Each submits validations
- Monitor for SQLITE_BUSY errors

## Oracle #10: Verify
- WAL mode enabled
- busy_timeout=5000 set
- No BUSY errors under load
- Response times < 2s

## Time: 2 hours
## Dependencies: P5.2 (access control implemented)
```

#### P5.10: Deploy Phase 5, create test pass user
```
## What
Deploy access control, verify with test pass user.

## Deploy
git push origin main
./deploy_prod.sh

## Create Test User
ssh deploy@178.156.161.140
cd /opt/citations/backend
sqlite3 credits.db "INSERT INTO user_passes ..."

## Verify
- Navigate with ?token=test_pass_user
- Submit validations
- Hit daily limit
- Verify messaging appears correctly

## Time: 1 hour
## Dependencies: P5.7, P5.8, P5.9 (tests + load test passing)
```

---

## Phase 6: UI Polish

**Phase Issue:** citations-BBBB
**Duration:** 1 day
**Blocks:** Phase 5 complete
**Success Criteria:**
- Pass counter shows expiration countdown
- Pricing tables polished on all screen sizes
- Success page shows purchase confirmation
- All E2E tests pass
- A/B test fully functional

### Phase 6 Tasks

#### P6.1: Polish CreditDisplay with pass expiration
```
## What
Finalize CreditDisplay to show detailed pass info.

## Display
- Pass users: formatPassExpiration(timestamp)
  "Expires in 2 days" or "Expires in 8 hours"
- Daily usage: "850/1000 today"
- Credit users: "500 Credits"

## Time: 1 hour
## Dependencies: P5.6 (basic implementation done)
```

#### P6.2: Final pricing table styling
```
## What
Apply final brand colors, ensure responsive, add polish.

## Tasks
- Apply brand colors from P2.2
- Test on mobile, tablet, desktop
- Add hover states, transitions
- Fix spacing/alignment issues
- Ensure accessibility (focus states, ARIA)

## Time: 2 hours
## Dependencies: P2.2 (brand colors obtained)
```

#### P6.3: Add loading states to checkout flow
```
## What
Show spinners, disable buttons during loading, handle errors.

## Implementation
- Show spinner while creating checkout link
- Disable buttons to prevent double-click
- Display errors gracefully (network failure, etc.)

## Time: 1 hour
## Dependencies: None
```

#### P6.4: Success page improvements (Oracle #23)
```
## What
Show what was purchased on success page.

## Implementation
const productId = new URLSearchParams(window.location.search).get('product_id');
const product = PRODUCT_CONFIG[productId];

<h1>Purchase Successful!</h1>
<p>✓ {product.display_name} added to your account!</p>

## Time: 1 hour
## Dependencies: None
```

#### P6.5: Final E2E test suite
```
## What
Complete E2E tests for all flows, all screen sizes.

## Tests
- Complete purchase flows (both variants)
- All limit scenarios
- Mobile responsive tests
- Success page confirmation
- Variant assignment persistence

## Time: 2 hours
## Dependencies: P6.1, P6.2, P6.3, P6.4
```

#### P6.6: Deploy Phase 6, final verification
```
## What
Deploy UI polish, verify everything works.

## Deploy
git push origin main
./deploy_prod.sh

## Final Verification Checklist
- [ ] Pass users see expiration countdown
- [ ] Pricing tables look polished (all devices)
- [ ] Loading states work
- [ ] Success page shows purchase details
- [ ] Both variants work (test each)
- [ ] Dashboard shows variant data
- [ ] All E2E tests pass
- [ ] Can measure conversion by variant

## Time: 1 hour
## Dependencies: P6.5 (all tests passing)
```

---

## Post-Launch Monitoring

After Phase 6 deployment, monitor for 1-2 weeks:

### Week 1 (Critical)
- Check dashboard daily for experiment data
- Monitor webhook logs for grant failures
- Verify both variants receiving ~50/50 traffic
- Check for user-reported payment issues
- Monitor SQLite performance (no BUSY errors)

### Week 2-4 (Analysis)
- Analyze conversion rates by variant
- Identify most popular product tiers
- Monitor pass renewal behavior
- Check daily limit enforcement
- Calculate revenue by variant

### Alerts to Set Up
- Webhook processing failures
- SQLite BUSY errors
- Unexpected daily usage spikes
- Product ID mismatches

---

## Quick Reference: Issue Creation Commands

### Create Phase 2
```bash
source /tmp/pricing_ids.txt

PHASE2=$(bd create "Phase 2: Frontend Foundation" -t feature -p 1 -d "[description]" --json | jq -r '.id')
bd dep add $PHASE2 $PHASE1 --type "blocks"

# Then create P2.1 through P2.6 with dependencies
```

### Create Phase 3
```bash
PHASE3=$(bd create "Phase 3: Tracking Infrastructure" -t feature -p 1 -d "[description]" --json | jq -r '.id')
bd dep add $PHASE3 $PHASE2 --type "blocks"

# Then create P3.1 through P3.6
```

### Dependency Patterns
```bash
# Task depends on previous task
bd dep add $CURRENT_TASK $PREVIOUS_TASK --type "blocks"

# Task discovered during work
bd dep add $NEW_TASK $CURRENT_TASK --type "discovered-from"

# Related but not blocking
bd dep add $TASK_A $TASK_B --type "related"
```

### View Structure
```bash
bd dep tree citations-z6w3  # View entire epic tree
bd show citations-69b7      # View Phase 1 details
bd list --status open       # See all open tasks
```

---

**End of Beads Structure Guide**

Use this document to create issues as needed during implementation. Start with Phase 1 (already created: citations-69b7), then create subsequent phases when ready.
