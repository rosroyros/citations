
citations-khgj: Inline Pricing A/B Test
Status: open
Priority: P1
Type: epic
Created: 2025-12-17 14:09
Updated: 2025-12-17 14:09

Description:
## Goal
Test whether showing pricing directly (without requiring a button click → modal) improves conversion from locked → purchase.

## Hypothesis
The current flow requires users to: See partial results → Click 'Upgrade' button → See modal with pricing → Select product. The extra click (button → modal) loses users. Eliminating it should improve conversion.

## Background
Production data (Dec 2025) shows:
- 123 users hit paywall (locked)
- Only 13 (10.6%) clicked the upgrade button
- Of those, 3 (23%) proceeded to modal/checkout
- 2-3 successful purchases

The 89% drop from locked → clicked is our biggest leak. This test directly addresses that.

## Variant Scheme
- 1.1: Credits + Button (current behavior)
- 1.2: Credits + Inline pricing (test)
- 2.1: Passes + Button (current behavior)
- 2.2: Passes + Inline pricing (test)

Users are assigned 25% to each variant. Migration: anyone with old '1'/'2' values gets re-assigned.

## Analytics Strategy
We must preserve data integrity. For inline variants:
- Fire 'pricing_viewed' with interaction_type='auto' (TRUTHFUL event)
- Fire 'clicked' with interaction_type='auto' (LEGACY compatibility for existing dashboards)

This lets us maintain funnel charts while enabling accurate future analysis.

## Files Affected
- Frontend: experimentVariant.js, checkoutFlow.js (NEW), PartialResults.jsx, UpgradeModal.jsx
- Backend: app.py (fallback assignment)
- Dashboard: log_parser.py, migrations/
- Tests: experimentVariant.test.js, PartialResults.test.jsx, pricing_variants.spec.cjs, test_upgrade_events.py (NEW)

## Success Criteria
- Inline variants (1.2/2.2) show pricing directly without extra click
- Checkout flow works for both button and inline variants
- Analytics correctly distinguishes passive views from active clicks
- E2E tests pass for all 4 variants
- Rollback plan documented and tested

Labels: [auto-workflow]

Children (11):
  ↳ citations-khgj.1: Create Database Migration for interaction_type Column [P1]
  ↳ citations-khgj.10: Deploy and Verify Inline Pricing A/B Test [P1]
  ↳ citations-khgj.2: Update Log Parser to Extract interaction_type [P1]
  ↳ citations-khgj.4: Refactor experimentVariant.js for 4-Variant Scheme [P1]
  ↳ citations-khgj.5: Create Shared checkoutFlow.js Utility [P1]
  ↳ citations-khgj.6: Implement Inline Pricing in PartialResults.jsx [P1]
  ↳ citations-khgj.9: Add E2E Tests for Inline Pricing Variants [P1]
  ↳ citations-khgj.11: Update Dashboard Funnel Chart for 4 Variants [P2]
  ↳ citations-khgj.3: Add Unit Tests for Upgrade Event Parsing [P2]
  ↳ citations-khgj.7: Add Unit Tests for PartialResults Inline Variants [P2]
  ↳ citations-khgj.8: Update Backend Fallback for 4-Variant Assignment [P2]

