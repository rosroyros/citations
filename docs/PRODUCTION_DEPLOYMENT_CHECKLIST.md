# Production Deployment Checklist - Polar Integration

## ⚠️ CRITICAL: Sandbox vs Production Configuration

### What Changes for Production:

| Component | Sandbox | Production |
|-----------|---------|------------|
| **API Endpoint** | `SERVER_SANDBOX` | No parameter (defaults to production) |
| **Access Token** | `polar_sandbox_...` | `polar_live_...` |
| **Product ID** | Sandbox product | Production product |
| **Webhook Secret** | Sandbox webhook secret | Production webhook secret |
| **Frontend URL** | `http://localhost:5173` | `https://citationformatchecker.com` |

---

## Step-by-Step Production Deployment

### ✅ Step 1: Get Production Credentials from User

User must provide:
- [ ] Production API key (starts with `polar_live_...`)
- [ ] Production product ID (format: `prod_...`)
- [ ] Production webhook secret (format: `whsec_...`)

### ✅ Step 2: Update Environment Variables on VPS

SSH to VPS and edit `.env`:

```bash
ssh deploy@178.156.161.140
cd /opt/citations
nano backend/.env
```

Update:
```bash
POLAR_ACCESS_TOKEN=polar_live_...  # NOT polar_sandbox_...
POLAR_PRODUCT_ID=prod_...
POLAR_WEBHOOK_SECRET=whsec_...
FRONTEND_URL=https://citationformatchecker.com
```

### ✅ Step 3: ⚠️ CRITICAL - Remove Sandbox API Configuration

Edit `backend/app.py`:

```bash
nano backend/app.py
```

**FIND (around line 26-30):**
```python
from polar_sdk import SERVER_SANDBOX
polar = Polar(
    access_token=os.getenv('POLAR_ACCESS_TOKEN'),
    server=SERVER_SANDBOX
)
```

**REPLACE WITH:**
```python
polar = Polar(
    access_token=os.getenv('POLAR_ACCESS_TOKEN')
    # No server parameter = production API
)
```

### ✅ Step 4: Commit Code Change

```bash
git add backend/app.py
git commit -m "chore: switch Polar client to production API endpoint"
git push origin main
```

### ✅ Step 5: Deploy to Production

```bash
./deployment/scripts/deploy.sh
```

Verify:
```bash
sudo systemctl status citations-backend  # Should be active (running)
sudo journalctl -u citations-backend -f  # Check logs
```

### ✅ Step 6: Smoke Test

1. Visit https://citationformatchecker.com
2. Complete a **real $8.99 purchase**
3. Monitor logs for webhook arrival
4. Verify credits granted

---

## 🚨 Common Production Mistakes

### ❌ Mistake 1: Forgot to Remove SERVER_SANDBOX
**Symptom:** Checkout creation fails with "invalid credentials"
**Cause:** Production tokens don't work with sandbox API
**Fix:** Remove `SERVER_SANDBOX` from code

### ❌ Mistake 2: Mixed Sandbox/Production Credentials
**Symptom:** Signature verification fails (401)
**Cause:** Using sandbox webhook secret with production token
**Fix:** Ensure ALL credentials are from production

### ❌ Mistake 3: Wrong Frontend URL
**Symptom:** Redirect after payment goes to localhost
**Cause:** FRONTEND_URL still set to localhost
**Fix:** Update to `https://citationformatchecker.com`

### ❌ Mistake 4: Webhook URL Not Updated
**Symptom:** Credits never appear after payment
**Cause:** Polar webhook pointing to ngrok URL
**Fix:** Update webhook URL to `https://citationformatchecker.com/api/polar-webhook`

---

## Verification Commands

### Check Environment Variables
```bash
ssh deploy@178.156.161.140
cd /opt/citations
grep POLAR backend/.env | head -3
# Should show polar_live_... (NOT polar_sandbox_...)
```

### Check Code Configuration
```bash
grep -A5 "Initialize Polar client" backend/app.py
# Should NOT contain SERVER_SANDBOX
```

### Test Checkout Creation
```bash
curl -X POST https://citationformatchecker.com/api/create-checkout \
  -H "Content-Type: application/json" \
  -d '{"token":"test-123"}'

# Should return checkout_url with polar.sh (NOT sandbox.polar.sh)
```

### Monitor Webhook
```bash
sudo journalctl -u citations-backend -f | grep "webhook"
# Watch for "Webhook signature verified" messages
```

---

## Quick Reference

### Sandbox (Development)
- Import: `from polar_sdk import SERVER_SANDBOX`
- Init: `Polar(..., server=SERVER_SANDBOX)`
- Token: `polar_sandbox_...`
- URL: `https://sandbox.polar.sh/checkout/...`

### Production
- Import: None needed
- Init: `Polar(access_token=...)`
- Token: `polar_live_...`
- URL: `https://polar.sh/checkout/...`

---

## Rollback Plan

If production fails:

```bash
ssh deploy@178.156.161.140
cd /opt/citations
git revert HEAD  # Revert last commit
./deployment/scripts/deploy.sh
```

---

**Created:** 2025-11-03
**Last Updated:** After webhook debugging session
