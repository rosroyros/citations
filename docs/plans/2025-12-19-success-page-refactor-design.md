# Success Page Refactor Design

## Problem
The current `Success.jsx` (655 lines) duplicates nearly all of `App.jsx` - the editor, validation form, results display, benefits section, FAQ, and footer. This creates maintenance burden when either file changes.

## Solution
Replace the full-page duplication with a **minimal "handoff" Success page** that handles purchase activation, then redirects to the homepage with a success banner.

## Architecture

### Success Page (Minimal ~100 lines)
**Responsibilities:**
1. Extract `token` and `job_id` from URL params
2. Save token to localStorage, clear free user ID
3. POST to `/api/upgrade-event` with success event
4. Poll `/api/credits` until credits appear (max 30s)
5. Track `purchase` analytics event
6. Redirect to `/?purchased=true`

**UI States:**
- `activating`: Spinner with "Activating your credits..."
- `success`: Brief "Success!" then auto-redirect (1s delay)
- `error`: Warning message + redirect anyway

### Homepage Changes
**When `?purchased=true` is present:**
- Show green success banner at top
- Banner text: "✅ Payment successful! Your credits are ready."
- Dismisses on scroll (existing behavior) or close button
- Does NOT persist across refresh (one-time display)

**If credits took too long (error case):**
- Redirect with `?purchased=pending`
- Show warning banner: "Purchase completed but credits may take a few minutes to appear. Contact support@citationformatchecker.com if needed."

## Data Flow

```
Polar Checkout
     ↓
/success?token=XXX&job_id=YYY
     ↓
[Success.jsx]
├── Save token to localStorage
├── POST /api/upgrade-event  
├── Poll /api/credits (max 30s)
└── Redirect → /?purchased=true (or ?purchased=pending)
     ↓
[App.jsx / Homepage]
├── Check URL params
├── Show success/warning banner
└── Clear param from URL (history.replaceState)
```

## Files Changed

| File | Change |
|------|--------|
| `Success.jsx` | Rewrite: Remove duplicated UI, keep only activation logic (~100 lines) |
| `App.jsx` | Add: URL param detection + success banner (~30 lines) |
| `App.css` | Verify: `.success-banner` styles exist (reuse from Success.jsx) |
| `Success.test.jsx` | Update: Tests for new minimal behavior |

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Webhook arrives quickly | Redirect with `?purchased=true`, green banner |
| Webhook slow (>30s) | Redirect with `?purchased=pending`, warning banner |
| Token missing from URL | Show error, link to support |
| Network error during polling | Retry 3 times, then redirect with `?purchased=pending` |

## Not In Scope
- Additional success page functionality (receipts, order IDs)
- Persistent purchase history
- Email confirmation display

## Testing
- E2E: `checkout-flow.spec.js` needs update for redirect behavior
- Unit: `Success.test.jsx` update for new states
- Manual: Verify banner appearance and dismissal
