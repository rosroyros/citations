# Webhook Signature Testing Guide - FINAL CRITICAL TEST

**Status**: READY FOR REAL PURCHASE TEST
**Date**: November 3, 2025
**Environment**: Polar Sandbox + Ngrok Tunnel

## 🎯 TEST OBJECTIVE

Complete end-to-end webhook signature validation using real Polar sandbox purchase to verify:
1. Polar sends webhook to ngrok endpoint
2. Signature validation passes
3. Credits are automatically granted
4. Idempotency protection works

## 🔧 TEST SETUP VERIFICATION

### ✅ Ngrok Tunnel Status
- **URL**: `https://samson-unchevroned-ronna.ngrok-free.dev/api/polar-webhook`
- **Status**: Active (HTTP/2 405 response for GET - correct behavior)
- **Backend**: `http://localhost:8000/api/polar-webhook`

### ✅ Polar Sandbox Configuration
- **Webhook URL**: `https://samson-unchevroned-ronna.ngrok-free.dev/api/polar-webhook`
- **Webhook Secret**: `polar_whs_pONDNf6TfVH6JXqrWrfyyk97TMAPRwWVDyekX2LLsuJ`
- **Status**: Configured in Polar sandbox

### ✅ Backend Configuration
```bash
# backend/.env contains correct credentials
POLAR_ACCESS_TOKEN=polar_oat_0zxtZDsHSkh20GyehuwRCT2I8aAmdPcy6NZEQ0bDl5N
POLAR_PRODUCT_ID=f12e0a67-826f-41c1-a027-73ceca3d2b1d
POLAR_WEBHOOK_SECRET=polar_whs_pONDNf6TfVH6JXqrWrfyyk97TMAPRwWVDyekX2LLsuJ
FRONTEND_URL=http://localhost:5173
```

## 🧪 TEST PROCEDURE

### Step 1: Pre-Purchase Verification
```bash
# Check initial balance (should be 0)
curl "http://localhost:8000/api/credits?token=webhook-final-test-456"
```

**Expected**: `{"token":"webhook-final-test-456","credits":0}`

### Step 2: Complete Polar Sandbox Purchase
**Checkout URL**: `https://polar.sh/checkout/polar_c_SF3USzXy78S8HnlK0yQS9ptKfEmEHt2yQiH4b240Dmg`

**Test User Token**: `webhook-final-test-456`

**Purchase Steps**:
1. Visit checkout URL above
2. Complete sandbox payment ($8.99)
3. Wait for redirect to success page
4. Monitor backend logs for webhook processing

### Step 3: Webhook Processing Verification

#### Watch Backend Logs:
```bash
# Monitor backend in real-time
tail -f backend/logs/app.log
# OR watch terminal output from running backend
```

#### Expected Log Sequence:
```
2025-11-03 09:30:00 - citation_validator - INFO - Polar webhook received
2025-11-03 09:30:01 - citation_validator - INFO - Webhook signature verified: order.created
2025-11-03 09:30:01 - citation_validator - INFO - Processing order.created: order_id=xyz, token=webhook-final-test-456
2025-11-03 09:30:01 - database - INFO - Added 1000 credits for token webhook-final-test-456, order xyz
2025-11-03 09:30:01 - citation_validator - INFO - Successfully granted 1000 credits for order xyz
```

#### ❌ FAILURE LOGS TO WATCH FOR:
```
# Signature validation failure
2025-11-03 09:30:00 - citation_validator - ERROR - Webhook signature verification failed: Invalid signature

# Missing headers
2025-11-03 09:30:00 - citation_validator - ERROR - Webhook signature verification failed: Missing required headers

# Database issues
2025-11-03 09:30:00 - citation_validator - ERROR - Failed to process webhook: database error
```

### Step 4: Post-Purchase Verification
```bash
# Check final balance (should be 1000)
curl "http://localhost:8000/api/credits?token=webhook-final-test-456"
```

**Expected**: `{"token":"webhook-final-test-456","credits":1000}`

### Step 5: Idempotency Test
Complete the same checkout URL again (should not grant additional credits):

```bash
# Balance should remain 1000 (no additional credits granted)
curl "http://localhost:8000/api/credits?token=webhook-final-test-456"
```

**Expected**: `{"token":"webhook-final-test-456","credits":1000}`

**Expected Log**: `WARNING:database:Order ID xyz already processed, skipping`

## 🎯 SUCCESS CRITERIA

### ✅ TEST PASSES IF:
1. **Webhook Received**: Backend logs show "Polar webhook received"
2. **Signature Validated**: "Webhook signature verified: order.created" appears in logs
3. **Credits Granted**: Balance changes from 0 → 1000
4. **Order Tracking**: Order ID logged and database shows order_id
5. **Idempotency**: Second purchase attempt doesn't add credits

### ❌ TEST FAILS IF:
1. **No Webhook**: No webhook logs in backend
2. **Signature Failure**: "Invalid signature" error in logs
3. **No Credits**: Balance remains 0 after purchase
4. **Database Errors**: Failed to process webhook errors

## 🚨 ROLLBACK PLAN

If webhook signature validation fails:
1. **Immediate Action**: Check backend logs for exact error
2. **Investigation**: Verify webhook secret matches Polar configuration
3. **Debug**: Test webhook signature manually if needed
4. **Fallback**: Document issue and proceed to production smoke test

## 📊 TEST RESULTS EXPECTATIONS

| Component | Expected Result | Verification Method |
|-----------|----------------|-------------------|
| Ngrok Tunnel | ✅ Active | HTTP 405 response |
| Webhook Receipt | ✅ Received | Backend logs |
| Signature Validation | ✅ Pass | "Webhook signature verified" in logs |
| Credit Activation | ✅ 1000 credits | Balance check |
| Idempotency | ✅ No duplicate credits | Second purchase test |

## 🎬 NEXT STEPS

### IF TEST PASSES:
1. ✅ **Webhook signature validation working**
2. ✅ **Production ready for Task 7.5**
3. ✅ **Deploy to production with confidence**

### IF TEST FAILS:
1. 🔍 **Debug signature validation**
2. 🔧 **Fix webhook configuration**
3. 📝 **Document limitation**
4. 🚀 **Proceed to production with monitoring**

## 📝 NOTES

- **Test Duration**: 5-10 minutes for complete purchase flow
- **Monitoring**: Keep backend logs visible during test
- **Polar Sandbox**: Uses test payment methods (no real charges)
- **Ngrok**: Tunnel remains active for 8 hours
- **Rollback**: Can restart backend with git revert if needed

---

**TEST STATUS**: 🟡 **WAITING FOR PURCHASE COMPLETION**
**READY TO PROCEED**: ✅ All infrastructure verified and monitoring active