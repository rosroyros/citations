You are conducting a code review.

## Task Context

### Beads Issue ID: 44xh

citations-44xh: P4.5: Add Polar checkout integration to components
Status: closed
Priority: P1
Type: task
Created: 2025-12-10 22:13
Updated: 2025-12-11 23:27

## Overview

Add Polar SDK checkout integration to pricing components onClick handlers.

**Files:** `PricingTableCredits.jsx`, `PricingTablePasses.jsx`

**Why:** Users need to click tier → open Polar checkout. Currently onClick handlers empty.

## Implementation

1. Install Polar SDK: `npm install @polar-sh/sdk`
2. Import in components: `import { Polar } from '@polar-sh/sdk'`
3. Initialize: `const polar = new Polar({ accessToken: import.meta.env.VITE_POLAR_ACCESS_TOKEN })`
4. Update onClick handlers to call `polar.checkout.create({ productId: tier.productId })`
5. Log events: pricing_table_shown, product_selected, checkout_started
6. Handle loading states and errors

## Success Criteria

- SDK installed
- Checkout opens when clicking tier
- Events logged
- Error handling in place

## Time: 1.5 hours
## Depends on: P4.4 (need productId in tiers)
## Parent: citations-q0cu

## Investigation Results - Security Architecture Review

### Discovery
During code review, we investigated whether Polar access tokens were already exposed in the system.

### Current Production Architecture
1. **Backend** uses secret OAuth Access Token (`polar_oat_...`) securely stored in backend/.env
2. **Frontend** calls `/api/create-checkout` endpoint (see UpgradeModal.jsx:37-41)
3. **Backend** creates Polar checkout using secret token, returns checkout_url
4. **Pattern**: Client never sees Polar token - secure and correct

### Issue with Initial Implementation
Our P4.5 implementation added Polar SDK directly to frontend, which would:
- Expose `VITE_POLAR_ACCESS_TOKEN` in client bundle
- Violate security best practices for OAuth tokens
- Diverge from existing secure architecture

### Revised Implementation Plan
1. Remove Polar SDK from frontend components
2. Follow existing pattern from UpgradeModal.jsx:
   - Frontend calls `/api/create-checkout` with productId
   - Backend validates productId and creates checkout
   - Backend returns checkout_url to client
3. Update backend to accept productId parameter (currently uses single product from env)

### Security Validation
This approach maintains security by:
- Keeping OAuth Access Token server-side only
- Reusing existing proven architecture
- Following principle of least privilege

### What Was Implemented

Round 1: Initially added Polar SDK to frontend with client-side checkout creation.
Round 2 (Current): **SECURITY FIX** - Removed Polar SDK from frontend, now uses secure backend API pattern:
- Frontend calls `/api/create-checkout` with productId (like UpgradeModal.jsx)
- Backend accepts productId and variantId parameters
- OAuth Access Token remains server-side only
- Removed @polar-sh/sdk dependency from frontend
- Maintained loading states and error handling

### Requirements/Plan

Key requirements from task description:
1. Install Polar SDK (@polar-sh/sdk) → REMOVED for security
2. Import Polar in both pricing components → REMOVED for security
3. Initialize Polar with access token from environment → DONE securely on backend
4. Update onClick handlers to call polar.checkout.create() → DONE via backend API
5. Log events (pricing_table_shown, product_selected, checkout_started) ✓
6. Handle loading states and errors ✓
7. Checkout should open when clicking tier ✓

## Code Changes to Review

Review the git changes between these commits:
- BASE_SHA: d984fd8b613b71896a5a6f9b0707790b31d81834
- HEAD_SHA: f54e4c8edd3be7ebc4512b02e2f980c867815998

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

## Special Questions for Oracle

1. **Downstream Impact**: Given that we changed from client-side Polar SDK to backend API calls:
   - Are there any tests that need updating?
   - Will the webhook handlers need any changes?
   - Any analytics or tracking that might be affected?

2. **Architecture Consistency**: Does this implementation match the existing production pattern used by UpgradeModal.jsx?

## Required Output Format

Provide structured feedback in these categories:

1. **Critical**: Must fix immediately (security, broken functionality, data loss)
2. **Important**: Should fix before merge (bugs, missing requirements, poor patterns)
3. **Minor**: Nice to have (style, naming, optimization opportunities)
4. **Strengths**: What was done well
5. **Downstream Issues**: Any systems, tests, or components that will need updates

**IMPORTANT**: Verify implementation matches task requirements above.

Be specific with file:line references for all issues.