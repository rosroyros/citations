# Embedded Checkout Migration Plan

**Date**: 2024-12-19  
**Status**: Ready for Implementation

## Overview

Replace Polar redirect-based checkout with embedded iframe checkout for reduced friction and better UX.

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Integration pattern | Inline in components | Simplest for 2 entry points |
| Success UX | In-place confirmation | Modal transforms, user clicks Continue |
| `/success` page | **Delete entirely** | No emails with links, no need for legacy route |
| Fallback | **None** | If env too restrictive, accept failed conversion |
| Theme | **Auto-detect** | Use `prefers-color-scheme` for dark/light |
| Test strategy | Mock Polar SDK | `MOCK_CHECKOUT` pattern |

---

## Changes by Component

### Backend (1 file)

#### `backend/app.py`
- **Production**: Replace `success_url` with `embed_origin`
- **Mock mode**: Return `https://mock.polar.sh/checkout?token=...` (frontend intercepts)

---

### Frontend Core (5 files)

#### `package.json`
```bash
npm install @polar-sh/checkout
```

#### `src/utils/checkoutFlow.js`
```javascript
import { PolarEmbedCheckout } from '@polar-sh/checkout/embed';

export async function initiateCheckout({ productId, experimentVariant, jobId, onError, onSuccess, onClose }) {
  try {
    // ... existing API call to create checkout session ...
    
    const { checkout_url } = await response.json();
    
    // Auto-detect theme
    const theme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    
    // Open embedded checkout
    const checkout = await PolarEmbedCheckout.create(checkout_url, theme);
    
    checkout.addEventListener('success', () => {
      trackEvent('checkout_completed', { productId, experimentVariant });
      if (onSuccess) onSuccess();
    });
    
    checkout.addEventListener('close', () => {
      trackEvent('checkout_abandoned', { productId, experimentVariant });
      if (onClose) onClose();
    });
    
  } catch (error) {
    trackEvent('checkout_error', { error: error.message });
    onError(error);
  }
}
```

#### Components to Update
| File | Changes |
|------|---------|
| `UpgradeModal.jsx` | Add success state, call `refreshCredits()`, show confirmation UI |
| `PricingTableCredits.tsx` | Use embed, add `onCheckoutSuccess` prop |
| `PricingTablePasses.jsx` | Use embed, add `onCheckoutSuccess` prop |
| `PartialResults.jsx` | Handle inline pricing success |

---

### Cleanup (delete)

| File | Action |
|------|--------|
| `src/pages/Success.jsx` | **Delete** |
| `src/pages/Success.test.jsx` | **Delete** |
| `src/App.jsx` | Remove `/success` route + import |

---

### Tests to Update

**E2E (5 files):**
- `checkout-flow.spec.js`
- `upgrade-tracking.spec.js`
- `upgrade-funnel.spec.cjs`
- `pricing-integration.spec.js`
- `user-access.spec.js`

**Unit (3 files):**
- `UpgradeModal.test.jsx`
- `PricingTableCredits.test.tsx`
- `PricingTablePasses.test.jsx`

---

## Analytics Events

| Event | Trigger | Purpose |
|-------|---------|---------|
| `checkout_embed_opened` | Iframe created | Track load success |
| `checkout_completed` | Success event | Track purchase |
| `checkout_abandoned` | User closes modal | Track user intent but no purchase |
| `checkout_error` | SDK/Network error | **Critical**: Monitor strict env failures |

---

## Verification

```bash
# Unit tests
npm test -- --grep "checkoutFlow|UpgradeModal|PricingTable"

# E2E tests
npx playwright test tests/e2e/checkout-flow.spec.js

# Manual: Polar Sandbox + ngrok
```

---

## Resolved Questions

1. **Fallback**: **NO.** Restrictive envs = accept lost conversion to keep code simple.
2. **Multi-tab**: **Acceptable** — credits refresh on page reload.
3. **Session timeout**: **Acceptable** — webhook still processes, edge case.

---

## Pre-Launch Checklist

- [ ] Email Polar (hello@polar.sh) to enable Apple Pay/Google Pay for our domain
- [ ] Deploy to staging
- [ ] Test with Polar sandbox + ngrok
- [ ] Deploy to production
- [ ] Monitor `checkout_error` events for first week
