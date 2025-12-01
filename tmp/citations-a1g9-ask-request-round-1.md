You are providing technical guidance and problem solving assistance.

## Issue Context
### Beads Issue ID: citations-a1g9

citations-a1g9: Fix gating for partial results - free users see empty results instead of gated overlay
Status: open
Priority: P1
Type: bug
Created: 2025-12-01 11:17
Updated: 2025-12-01 11:17

Description:
## Context
Gating functionality developed in citations-xnp6 is broken in production. Free users who hit their 10-citation limit see empty results instead of the gated blur overlay with "View Results" button that should drive upgrades.

The issue was discovered through systematic debugging after user reported broken gating functionality.

## Requirements
- [ ] Fix backend gating logic to properly handle partial results from limit-reached users
- [ ] Ensure free users at limit see gated blur overlay, not empty results
- [ ] Maintain existing gating behavior for partial results with actual data
- [ ] Test fix end-to-end to ensure upgrade prompt works correctly

## Technical Analysis

### Current Behavior (BROKEN)
```json
// User at limit (10/10) submitting 11 citations:
{
  "results": [],
  "partial": true,
  "citations_checked": 0,
  "citations_remaining": 11,
  "free_used": 10,
  "results_gated": false,  // ❌ SHOULD BE TRUE
}
```

### Expected Behavior (FIXED)
```json
{
  "results": [],           // Empty array (correct)
  "partial": true,         // Partial result (correct)  
  "results_gated": true,   // ✅ SHOULD BE TRUE
  "job_id": "sync_..."
}
```

### Root Cause
File: `backend/gating.py:75-76`
```python
if results.get('isPartial', False):
    logger.debug("Partial results bypass gating")  # ❌ WRONG!
    return False
```

**Problem**: Line 75-76 automatically bypasses gating for ALL partial results, but partial results from limit-reached users SHOULD be gated.

### Frontend Status
✅ Frontend environment restored (`VITE_GATED_RESULTS_ENABLED=true`)
✅ Frontend gating logic active and ready
✅ GatedResults component exists and working
❌ Backend sending `results_gated: false` prevents gating activation

## Implementation Approach

**Minimal Fix Option (Recommended):**
```python
# backend/gating.py:75-76
if results.get('isPartial', False):
    # Only bypass gating if there are actually results being shown
    if results.get('results'):  # Only if results array is not empty
        logger.debug("Partial results with data bypass gating")
        return False
    # If partial but empty results (limit reached), continue to gating logic
```

**Alternative (More Explicit):**
```python
if results.get('isPartial', False):
    # Check if this is a limit-reached scenario (empty results + partial=true)
    if not results.get('results'):
        logger.info("Partial results with no data - applying gating for limit-reached user")
        # Continue to empty results gating logic below
    else:
        logger.debug("Partial results with data bypass gating")
        return False
```

## Verification Criteria
- [ ] Free users at limit see blur overlay instead of empty results
- [ ] Free users under limit see results normally
- [ ] Partial results with actual data (e.g., timeouts) bypass gating
- [ ] "View Results" button appears and functions correctly
- [ ] Reveal tracking analytics work as expected
- [ ] Backend logs show correct gating decisions
- [ ] Frontend environment variables are present and working

## Testing Plan
1. Test free user at limit (10/10) submitting 11+ citations
2. Test free user under limit (9/10) submitting 3 citations
3. Test partial results with actual data (ensure not gated)
4. Verify frontend blur/overlay appears correctly
5. Test reveal button functionality and analytics

## Impact
- **Revenue**: Direct impact on conversion funnel for free tier upgrades
- **User Experience**: Currently broken for free users at limit
- **Priority**: P1 - Core functionality affecting monetization

### Current Status

I've completed systematic debugging of the broken gating functionality. The frontend environment has been restored (VITE_GATED_RESULTS_ENABLED=true), but there's a critical bug in backend/gating.py where all partial results bypass gating automatically. The issue is isolated to lines 75-76 where the logic should distinguish between partial results with actual data vs limit-reached scenarios with empty results.

### The Question/Problem/Dilemma

User wants me to show this problem and solution to Gemini and get feedback on the approach.

I'm seeking technical guidance on:
1. Is the proposed fix approach sound and complete?
2. Are there any edge cases or risks I haven't considered?
3. Which implementation option (minimal fix vs explicit) would you recommend?
4. Any additional logging or monitoring that should be added?
5. Is the testing plan comprehensive enough?

The specific problem is in backend/gating.py where partial results automatically bypass gating, but limit-reached users (empty results + partial=true) SHOULD be gated to show the upgrade prompt.

### Relevant Context

This is a production issue affecting the conversion funnel for a citation validation service. Free users get 10 citations, then should see a gated overlay encouraging upgrade. Currently they see empty results instead, breaking the upgrade flow.

The gating functionality was developed in citations-xnp6 and involves both backend (Python/FastAPI) and frontend (React) components. The frontend side is working correctly after environment restoration.

### Supporting Information

Key files involved:
- `backend/gating.py` - Contains the buggy logic
- `backend/app.py` - Handles validation endpoints and gating response
- `frontend/frontend/src/App.jsx` - Frontend gating logic (now working)
- `frontend/frontend/src/components/GatedResults.jsx` - Gated overlay component

Environment:
- Production VPS with FastAPI backend and React frontend
- Feature flags: GATED_RESULTS_ENABLED=true (backend), VITE_GATED_RESULTS_ENABLED=true (frontend)
- Priority: P1 due to revenue impact

The fix appears to be a few lines of code but has significant business impact.
