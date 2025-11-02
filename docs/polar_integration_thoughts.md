# 💳 Polar Payments Integration — CitationFormatChecker

## 🎯 Goal
Add a simple **$8.99 one-time payment** that grants users **1,000 citation credits** (credits do not expire).

No login system — users are identified via a unique token set after checkout.

---

## ✅ Decisions So Far

### 1. Payment Processor
- Use **[Polar](https://polar.sh/)** for checkout and payment processing.
- Polar provides hosted checkout and webhook notifications for payment completion.
- No credit card handling on our server.

### 2. Pricing Model
- **One-time payment**: $8.99 for 1,000 citation credits.
- Credits **never expire**.
- Free users get a limited number of credits (e.g., 30–50).

### 3. Authentication / User Management
- No traditional login or registration.
- System uses a **unique token (UUID)** generated at checkout.
- Polar checkout embeds this token in its `metadata`.
- After checkout success, Polar redirects back to the site with that token.
- Polar webhook confirms the payment, activating that token.
- Browser stores the token in a cookie; all API calls include it.

This provides paywall control without user accounts.

---

## ⚙️ System Overview

| Component | Responsibility |
|------------|----------------|
| **Frontend (HTML/JS)** | Show credit balance; display “Buy More Credits” button; redirect to Polar checkout; handle success page and store token. |
| **Backend API** | Create checkout sessions, handle webhooks, track tokens and credit balances, enforce limits. |
| **Polar** | Handles checkout, payment confirmation, and webhook notifications. |

---

## 🧩 Architecture Flow Diagram

```text
┌──────────────────┐          ┌────────────────────┐          ┌──────────────────┐
│  User (Browser)  │          │  Your Backend API  │          │      Polar       │
└───────┬──────────┘          └────────┬───────────┘          └────────┬─────────┘
        │                               │                               │
        │ Click "Buy 1,000 Credits"     │                               │
        │──────────────▶                │                               │
        │                               │ Create checkout via Polar API │
        │                               │──────────────▶                │
        │                               │◀──────────────                │
        │◀────────────── Checkout URL   │                               │
        │                               │                               │
        │ Redirect user to Polar        │                               │
        │──────────────▶                │                               │
        │                               │                               │ User completes payment
        │                               │                               │────────────▶
        │                               │                               │
        │◀────────────── Success redirect (with token)                  │
        │ Set cookie with token         │                               │
        │                               │                               │
        │                               │◀────────────── Webhook: payment.success
        │                               │ Update DB: token → +1000 credits          
        │                               │                               │
        │ API requests include token    │                               │
        │──────────────▶ Check credits, process citation
        │◀────────────── Response        │                               │
```

---

## 🔧 API Endpoints

### 1️⃣ `POST /api/create-checkout`
Creates a new Polar checkout session.
```js
const polar = new Polar({
  accessToken: process.env.POLAR_ACCESS_TOKEN,
  server: "sandbox", // for testing
});

const uuid = generateUUID();

const checkout = await polar.checkouts.create({
  productId: "prod_XXX", // 1,000 credits product
  successUrl: `https://citationformatchecker.com/success?token=${uuid}`,
  metadata: { token: uuid }
});

return checkout.url;
```

### 2️⃣ `POST /api/polar-webhook`
Handles webhook events from Polar (e.g., payment success).
```json
{
  "type": "order.created",
  "data": {
    "metadata": { "token": "abc123" },
    "status": "paid",
    "amount": 899
  }
}
```
Backend verifies signature and updates DB:
```text
credits[token] += 1000
```

### 3️⃣ `POST /api/use-citation`
Consumes 1 credit per citation request. If credits are insufficient, returns an error.

---

## 🧪 Testing Plan

### Use **Polar Sandbox**
- Configure sandbox in dashboard.
- Create test product: “1,000 Credits (Test)”.
- Use sandbox access token.

```js
server: "sandbox"
```

### Test Cards
| Card | Result |
|------|--------|
| `4242 4242 4242 4242` | Success |
| `4000 0000 0000 9995` | Declined |
| `4000 0025 0000 3155` | 3D Secure Test |

### Test Webhooks
- In Polar Dashboard → Webhooks → *Send test event*.
- Verify DB or local file updates correctly.

---

## 🚀 Going Live
1. Switch to `server: "production"` and use live access token.
2. Create live “1,000 Credits” product in Polar.
3. Update webhook to production.
4. Perform one real checkout to confirm flow.

---

## 📋 Open Questions / Considerations
| Area | Decision Needed |
|------|------------------|
| **Backend language** | Confirm backend stack (Python, Node, PHP, etc.) to prepare sample code. |
| **Credit storage** | Decide where to store token + remaining credits (SQLite / Redis / JSON). |
| **Free tier** | Finalize free credits count and renewal policy. |
| **Error handling** | Define frontend UX when user runs out of credits. |
| **Security** | Consider adding HMAC or signature to token validation. |

---

## 📚 References
- Polar Docs → [https://docs.polar.sh/](https://docs.polar.sh/)
- API Reference → [https://docs.polar.sh/reference](https://docs.polar.sh/reference)
- Checkout Sessions → [https://docs.polar.sh/reference/post-checkouts](https://docs.polar.sh/reference/post-checkouts)
- Webhooks → [https://docs.polar.sh/reference/webhooks](https://docs.polar.sh/reference/webhooks)
- Sandbox Overview → [https://docs.polar.sh/docs/sandbox](https://docs.polar.sh/docs/sandbox)

---

**Summary:**  
- $8.99 for 1,000 non-expiring credits.  
- No user accounts; tokens manage credit ownership.  
- Use Polar’s sandbox for full testing before production deployment.
