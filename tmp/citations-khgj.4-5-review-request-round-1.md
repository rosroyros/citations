You are conducting a code review.

## Task Context

### Beads Issue IDs: citations-khgj.4 and citations-khgj.5

**citations-khgj.4**: Refactor experimentVariant.js for 4-Variant Scheme
Status: closed
Priority: P1
Type: task
Created: 2025-12-17 14:11
Updated: 2025-12-17 23:23

Description:
## Context
The current experimentVariant.js returns "1" (Credits) or "2" (Passes). We need to expand this to support 4 variants that combine pricing type with display type:
- 1.1 = Credits + Button (current)
- 1.2 = Credits + Inline (test)
- 2.1 = Passes + Button (current)
- 2.2 = Passes + Inline (test)

## Why This Matters
This is the foundation for the entire A/B test. All other frontend changes depend on this utility correctly identifying which variant a user is in.

## Implementation
Modify frontend/frontend/src/utils/experimentVariant.js:

### Constants
```javascript
const VALID_VARIANTS = ["1.1", "1.2", "2.1", "2.2"];
```

### getExperimentVariant()
- If missing or invalid (including old "1"/"2"), assign fresh new variant
- 25% split across all 4 variants

### New Helper Functions
- isInlineVariant(variant): returns true if ends with ".2"
- getPricingType(variant): returns "credits" or "passes"

### Update forceVariant()
- Validate against VALID_VARIANTS
- Update error message for new format

### Update getVariantName()
- Support new format:
  - "1.1" -> "Credits (Button)"
  - "1.2" -> "Credits (Inline)"
  - "2.1" -> "Passes (Button)"
  - "2.2" -> "Passes (Inline)"

## Migration Strategy
Users with old "1" or "2" values get RE-ASSIGNED to one of the 4 new variants randomly. This is intentional - we want fresh 25% splits across all 4.

## Verification
Run: cd frontend/frontend && npm test -- experimentVariant.test.js

## Dependencies
None - this is foundational

## Files
- MODIFY: frontend/frontend/src/utils/experimentVariant.js
- MODIFY: frontend/frontend/src/utils/experimentVariant.test.js

**citations-khgj.5**: Create Shared checkoutFlow.js Utility
Status: closed
Priority: P1
Type: task
Created: 2025-12-17 14:11
Updated: 2025-12-17 23:25

Description:
## Context
Currently, checkout logic lives inside UpgradeModal.jsx. For inline pricing, we need to trigger checkout from PartialResults.jsx without opening a modal. We need shared checkout logic.

## Why This Matters
1. DRY principle - same checkout logic used by both modal and inline
2. Robustness - centralized error handling
3. Maintainability - one place to update checkout behavior

## Implementation
Create frontend/frontend/src/utils/checkoutFlow.js:

Key features:
- Takes productId, experimentVariant, jobId, onError callback
- Tracks "product_selected" event
- Stores job_id in localStorage for success page attribution
- Wraps fetch in try/catch, calls onError on failure
- Redirects to checkout_url on success

## Key Design Decisions
1. onError callback: Allows calling component to handle errors (show message, re-enable button)
2. Stores job_id: For success page attribution
3. Tracks product_selected: Maintains analytics continuity

## ALSO: Update UpgradeModal to Fire pricing_viewed

**Critical for analytics parity**: The plan requires BOTH variants to fire `pricing_viewed`.

**Current state** (lines 41-45):
```javascript
trackEvent("upgrade_modal_shown", {
  experiment_variant: variantId,
  limit_type: limitType
});
```

**Required addition** (add after line 45):
```javascript
// Truthful event for funnel comparison with inline variants
trackEvent("pricing_viewed", {
  variant: variantId,
  interaction_type: "active"  // User actively clicked to see this
});
```

This ensures fair comparison: both variants fire pricing_viewed, but with different interaction_type values.

## Verification
1. Import in UpgradeModal, verify modal still works
2. Check Network tab: pricing_viewed fires with interaction_type="active"
3. Later: Import in PartialResults for inline variant

## Dependencies
None - can be developed in parallel

## Files
- NEW: frontend/frontend/src/utils/checkoutFlow.js
- MODIFY: frontend/frontend/src/components/UpgradeModal.jsx (use new util + add pricing_viewed event)

### What Was Implemented

**citations-khgj.4**: Refactored experimentVariant.js to support 4 variants (1.1, 1.2, 2.1, 2.2) with 25% distribution each. Added helper functions isInlineVariant() and getPricingType(). Implemented migration logic that re-assigns users with old '1'/'2' values to fresh 25% split. Updated all unit tests to cover new variants and migration scenarios. All 23 tests passing.

**citations-khgj.5**: Created new shared utility checkoutFlow.js with initiateCheckout() function that handles product selection tracking, job ID storage, checkout creation, and error handling. Updated UpgradeModal.jsx to use the shared utility and added pricing_viewed event with interaction_type='active' for analytics parity.

### Requirements/Plan

**Key Requirements from Task Descriptions:**
- Support 4 variants combining pricing type (credits/passes) with display type (button/inline)
- 25% split across all 4 variants
- Migration of old '1'/'2' values to new 4-variant scheme (intentional re-assignment)
- Helper functions to check variant type (isInlineVariant, getPricingType)
- Create shared checkout flow utility for both modal and inline pricing
- Add pricing_viewed event with interaction_type='active' to UpgradeModal
- Ensure analytics parity between button and inline variants
- All tests must pass

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: aaf6318dd5b1e66fef5ca8b5026746731c926385
- HEAD_SHA: 366bc522ba5d8f097d69ba106cbde23310947331

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