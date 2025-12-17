# Inline Pricing A/B Test - Implementation Plan

**Goal**: Test if showing pricing directly (vs button → modal) improves conversion from locked → purchase.

**Hypothesis**: The extra click loses users. Removing it should improve conversion.

---

## 1. Variant Scheme

| ID | Pricing | Display | Behavior |
|----|---------|---------|----------|
| 1.1 | Credits | Button | Current behavior |
| 1.2 | Credits | Inline | Pricing shown directly |
| 2.1 | Passes | Button | Current behavior |
| 2.2 | Passes | Inline | Pricing shown directly |

**Assignment**: 25% each (equal split across 4 variants)

**Migration**: Re-assign all existing users (`"1"` → random `.1`/`.2`, `"2"` → random `.1`/`.2`)

---

## 2. Changes Required

### Frontend - Core

| File | Change |
|------|--------|
| `experimentVariant.js` | Return `1.1`/`1.2`/`2.1`/`2.2`, new helpers, **simplified migration logic** |
| `checkoutFlow.js` | **[NEW]** Extract checkout logic, include **try/catch and onError callback** |
| `PartialResults.jsx` | Render banner + inline pricing, track **`pricing_viewed` (truthful) and `clicked` (auto/legacy)** |
| `UpgradeModal.jsx` | Import from `checkoutFlow.js`, keep modal wrapper |

### Frontend - Other Files Using Variant

| File | Impact |
|------|--------|
| `App.jsx` | Sends `X-Experiment-Variant` header - OK |
| `Success.jsx` | Sends `X-Experiment-Variant` header - OK |
| `MiniChecker.jsx` | Sends header - OK |

### Backend

| File | Change |
|------|--------|
| `app.py` | Update fallback assignment to use `['1.1', '1.2', '2.1', '2.2']` |

### Dashboard

| File | Change |
|------|--------|
| `index.html` | Update funnel chart labels to show 4 variants |

### Tests

| File | Change |
|------|--------|
| `experimentVariant.test.js` | Update expectations for new format |
| `pricing_variants.spec.cjs` | Add tests for 1.2 and 2.2 inline variants |
| `PartialResults.test.jsx` | Test inline pricing rendering and events |

---

## 3. Detailed Implementation

### 3.1 experimentVariant.js Changes

Simplified logic for robust assignment/migration:

```javascript
// New constants
const VALID_VARIANTS = ['1.1', '1.2', '2.1', '2.2'];

export function getExperimentVariant() {
  let variantId = localStorage.getItem('experiment_v1');
  
  // If missing or invalid (including old '1'/'2' formats), assign a fresh new variant
  if (!variantId || !VALID_VARIANTS.includes(variantId)) {
    variantId = VALID_VARIANTS[Math.floor(Math.random() * VALID_VARIANTS.length)];
    localStorage.setItem('experiment_v1', variantId);
  }
  
  return variantId;
}

// New helpers
export function isInlineVariant(variant) {
  return variant?.endsWith('.2');
}

export function getPricingType(variant) {
  return variant?.startsWith('1') ? 'credits' : 'passes';
}
```

### 3.2 PartialResults.jsx Changes

Updated for truthful analytics and proper imports:

```jsx
import { Lock } from 'lucide-react';
// ... other imports

// Inside component:
const variant = getExperimentVariant();
const showInline = isInlineVariant(variant);

useEffect(() => {
  if (showInline) {
    // Truthful event for new analysis
    trackEvent('pricing_viewed', { 
      variant, 
      interaction_type: 'auto' 
    });
    
    // Legacy support: auto-fire clicked so funnel 'Step 2' isn't 0%
    // BUT mark it clearly so we can exclude it later
    trackEvent('clicked', { 
      variant, 
      interaction_type: 'auto',
      note: 'legacy_funnel_support'
    });
  }
}, [showInline, variant]);

// Render:
{showInline ? (
  <>
    <div className="upgrade-banner">
      <Lock size={16} /> {citations_remaining} more citations available
      <br/>Upgrade to unlock validation results & more usage
    </div>
    <div className="inline-pricing-container">
      {getPricingType(variant) === 'credits' ? (
        <PricingTableCredits onSelectProduct={handleCheckout} />
      ) : (
        <PricingTablePasses onSelectProduct={handleCheckout} />
      )}
    </div>
  </>
) : (
  // Existing button behavior
)}
```

**CSS (`PartialResults.css`):**
```css
.inline-pricing-container {
  margin-top: 1.5rem;
  width: 100%;
}
```

### 3.3 checkoutFlow.js (New File)

Updated for robustness (try/catch + error callback):

```javascript
export async function createCheckout({ productId, experimentVariant, jobId, onError }) {
  const token = localStorage.getItem('userToken');
  
  trackEvent('product_selected', { 
    product_id: productId, 
    experiment_variant: experimentVariant 
  });
  
  // Store job_id for success page
  if (jobId) {
    localStorage.setItem('pending_upgrade_job_id', jobId);
  }
  
  try {
    const response = await fetch('/api/create-checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, productId, variantId: experimentVariant, job_id: jobId })
    });

    if (!response.ok) throw new Error('Checkout creation failed');

    const { checkout_url } = await response.json();
    window.location.href = checkout_url;
  } catch (error) {
    console.error('Checkout error:', error);
    if (onError) onError(error);
    // Optional: show toast or alert if onError provides that logic
  }
}
```

---

## 4. Tracking Strategy

| Event | Button Variant | Inline Variant | Notes |
|-------|---------------|----------------|-------|
| `upgrade_presented` | On mount | On mount | |
| `locked` state | On mount | On mount | |
| `pricing_viewed` | On Modal Open | **On Mount** | **New truthful event** |
| `clicked` | On Button Click | **On Mount (Auto)** | Legacy support (`interaction_type: 'auto'`) |
| `product_selected` | When user picks | When user picks | |

---

## 5. Verification

```bash
# Unit tests
cd frontend/frontend && npm test -- --run

# E2E tests  
cd frontend/frontend && npx playwright test tests/e2e/pricing_variants.spec.cjs
```
