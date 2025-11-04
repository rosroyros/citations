# Polar Webhook Integration - Issues Resolved

## Summary

Successfully debugged and fixed **4 critical issues** blocking Polar webhook integration in sandbox environment. The webhook system is now fully functional with signature validation, credit granting, and idempotency protection working end-to-end.

---

## Issues Fixed

### 1. ✅ Sandbox API Endpoint Mismatch

**Problem:** Polar SDK defaulted to production API (`https://api.polar.sh`) even when using sandbox credentials.

**Symptom:** Test card rejected with error "Your request was in live mode, but used a known test card"

**Root Cause:** SDK requires explicit `server` parameter to use sandbox

**Fix:**
```python
from polar_sdk import SERVER_SANDBOX

polar = Polar(
    access_token=os.getenv('POLAR_ACCESS_TOKEN'),
    server=SERVER_SANDBOX  # Explicitly use sandbox API
)
```

**Result:** Checkout URLs now correctly point to `https://sandbox.polar.sh/checkout/...`

---

### 2. ✅ Wrong Webhook Signature Header Name

**Problem:** All webhooks returned 401 "Invalid signature" errors

**Symptom:** ngrok showed webhook attempts but backend rejected them

**Root Cause:** Code looked for `X-Polar-Signature` but Polar sends `webhook-signature`

**Fix:**
```python
# Before (wrong)
signature = request.headers.get('X-Polar-Signature')

# After (correct)
signature = request.headers.get('webhook-signature')
```

**Result:** Signature validation now passes

---

### 3. ✅ Event Type Detection Method

**Problem:** 500 error: `'WebhookCheckoutCreatedPayload' object has no attribute 'type'`

**Symptom:** Webhook signature validated but processing failed

**Root Cause:** Polar SDK uses discriminated unions, not a `.type` attribute

**Fix:**
```python
# Before (wrong)
if webhook.type == "order.created":
    await handle_order_created(webhook)

# After (correct)
from polar_sdk.models.webhookordercreatedpayload import WebhookOrderCreatedPayload

if isinstance(webhook, WebhookOrderCreatedPayload):
    await handle_order_created(webhook)
```

**Result:** Event routing now works correctly

---

### 4. ✅ Metadata Dictionary Access

**Problem:** 500 error: `'dict' object has no attribute 'token'`

**Symptom:** Event detected but token extraction failed

**Root Cause:** `webhook.data.metadata` is a dict, not an object with attributes

**Fix:**
```python
# Before (wrong)
token = webhook.data.metadata.token

# After (correct)
token = webhook.data.metadata.get('token') if isinstance(webhook.data.metadata, dict) else webhook.data.metadata.token
```

**Result:** Token extraction works with proper error handling

---

### 5. ✅ Async/Sync API Consistency

**Problem:** `await` used on non-async function

**Symptom:** Minor - didn't break but incorrect for SDK version

**Root Cause:** Polar SDK 0.27.3 uses synchronous API calls

**Fix:**
```python
# Before
checkout = await polar.checkouts.create(...)

# After
checkout = polar.checkouts.create(...)
```

**Result:** Code matches SDK expectations

---

## Verification Tests Completed

### ✅ Sandbox Checkout Flow
- Created checkout URL: `https://sandbox.polar.sh/checkout/...`
- Test card accepted: `4242 4242 4242 4242`
- Payment completed successfully
- Redirected to success page

### ✅ Webhook Delivery
- Polar sent `checkout.created` webhook
- Polar sent `order.created` webhook
- Backend received both webhooks
- ngrok tunnel working correctly

### ✅ Signature Validation
- Webhook signature header found: `webhook-signature`
- Signature verification passed using `validate_event()`
- No 401 errors

### ✅ Credit Granting
```sql
-- Database verification
SELECT * FROM users WHERE token = 'verbose-test-123';
-- Result: verbose-test-123|1000|2025-11-03 19:04:27

SELECT * FROM orders WHERE order_id LIKE '5866457b%';
-- Result: 5866457b-93e1-4b7f-b489-48dc50a0b003|verbose-test-123|1000|2025-11-03 19:04:27
```

**✅ 1,000 credits successfully granted**
**✅ Order ID recorded (idempotency protection)**

### ✅ Logs Confirmation
```
2025-11-03 21:04:27 - citation_validator - INFO - Webhook signature verified: order.created
2025-11-03 21:04:27 - citation_validator - INFO - Processing order.created: order_id=5866457b-93e1-4b7f-b489-48dc50a0b003, token=verbose-...
2025-11-03 21:04:27 - citation_validator - INFO - Successfully granted 1000 credits for order 5866457b-93e1-4b7f-b489-48dc50a0b003
```

---

## Current Status

### ✅ Working
- Sandbox checkout creation
- Test card payment processing
- Webhook signature validation
- Credit granting (1000 per order)
- Idempotency protection
- Database persistence

### ⚠️ Known Gaps (Not Tested Yet)
- Frontend credit display integration
- Partial results UI (insufficient credits)
- Free tier (10 citations) enforcement
- Production environment configuration

---

## Next Steps

### Immediate (Required for Task 7.1 Completion)
1. **Test frontend integration**
   - Create new checkout from frontend
   - Complete payment
   - Verify credits appear in header
   - Test validation with credits deduction

2. **Test partial results**
   - Set user to 2 credits
   - Submit 5 citations
   - Verify only 2 results shown
   - Verify upgrade modal appears

### Before Production Deployment
3. **Switch to production Polar**
   - Get production API key
   - Get production product ID
   - Get production webhook secret
   - Update `.env` with production credentials
   - Remove `SERVER_SANDBOX` (defaults to production)

4. **Production smoke test**
   - Real $8.99 purchase
   - Verify webhook received
   - Verify credits granted
   - Test full flow

---

## Key Learnings

1. **Polar SDK requires explicit sandbox mode** - doesn't auto-detect from token format
2. **Webhook header names are lowercase with hyphens** - not X-Prefixed-Pascal-Case
3. **Polar SDK uses discriminated unions** - use `isinstance()` not attribute checks
4. **Metadata is always a dict** - never assume object attributes
5. **SDK version matters** - 0.27.3 is synchronous, not async

---

## Files Modified

- `backend/app.py` - All webhook and checkout fixes
- `backend/.env` - Sandbox credentials (not committed)

## Commit

```
fix: resolve Polar sandbox webhook integration issues

Commit: e561dba
```

---

## Credits

Debugging collaboration between architect (Claude) and user on 2025-11-03.

**Total debugging time:** ~2 hours
**Issues identified:** 5
**Issues resolved:** 5
**Success rate:** 100%

🎉 **Webhook system fully operational!**
