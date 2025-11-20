# Free Tier Paywall Design

**Date:** 2025-11-20
**Status:** Design Review
**Related Issue:** citations-rif

## Problem Statement

### Current Bugs

1. **Backend doesn't enforce free tier limit** - Returns all results for free users regardless of count
2. **Frontend doesn't send usage info** - No `X-Free-Used` header sent to backend
3. **Partial results don't increment counter** - When backend returns partial results, frontend never updates localStorage
4. **No sync between frontend/backend** - Backend doesn't return authoritative count back to frontend

### Impact

Users can bypass the 10 citation limit entirely:
- Fresh user submits 100 citations → gets all 100 free
- Or: User submits 8 citations repeatedly, getting 5-10 each time, infinitely
- Result: Unlimited LLM costs, no conversion to paid tier

## Solution Overview

### Architecture

**Backend as source of truth:**
- Frontend sends current usage via base64-encoded header
- Backend enforces 10 citation limit
- Backend returns authoritative count to sync frontend
- Partial results pattern matches paid tier behavior

**Conversion strategy:**
- Process ALL citations (even over limit)
- Return first N within limit
- Show partial results + locked teaser
- Drive upgrades via FOMO

## Detailed Design

### Data Flow

**Example: User with 5 used submits 8 citations**

1. **Frontend request:**
   - Reads `localStorage.freeUsed = 5`
   - Encodes: `btoa("5")` → `"NQ=="`
   - Sends header: `X-Free-Used: NQ==`

2. **Backend processing:**
   - Decodes header: `base64.b64decode("NQ==")` → `5`
   - Calculates: `affordable = 10 - 5 = 5`
   - Processes all 8 citations via LLM
   - Returns first 5 results
   - Response: `{results: [5 items], partial: true, citations_checked: 5, citations_remaining: 3, free_used_total: 10}`

3. **Frontend handling:**
   - Updates: `localStorage.freeUsed = 10`
   - Displays: 5 results + "🔒 3 more locked - Upgrade to see"
   - Shows PartialResults component with upgrade CTA

### Backend Changes

**File:** `backend/app.py`

**Location:** After LLM validation, around line 287-295

```python
import base64

# In /api/validate endpoint, after validation_results
if not token:
    # Free tier - enforce 10 citation limit
    free_used_header = http_request.headers.get('X-Free-Used', '')
    try:
        free_used = int(base64.b64decode(free_used_header).decode('utf-8'))
    except:
        free_used = 0  # Default if header missing/invalid
        logger.warning("Invalid or missing X-Free-Used header")

    FREE_LIMIT = 10
    citation_count = len(results)
    affordable = max(0, FREE_LIMIT - free_used)

    logger.info(f"Free tier: used={free_used}, submitting={citation_count}, affordable={affordable}")

    if affordable >= citation_count:
        # Under limit - return all results
        return ValidationResponse(
            results=results,
            free_used_total=free_used + citation_count
        )
    else:
        # Over limit - partial results (same as paid tier)
        return ValidationResponse(
            results=results[:affordable],
            partial=True,
            citations_checked=affordable,
            citations_remaining=citation_count - affordable,
            free_used_total=FREE_LIMIT  # Capped at limit
        )
```

**Schema update:**

```python
class ValidationResponse(BaseModel):
    results: list[CitationResult]
    partial: bool = False
    citations_checked: Optional[int] = None
    citations_remaining: Optional[int] = None
    credits_remaining: Optional[int] = None
    free_used_total: Optional[int] = None  # NEW - authoritative count for frontend
```

### Frontend Changes

**File:** `frontend/frontend/src/App.jsx`

**Location 1:** Send header (around line 177-181)

```javascript
// Build headers
const headers = { 'Content-Type': 'application/json' }
if (token) {
  headers['X-User-Token'] = token
} else {
  // Free tier - send usage count
  const freeUsed = getFreeUsage()
  headers['X-Free-Used'] = btoa(String(freeUsed))
}
```

**Location 2:** Sync localStorage (after line 213, before if/else)

```javascript
// After getting data from API
console.log('API response data:', data)

// Sync localStorage with backend's authoritative count
if (data.free_used_total !== undefined) {
  localStorage.setItem('citation_checker_free_used', String(data.free_used_total))
  console.log(`Updated free usage to: ${data.free_used_total}`)
}

// Handle response (existing code)
if (data.partial) {
  // Partial results (insufficient credits or free limit)
  setResults({ ...data, isPartial: true })
} else {
  // Full results
  setResults(data)
  // ... rest of existing code
}
```

**Location 3:** Remove old increment (line 234-237)

```javascript
// DELETE these lines - now handled by free_used_total sync
// if (!token) {
//   incrementFreeUsage(data.results.length)
// }
```

**Location 4:** Remove pre-check (line 148-153)

```javascript
// DELETE these lines - blocks conversion teaser for users at limit
// if (!token && freeUsed >= 10) {
//   trackEvent('upgrade_modal_shown', { trigger: 'free_limit' })
//   setShowUpgradeModal(true)
//   return
// }
```

**Rationale:** Removing pre-check allows users at limit to see locked results teaser, driving conversions. Trade-off: LLM costs for submissions at limit, but conversion value likely outweighs cost.

## Edge Cases

### Missing/Invalid Header

**Scenario:** User manipulates or clears localStorage
**Behavior:** Backend defaults to `free_used = 0`, allows 10 citations
**Acceptable:** Same as clearing localStorage today

### Citation Count Mismatch

**Scenario:** Frontend counts 8, backend counts 7 (formatting differences)
**Behavior:** Backend count is source of truth
**Impact:** Minor UX surprise, no functional issue

### Partial Results Already Exist

**Scenario:** Paid users already get partial results when credits run out
**Behavior:** Free tier uses identical pattern
**Benefit:** No new UX to design, component already exists

### Base64 Security

**Q:** Can users bypass by sending fake header?
**A:** Yes, but they can also clear localStorage. Both give same result: 10 free citations. Acceptable for free tier.
**Note:** Base64 is obfuscation, not security. Prevents casual DevTools inspection.

## Testing Strategy

### Backend Tests

**File:** `backend/tests/test_free_tier.py` (new)

1. **Test: Free user under limit**
   - Send 5 citations, header `X-Free-Used: MA==` (0)
   - Assert: All 5 results returned, `free_used_total=5`

2. **Test: Free user at limit**
   - Send 2 citations, header `X-Free-Used: OA==` (8)
   - Assert: All 2 results, `free_used_total=10`

3. **Test: Free user over limit**
   - Send 8 citations, header `X-Free-Used: NQ==` (5)
   - Assert: 5 results, `partial=true`, `citations_remaining=3`, `free_used_total=10`

4. **Test: Free user already at limit**
   - Send 5 citations, header `X-Free-Used: MTA=` (10)
   - Assert: 0 results, `partial=true`, `citations_remaining=5`

5. **Test: Missing header**
   - Send 5 citations, no header
   - Assert: All 5 results, `free_used_total=5`

6. **Test: Invalid header**
   - Send 5 citations, header `X-Free-Used: invalid!!!`
   - Assert: All 5 results (defaults to 0), `free_used_total=5`

### Frontend Tests (Playwright E2E)

**File:** `frontend/frontend/tests/e2e/free-tier-paywall.spec.js` (new)

1. **Test: First-time user submits 5 citations**
   - Clear localStorage
   - Submit 5 citations
   - Assert: All 5 results shown
   - Assert: localStorage updated to 5

2. **Test: User with 5 used submits 8 citations**
   - Set localStorage to 5
   - Submit 8 citations
   - Assert: 5 results shown
   - Assert: Partial results banner: "🔒 3 more citations available"
   - Assert: localStorage updated to 10

3. **Test: User at limit tries to submit**
   - Set localStorage to 10
   - Submit 5 citations
   - Assert: 0 results shown
   - Assert: Upgrade modal or partial results with all locked

4. **Test: User submits 100 citations (first time)**
   - Clear localStorage
   - Submit 100 citations
   - Assert: 10 results shown
   - Assert: Partial results: "🔒 90 more citations available"
   - Assert: localStorage = 10

5. **Test: Backend sync overrides frontend**
   - Set localStorage to 3
   - Mock backend returns `free_used_total=7`
   - Assert: localStorage updated to 7 (backend wins)

## Implementation Order

Following TDD approach:

1. **Backend tests** (write failing tests first)
2. **Backend implementation** (make tests pass)
3. **Frontend E2E tests** (write failing tests)
4. **Frontend implementation** (make tests pass)
5. **Manual testing** on localhost
6. **Deploy to production**

## Success Criteria

- [ ] Fresh user submitting 100 citations gets exactly 10 results
- [ ] User cannot bypass limit by repeated submissions
- [ ] Partial results show upgrade teaser
- [ ] localStorage syncs with backend authoritative count
- [ ] All tests pass
- [ ] No regression in paid tier partial results

## Rollback Plan

If critical issues discovered in production:

1. **Quick fix:** Remove backend enforcement, revert to frontend-only check (original buggy state)
2. **Investigate:** Test locally with production data
3. **Deploy fix:** Follow normal deployment process

## Notes

- Uses existing `PartialResults` component - no new UI needed
- Pattern matches paid tier partial results - consistent UX
- Base64 encoding is obfuscation only, not security
- Backend is source of truth for all counting
- LLM processes all citations even over limit (conversion strategy)
