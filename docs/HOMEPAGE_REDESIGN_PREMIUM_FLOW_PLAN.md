# Homepage Redesign + Premium Flow - Implementation Plan

---

## ⚠️ CRITICAL INSTRUCTIONS FOR DEVELOPER

**DO NOT DEVIATE FROM THIS PLAN FOR ANY REASON.**

If you encounter:
- Unexpected errors or challenges
- Missing dependencies or credentials
- Unclear requirements
- Technical blockers
- Design decisions not covered in the plan

**STOP IMMEDIATELY and ask the user/architect for guidance.**

Do NOT:
- Make assumptions
- Choose alternative approaches
- Skip steps
- Improvise solutions
- Continue until your question is answered

Post your question in this format:
```
BLOCKED: [Brief description of issue]
CONTEXT: [What you were doing when blocked]
QUESTION: [Specific question for architect]
```

The user will consult with the architect (Claude) and provide guidance. **Wait for explicit approval before continuing.**

---

## Environment Setup (Developer Task)

**Virtual Environment:**
This project uses Python virtual environment (`venv`) for dependency isolation.

**Activation:**
```bash
# From project root
source venv/bin/activate

# You should see (venv) in your terminal prompt
# Example: (venv) user@machine:~/citations$
```

**Always activate venv before:**
- Installing Python packages
- Running backend commands
- Running tests

**Deactivation (when done working):**
```bash
deactivate
```

**If venv doesn't exist or is corrupted:**
```bash
# STOP and ask user/architect before proceeding
# Do not create new venv without approval
```

---

## Task Assignment Legend

**👤 USER TASK** - User must complete before developer can proceed
**👨‍💻 DEVELOPER TASK** - Developer implements and tests
**🤝 COLLABORATIVE** - Developer implements, user reviews/approves

---

## Credit System Model

**Free Tier (Frontend-enforced):**
- 10 free citations tracked in localStorage
- Frontend blocks submission after 10, shows upgrade modal
- Backend validates everything if no token present (no credit check)

**Paid Tier (Backend-enforced):**
- 1,000 Citation Credits for $8.99
- Tracked in SQLite database
- Separate from free tier (10 free + 1,000 paid = 1,010 total capacity)
- Credits never expire
- Repeat purchases ADD credits

**Validation Flow:**
1. LLM validates ALL citations (regardless of credits)
2. Backend counts results: `len(validation_results["results"])`
3. If insufficient credits: return first N results + partial flag
4. Deduct credits based on results shown

---

## Prerequisites: Polar Dashboard Setup

### 👤 USER TASK: Step 1 - Get Sandbox Access Token
1. Log in to [polar.sh](https://polar.sh)
2. Toggle "Sandbox Mode" (switch in top-right corner)
3. Navigate to Settings → API Keys
4. Click "Create API Key", name it "Citation Checker Sandbox"
5. Copy token (format: `polar_sandbox_...`)
6. **Provide to developer** in secure manner (Slack DM, password manager, etc.)

### 👤 USER TASK: Step 2 - Create Product
1. Products → Create Product
2. Fill in:
   - **Name:** "1,000 Citation Credits"
   - **Description:** "Check 1,000 citations with our APA validator"
   - **Price:** $8.99 USD
   - **Type:** One-time purchase (not subscription)
3. Copy Product ID (format: `prod_...`)
4. **Provide to developer**

### 👤 USER TASK: Step 3 - Configure Webhook (Sandbox)
1. Settings → Webhooks → Add Endpoint
2. **URL:** Developer will provide ngrok URL (format: `https://abc123.ngrok.io/api/polar-webhook`)
3. **Events:** Select:
   - ✅ `checkout.created`
   - ✅ `checkout.updated`
   - ✅ `order.created`
4. Click Create
5. Copy webhook signing secret (format: `whsec_...`)
6. **Provide to developer**

### 👤 USER TASK: Step 4 - Provide Refund Policy Text
Developer needs refund policy wording for FAQ section. Provide exact text, e.g.:
```
"Yes, we offer full refunds within 30 days of purchase if you're not satisfied."
```
OR
```
"All sales are final. Credits never expire."
```

### 👨‍💻 DEVELOPER TASK: Step 5 - Set Up Local Webhook Testing
1. Install ngrok (if not installed): `brew install ngrok`
2. Run: `ngrok http 8000`
3. Copy HTTPS URL from output (e.g., `https://abc123.ngrok.io`)
4. **Provide URL to user** for webhook configuration (Step 3 above)
5. Keep ngrok running during development

### 👨‍💻 DEVELOPER TASK: Step 6 - Configure Environment Variables
1. Activate venv: `source venv/bin/activate`
2. Create/update `backend/.env` file:
   ```bash
   # Polar sandbox credentials (user provides these)
   POLAR_ACCESS_TOKEN=polar_sandbox_...
   POLAR_PRODUCT_ID=prod_...
   POLAR_WEBHOOK_SECRET=whsec_...

   # Frontend URL (for redirect after checkout)
   FRONTEND_URL=http://localhost:5173

   # OpenAI (should already exist)
   OPENAI_API_KEY=...
   ```
3. Verify `.env` is in `.gitignore` (should already be)
4. **NEVER commit `.env` to git**

### 👤 USER TASK: Step 7 - Production Setup (Phase 7 - After Testing)
**Complete this AFTER successful local testing, before production deployment.**

1. In Polar dashboard, toggle OFF Sandbox Mode
2. Repeat Steps 1-3 above for production:
   - Create production API key
   - Create production product ($8.99)
   - Configure production webhook:
     - **URL:** `https://citationformatchecker.com/api/polar-webhook`
     - Same events as sandbox
3. Provide production credentials to developer for deployment

---

## Phase 1: Backend - Database Setup

### 👨‍💻 DEVELOPER TASK 1.1: Create SQLite Database Schema

**Context:** Need persistent storage for paid users' tokens, credit balances, and purchase records. Using SQLite for simplicity (single-file database, no separate server).

**Why this matters:** Without a database, credits can't persist across sessions, and webhook can't update balances.

**Files to create:**
- `backend/database.py`
- `backend/tests/test_database_schema.py`

**Database schema:**
```sql
-- Users table: tracks credit balances
CREATE TABLE users (
    token TEXT PRIMARY KEY,
    credits INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table: prevents duplicate webhook processing
CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,  -- Polar's unique order ID
    token TEXT NOT NULL,
    credits_granted INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (token) REFERENCES users(token)
);
```

**Execution steps:**
1. **Activate venv:** `source venv/bin/activate`
2. **Write test** (`test_database_schema.py`):
   - Test that `init_db()` creates database file
   - Test that `users` table exists with correct columns
   - Test that `orders` table exists with correct columns
   - Test foreign key constraint works
3. **Run test:** `python3 -m pytest backend/tests/test_database_schema.py -v`
   - Expect FAILURE (no database.py yet)
4. **Implement** `database.py`:
   - Import sqlite3
   - Create `DB_PATH = 'backend/credits.db'` constant
   - Implement `init_db()` function:
     - Connect to database (creates file if not exists)
     - Execute CREATE TABLE statements (with IF NOT EXISTS)
     - Commit and close
   - Add proper error handling (permissions, disk space)
5. **Run test again:**
   - Expect PASS
6. **Manual verification:**
   - Run `python3 -c "from backend.database import init_db; init_db()"`
   - Check file exists: `ls -lh backend/credits.db`
   - Inspect schema: `sqlite3 backend/credits.db ".schema"`

**Why order_id is critical:** Without this, duplicate webhooks (network retries) would grant credits twice. Order ID ensures idempotency.

**Verification checklist:**
- [ ] Tests pass
- [ ] `credits.db` file created
- [ ] Tables have correct structure
- [ ] Foreign key constraint enforced

**Commits (2 separate commits):**
1. `test: add database schema tests`
2. `feat: create SQLite database schema for credit tracking`

**If blocked:** STOP and ask user/architect.

---

### 👨‍💻 DEVELOPER TASK 1.2: Create Database Operations

**Context:** API endpoints need functions to read/write credits and log transactions. These functions handle all SQL operations with proper error handling and atomic operations.

**Why atomic operations matter:** Two simultaneous requests could try to deduct credits from same balance. Using `UPDATE ... WHERE credits >= amount` ensures only one succeeds.

**Files to modify:**
- `backend/database.py` (add functions)
- `backend/tests/test_database_operations.py` (new)

**Functions to implement:**

1. **`get_credits(token: str) -> int`**
   - Returns credit balance for token
   - Returns 0 if token doesn't exist
   - Read-only, no locking needed

2. **`add_credits(token: str, amount: int, order_id: str) -> bool`**
   - Creates user if doesn't exist
   - Adds credits to existing user (always ADD, never replace)
   - Records order_id in orders table
   - **Returns False if order_id already exists** (idempotency check)
   - Uses transaction for atomicity

3. **`deduct_credits(token: str, amount: int) -> bool`**
   - Atomically deducts credits using: `UPDATE users SET credits = credits - ? WHERE token = ? AND credits >= ?`
   - **Returns False if insufficient credits** (no row updated)
   - Returns True if successful

**Execution steps:**
1. **Activate venv:** `source venv/bin/activate`
2. **Write tests:**
   - Test `get_credits` returns 0 for non-existent token
   - Test `add_credits` creates new user with correct balance
   - Test `add_credits` adds to existing user (100 + 1000 = 1100)
   - Test `add_credits` rejects duplicate order_id (idempotency)
   - Test `deduct_credits` reduces balance correctly
   - Test `deduct_credits` returns False when insufficient credits
   - Test `deduct_credits` race condition (two simultaneous deductions)
3. **Run tests:** `python3 -m pytest backend/tests/test_database_operations.py -v`
   - Expect FAILURES
4. **Implement functions** in `database.py`:
   - Use context managers for connections: `with sqlite3.connect(DB_PATH) as conn:`
   - Enable foreign keys: `conn.execute("PRAGMA foreign_keys = ON")`
   - Use parameterized queries (prevents SQL injection)
   - Add logging for all operations
   - Handle exceptions (database locked, constraint violations)
5. **Run tests again:**
   - Expect PASS
6. **Manual verification:**
   - Create test user: `add_credits('test-token-123', 1000, 'order-1')`
   - Check balance: `get_credits('test-token-123')` → should return 1000
   - Deduct credits: `deduct_credits('test-token-123', 50)` → should return True
   - Check new balance: `get_credits('test-token-123')` → should return 950
   - Try duplicate order: `add_credits('test-token-123', 1000, 'order-1')` → should return False

**Why this approach:** Keeping database logic separate from API logic makes testing easier and allows reuse across endpoints.

**Verification checklist:**
- [ ] All tests pass
- [ ] Idempotency works (duplicate order_id rejected)
- [ ] Atomic deduction prevents race conditions
- [ ] Functions handle errors gracefully

**Commits (2 separate commits):**
1. `test: add database operation tests`
2. `feat: implement database CRUD operations for credits`

**If blocked:** STOP and ask user/architect.

---

## Phase 2: Backend - Polar Integration

### 👨‍💻 DEVELOPER TASK 2.1: Add Polar SDK Dependency

**Context:** Need Polar's official Python SDK to interact with their API (create checkouts, verify webhooks).

**Files to modify:**
- `backend/requirements.txt`

**Execution steps:**
1. **Activate venv:** `source venv/bin/activate`
2. Check latest version: Visit https://pypi.org/project/polar-sdk/
3. Add to `requirements.txt`: `polar-sdk==0.x.x` (use latest stable version)
4. Install: `python3 -m pip install -r requirements.txt`
5. Verify import: `python3 -c "from polar_sdk import Polar; print('Polar SDK installed')"`

**Verification:**
- [ ] Installation succeeds
- [ ] Import works without errors

**Commit:** `feat: add Polar SDK dependency`

**If blocked:** STOP and ask user/architect.

---

### 👨‍💻 DEVELOPER TASK 2.2: Create Checkout Endpoint

**Context:** When user clicks "Get Citation Credits", frontend needs a Polar checkout URL to redirect to. This endpoint generates that URL using Polar's API, embedding the user's token in metadata so webhook can identify them later.

**Why token in metadata:** After payment, Polar webhook includes this metadata. That's how we know which user to credit.

**Files to modify:**
- `backend/app.py`
- `backend/tests/test_checkout_endpoint.py` (new)

**API contract:**
```
POST /api/create-checkout
Request body: { "token": "optional-existing-token" }
Response: {
  "checkout_url": "https://checkout.polar.sh/...",
  "token": "abc-123-xyz"  // Generated or provided token
}
```

**Execution steps:**
1. **Activate venv:** `source venv/bin/activate`
2. **Write tests:**
   - Test generates UUID if no token provided
   - Test uses existing token if provided
   - Mock Polar API call, verify parameters (product_id, success_url, metadata)
   - Test returns checkout_url from Polar response
   - Test error handling if Polar API fails (network error, invalid credentials)
3. **Run tests:** `python3 -m pytest backend/tests/test_checkout_endpoint.py -v`
   - Expect FAILURE
4. **Implement endpoint** in `app.py`:
   - Import: `from polar_sdk import Polar`, `import uuid`, `import os`
   - Initialize Polar client: `polar = Polar(access_token=os.getenv('POLAR_ACCESS_TOKEN'))`
   - Create endpoint:
     ```python
     @app.post("/api/create-checkout")
     async def create_checkout(request: dict):
         # Get or generate token
         token = request.get('token') or str(uuid.uuid4())

         # Create Polar checkout
         checkout = await polar.checkouts.create({
             "product_id": os.getenv('POLAR_PRODUCT_ID'),
             "success_url": f"{os.getenv('FRONTEND_URL')}/success?token={token}",
             "metadata": {"token": token}
         })

         return {"checkout_url": checkout.url, "token": token}
     ```
   - Add FRONTEND_URL to .env if not already there
   - Handle Polar API errors (auth failure, invalid product_id)
   - Log checkout creation for debugging
5. **Run tests:**
   - Expect PASS
6. **Manual test:**
   - Ensure backend running: `python3 backend/app.py`
   - `curl -X POST http://localhost:8000/api/create-checkout -H "Content-Type: application/json" -d '{}'`
   - Should return JSON with checkout_url
   - Open URL in browser → should redirect to Polar payment page

**Verification checklist:**
- [ ] Tests pass
- [ ] Endpoint returns valid checkout URL
- [ ] URL opens to Polar payment page (sandbox)
- [ ] Token embedded in success_url

**Commits (2 separate commits):**
1. `test: add checkout creation tests`
2. `feat: implement Polar checkout creation endpoint`

**If blocked:** STOP and ask user/architect.

---

### 👨‍💻 DEVELOPER TASK 2.3: Create Webhook Endpoint

**Context:** After user completes payment, Polar sends HTTP POST to our webhook with payment details. This endpoint verifies the webhook is authentic (signature check), extracts user token from metadata, and grants 1,000 credits. **Critical security:** Must verify webhook signature to prevent fake payment notifications.

**Why idempotency matters:** Polar may retry webhooks on network errors. Without order_id check, user could get 2,000 credits for one payment.

**Files to modify:**
- `backend/app.py`
- `backend/tests/test_webhook_endpoint.py` (new)

**Webhook payload example:**
```json
{
  "type": "order.created",
  "data": {
    "id": "order_abc123",
    "amount": 899,
    "metadata": {
      "token": "user-token-xyz"
    }
  }
}
```

**Execution steps:**
1. **Activate venv:** `source venv/bin/activate`
2. **Write tests:**
   - Test valid webhook signature accepted
   - Test invalid signature rejected (401 response)
   - Test order.created event grants 1,000 credits
   - Test duplicate webhook (same order_id) doesn't grant credits twice
   - Test non-order events ignored (checkout.created, etc.)
   - Mock `add_credits` database function
3. **Run tests:** `python3 -m pytest backend/tests/test_webhook_endpoint.py -v`
   - Expect FAILURE
4. **Implement endpoint:**
   - Import webhook verification from Polar SDK
   - Create `POST /api/polar-webhook` endpoint
   - Extract signature from headers: `request.headers.get('X-Polar-Signature')`
   - Verify signature using Polar SDK:
     ```python
     from polar_sdk.webhooks import verify_signature

     if not verify_signature(
         payload=request.body,
         signature=signature,
         secret=os.getenv('POLAR_WEBHOOK_SECRET')
     ):
         return JSONResponse(status_code=401, content={"error": "Invalid signature"})
     ```
   - Parse JSON body
   - Check event type: only process `order.created` or `checkout.updated` with status=completed
   - Extract: `order_id = data['id']`, `token = data['metadata']['token']`
   - Grant credits: `success = add_credits(token, 1000, order_id)`
   - If success: log transaction, return 200
   - If duplicate (success=False): log warning, return 200 anyway (Polar expects 200)
   - Return 200 OK (Polar requires this to stop retrying)
5. **Run tests:**
   - Expect PASS
6. **Manual test using ngrok:**
   - Ensure ngrok running: `ngrok http 8000`
   - Start backend: `python3 backend/app.py`
   - In Polar dashboard: Send test webhook
   - Check backend logs for webhook received
   - Check database: `sqlite3 backend/credits.db "SELECT * FROM users;"`
   - Verify 1,000 credits added

**Security note:** Never skip signature verification in production. Attackers could POST fake webhooks to grant unlimited credits.

**Verification checklist:**
- [ ] Tests pass
- [ ] Signature verification works
- [ ] Credits granted on valid webhook
- [ ] Duplicate webhooks handled (idempotency)
- [ ] Test webhook from Polar succeeds

**Commits (2 separate commits):**
1. `test: add webhook handler tests`
2. `feat: implement Polar webhook endpoint with signature verification`

**If blocked:** STOP and ask user/architect.

---

### 👨‍💻 DEVELOPER TASK 2.4: Create Credits Balance Endpoint

**Context:** Frontend needs to fetch user's current credit balance to display in header. Simple read-only endpoint.

**Files to modify:**
- `backend/app.py`
- `backend/tests/test_credits_endpoint.py` (new)

**API contract:**
```
GET /api/credits?token=abc-123
Response: { "token": "abc-123", "credits": 847 }
```

**Execution steps:**
1. **Activate venv:** `source venv/bin/activate`
2. **Write tests:**
   - Test returns correct balance for existing user
   - Test returns 0 for non-existent token
   - Test returns error if token parameter missing
3. **Run tests:** `python3 -m pytest backend/tests/test_credits_endpoint.py -v`
   - Expect FAILURE
4. **Implement endpoint:**
   ```python
   @app.get("/api/credits")
   async def get_credits_balance(token: str):
       if not token:
           raise HTTPException(status_code=400, detail="Token required")

       balance = get_credits(token)
       return {"token": token, "credits": balance}
   ```
5. **Run tests:**
   - Expect PASS
6. **Manual test:** `curl "http://localhost:8000/api/credits?token=test-123"`

**Verification:**
- [ ] Tests pass
- [ ] Returns correct balances

**Commits (2 separate commits):**
1. `test: add credits balance endpoint tests`
2. `feat: add credits balance query endpoint`

**If blocked:** STOP and ask user/architect.

---

## Phase 3: Backend - Credit Enforcement

### 👨‍💻 DEVELOPER TASK 3.1: Modify Validation Endpoint for Credit Enforcement

**Context:** Current `/api/validate` endpoint validates citations without any credit checking. Need to add logic that: extracts user token, calls LLM to validate all citations, counts results, checks credits, returns full or partial results accordingly.

**Critical insight:** Citation counting happens AFTER LLM call by checking `len(results)`. The LLM already identifies citation boundaries (in `openai_provider.py`), so we don't need complex parsing logic upfront.

**Flow:**
```
1. Extract token from X-User-Token header (optional)
2. Call LLM with all citations (existing logic)
3. LLM returns array of results (existing logic)
4. Count citations: citation_count = len(results)
5. If no token → return all results (free tier, frontend-enforced)
6. If token exists:
   a. Get user credits from database
   b. If credits >= citation_count:
      - Deduct citation_count credits
      - Return all results
   c. If credits < citation_count:
      - Deduct credits (all remaining)
      - Return partial results (first N)
```

**Files to modify:**
- `backend/app.py` (modify existing `/api/validate` endpoint around line 144)
- `backend/tests/test_credit_enforcement.py` (new)

**Execution steps:**
1. **Activate venv:** `source venv/bin/activate`
2. **Write tests covering all scenarios:**
   - **No token (free tier):** Validates 10 citations, returns all results
   - **Token with sufficient credits:** User has 100 credits, submits 5 citations, gets all 5 results, credits → 95
   - **Token with insufficient credits:** User has 3 credits, submits 10 citations, gets 3 results + partial flag, credits → 0
   - **Token with zero credits:** User has 0 credits, submits any citations, gets error immediately
   - **Edge case:** User has 50 credits, submits 50 citations, gets all results, credits → 0
   - Mock LLM and database functions
3. **Run tests:** `python3 -m pytest backend/tests/test_credit_enforcement.py -v`
   - Expect FAILURE
4. **Modify `/api/validate` endpoint:**
   - Add token extraction at start of function:
     ```python
     token = request.headers.get('X-User-Token')
     ```
   - Keep existing LLM call (already works - don't modify)
   - After getting LLM results (around line 171-178), add credit logic:
     ```python
     results = validation_results["results"]
     citation_count = len(results)

     if not token:
         # Free tier - return everything (frontend enforces 10 limit)
         return ValidationResponse(results=results)

     # Paid tier - check credits
     user_credits = get_credits(token)

     if user_credits == 0:
         raise HTTPException(
             status_code=402,  # Payment Required
             detail="You have 0 Citation Credits remaining. Purchase more to continue."
         )

     if user_credits >= citation_count:
         # Can afford all citations
         deduct_credits(token, citation_count)
         return ValidationResponse(
             results=results,
             credits_remaining=user_credits - citation_count
         )
     else:
         # Partial results
         affordable = user_credits
         deduct_credits(token, affordable)
         return ValidationResponse(
             results=results[:affordable],
             partial=True,
             citations_checked=affordable,
             citations_remaining=citation_count - affordable,
             credits_remaining=0
         )
     ```
   - **Update ValidationResponse model** (around line 127) to support partial results:
     ```python
     class ValidationResponse(BaseModel):
         results: list[CitationResult]
         partial: bool = False
         citations_checked: Optional[int] = None
         citations_remaining: Optional[int] = None
         credits_remaining: Optional[int] = None
     ```
5. **Run tests:**
   - Expect PASS
6. **Manual testing:**
   - Create test user with 3 credits: `sqlite3 backend/credits.db "INSERT INTO users (token, credits) VALUES ('test-token', 3);"`
   - Start backend: `python3 backend/app.py`
   - Submit 10 citations with token header:
     ```bash
     curl -X POST http://localhost:8000/api/validate \
       -H "Content-Type: application/json" \
       -H "X-User-Token: test-token" \
       -d '{"citations": "...(10 citations)...", "style": "apa7"}'
     ```
   - Verify response has `partial: true`, only 3 results
   - Check database: `sqlite3 backend/credits.db "SELECT credits FROM users WHERE token='test-token';"` → should be 0

**Verification checklist:**
- [ ] All test scenarios pass
- [ ] Free tier (no token) returns all results
- [ ] Paid tier deducts correct credits
- [ ] Partial results work correctly
- [ ] Zero credits returns 402 error

**Commits (2 separate commits):**
1. `test: add credit enforcement tests`
2. `feat: add credit enforcement to validation endpoint`

**If blocked:** STOP and ask user/architect.

---

## Phase 4: Frontend - Credit System Infrastructure

### 👨‍💻 DEVELOPER TASK 4.1: Create Credit Storage Utilities

**Context:** Need localStorage wrapper to save/retrieve user token and track free tier usage client-side. Keeps storage logic centralized and testable.

**Files to create:**
- `frontend/frontend/src/utils/creditStorage.js`
- `frontend/frontend/src/utils/creditStorage.test.js`

**Functions to implement:**
```javascript
// Token management (paid tier)
saveToken(token: string): void
getToken(): string | null
clearToken(): void

// Free tier tracking
getFreeUsage(): number  // Returns 0-10
incrementFreeUsage(count: number): void
resetFreeUsage(): void
```

**Execution steps:**
1. **Write tests:**
   - Test `saveToken` stores in localStorage under key `citation_checker_token`
   - Test `getToken` retrieves token or returns null
   - Test `clearToken` removes token
   - Test `getFreeUsage` returns 0 for new users
   - Test `incrementFreeUsage` increments counter correctly
   - Test `resetFreeUsage` clears counter
   - Test handles localStorage quota exceeded gracefully
2. **Run tests:** `npm test creditStorage.test.js`
   - Expect FAILURE
3. **Implement functions:**
   ```javascript
   const TOKEN_KEY = 'citation_checker_token';
   const FREE_USAGE_KEY = 'citation_checker_free_used';

   export const saveToken = (token) => {
     try {
       localStorage.setItem(TOKEN_KEY, token);
     } catch (e) {
       console.error('Failed to save token:', e);
     }
   };

   export const getToken = () => {
     try {
       return localStorage.getItem(TOKEN_KEY);
     } catch (e) {
       return null;
     }
   };

   export const getFreeUsage = () => {
     try {
       return parseInt(localStorage.getItem(FREE_USAGE_KEY) || '0', 10);
     } catch (e) {
       return 0;
     }
   };

   export const incrementFreeUsage = (count) => {
     const current = getFreeUsage();
     localStorage.setItem(FREE_USAGE_KEY, String(current + count));
   };
   ```
4. **Run tests:**
   - Expect PASS
5. **Manual browser testing:**
   - Open DevTools → Application → Local Storage
   - Call functions in console
   - Verify values stored correctly

**Verification:**
- [ ] Tests pass
- [ ] Functions work in browser
- [ ] Handles errors gracefully

**Commits (2 separate commits):**
1. `test: add credit storage utilities tests`
2. `feat: implement credit storage utilities`

**If blocked:** STOP and ask user/architect.

---

### 👨‍💻 DEVELOPER TASK 4.2: Create useCredits Hook

**Context:** React hook to manage paid credit state across the app. Fetches balance from backend, provides refresh method, stores in React state for reactive UI updates.

**Files to create:**
- `frontend/frontend/src/hooks/useCredits.js`
- `frontend/frontend/src/hooks/useCredits.test.jsx`

**Hook interface:**
```javascript
const {
  credits,           // number | null
  loading,          // boolean
  error,            // string | null
  refreshCredits,   // () => Promise<void>
  hasToken          // boolean
} = useCredits();
```

**Execution steps:**
1. **Write tests:**
   - Hook fetches credits on mount if token exists
   - Hook returns null if no token
   - `refreshCredits()` refetches from API
   - Loading state works correctly
   - Error state captures API failures
2. **Run tests:** `npm test useCredits.test.jsx`
   - Expect FAILURE
3. **Implement hook:**
   ```javascript
   import { useState, useEffect } from 'react';
   import { getToken } from '../utils/creditStorage';

   export const useCredits = () => {
     const [credits, setCredits] = useState(null);
     const [loading, setLoading] = useState(false);
     const [error, setError] = useState(null);
     const token = getToken();

     const fetchCredits = async () => {
       if (!token) return;

       setLoading(true);
       setError(null);

       try {
         const response = await fetch(`/api/credits?token=${token}`);
         const data = await response.json();
         setCredits(data.credits);
       } catch (e) {
         setError(e.message);
       } finally {
         setLoading(false);
       }
     };

     useEffect(() => {
       fetchCredits();
     }, [token]);

     return {
       credits,
       loading,
       error,
       refreshCredits: fetchCredits,
       hasToken: !!token
     };
   };
   ```
4. **Run tests:**
   - Expect PASS

**Verification:**
- [ ] Tests pass
- [ ] Hook fetches correctly

**Commits (2 separate commits):**
1. `test: add useCredits hook tests`
2. `feat: implement useCredits React hook`

**If blocked:** STOP and ask user/architect.

---

### 👨‍💻 DEVELOPER TASK 4.3: Add Credit Display to Header

**Context:** Show "Citation Credits: 847" in header for paid users. Only visible if user has token. Updates automatically when credits change.

**Files to modify:**
- `frontend/frontend/src/App.jsx` (modify header section around lines 101-111)
- `frontend/frontend/src/components/CreditDisplay.jsx` (new)
- `frontend/frontend/src/components/CreditDisplay.test.jsx` (new)
- `frontend/frontend/src/App.css` (add styles)

**Execution steps:**
1. **Write tests:**
   - Component renders nothing if no token
   - Component displays credits if token exists
   - Component shows loading state
   - Component updates when credits prop changes
2. **Run tests:** `npm test CreditDisplay.test.jsx`
   - Expect FAILURE
3. **Create `CreditDisplay.jsx`:**
   ```jsx
   import { useCredits } from '../hooks/useCredits';

   export const CreditDisplay = () => {
     const { credits, loading, hasToken } = useCredits();

     if (!hasToken) return null;
     if (loading) return <span className="credit-display">Loading...</span>;

     return (
       <span className="credit-display">
         Citation Credits: {credits || 0}
       </span>
     );
   };
   ```
4. **Modify App.jsx header (around line 102):**
   ```jsx
   <header className="header">
     <div className="header-content">
       <div className="logo">
         {/* existing logo code */}
       </div>
       <CreditDisplay />  {/* Add this line */}
     </div>
   </header>
   ```
5. **Add CSS to App.css:**
   ```css
   .header-content {
     display: flex;
     justify-content: space-between;
     align-items: center;
   }

   .credit-display {
     font-size: 0.9rem;
     color: var(--primary-color);
     font-weight: 500;
   }
   ```
6. **Run tests:**
   - Expect PASS
7. **Manual testing:**
   - Add token to localStorage in browser console: `localStorage.setItem('citation_checker_token', 'test-123')`
   - Reload page
   - Verify display appears in header

**Verification:**
- [ ] Tests pass
- [ ] Display appears for paid users
- [ ] Hidden for free users
- [ ] Styling matches site theme

**Commits (2 separate commits):**
1. `test: add credit display tests`
2. `feat: add credit balance display to header`

**If blocked:** STOP and ask user/architect.

---

## Phase 5: Frontend - Premium Flow

### 👨‍💻 DEVELOPER TASK 5.1: Create UpgradeModal Component

**Context:** Modal that appears when user needs credits. Shows pricing ($8.99 for 1,000), redirects to Polar checkout.

**Files to create:**
- `frontend/frontend/src/components/UpgradeModal.jsx`
- `frontend/frontend/src/components/UpgradeModal.test.jsx`
- `frontend/frontend/src/components/UpgradeModal.css`

**Execution steps:**
1. **Write tests:**
   - Modal opens/closes correctly
   - "Continue to Checkout" calls `/api/create-checkout`
   - Redirects to checkout_url on success
   - Shows error if API fails
   - Shows loading state during API call
2. **Run tests:** `npm test UpgradeModal.test.jsx`
   - Expect FAILURE
3. **Implement component:**
   - Modal overlay with centered card
   - **Title:** "Get 1,000 Citation Credits"
   - **Price:** "$8.99"
   - **Subtitle:** "Credits never expire"
   - **Benefits list:**
     - ✓ Check unlimited citations
     - ✓ No subscription
     - ✓ Lifetime access
   - **CTA button:** "Continue to Checkout"
   - On click:
     ```javascript
     const handleCheckout = async () => {
       setLoading(true);
       try {
         const token = getToken();
         const response = await fetch('/api/create-checkout', {
           method: 'POST',
           headers: { 'Content-Type': 'application/json' },
           body: JSON.stringify({ token })
         });
         const { checkout_url } = await response.json();
         window.location.href = checkout_url;  // Redirect to Polar
       } catch (e) {
         setError(e.message);
       } finally {
         setLoading(false);
       }
     };
     ```
   - **Close button (X)** in top-right corner
4. **Style modal (UpgradeModal.css):**
   - Purple theme matching site
   - Centered overlay
   - Clean, professional design
   - Responsive (mobile-friendly)
5. **Run tests:**
   - Expect PASS
6. **Manual testing:**
   - Import and render modal in App
   - Click "Continue to Checkout"
   - Should redirect to Polar sandbox checkout

**Verification:**
- [ ] Tests pass
- [ ] Modal styled correctly
- [ ] Checkout redirect works
- [ ] Loading/error states work

**Commits (2 separate commits):**
1. `test: add upgrade modal tests`
2. `feat: create upgrade modal component`

**If blocked:** STOP and ask user/architect.

---

### 👨‍💻 DEVELOPER TASK 5.2: Create PartialResults Component

**Context:** Display when user has insufficient credits. Shows validated citations fully, displays locked citations with paywall.

**Files to create:**
- `frontend/frontend/src/components/PartialResults.jsx`
- `frontend/frontend/src/components/PartialResults.test.jsx`
- `frontend/frontend/src/components/PartialResults.css`

**Component props:**
```javascript
{
  results: [...],              // Validated citations
  partial: true,
  citations_checked: 3,
  citations_remaining: 7,
  onUpgrade: () => void       // Callback to show upgrade modal
}
```

**Execution steps:**
1. **Write tests:**
   - Displays validated citations with full error details
   - Shows locked citations count
   - "Upgrade" button calls onUpgrade callback
2. **Run tests:** `npm test PartialResults.test.jsx`
   - Expect FAILURE
3. **Implement component:**
   - Render full results for checked citations (reuse existing citation result cards from App.jsx)
   - After validated results, show locked section:
     ```jsx
     <div className="locked-results">
       <div className="lock-icon">🔒</div>
       <p className="lock-message">
         {citations_remaining} more citation{citations_remaining > 1 ? 's' : ''} checked
       </p>
       <p className="lock-subtitle">Upgrade to see all results</p>
       <button className="upgrade-button" onClick={onUpgrade}>
         Get 1,000 Citation Credits for $8.99
       </button>
     </div>
     ```
4. **Style component:**
   - Locked section has light gray background
   - Clear visual separation from validated results
   - Button matches site theme
5. **Run tests:**
   - Expect PASS

**Verification:**
- [ ] Tests pass
- [ ] UI matches site design
- [ ] Callback works correctly

**Commits (2 separate commits):**
1. `test: add partial results tests`
2. `feat: create partial results component`

**If blocked:** STOP and ask user/architect.

---

### 👨‍💻 DEVELOPER TASK 5.3: Create Success Page with Polling

**Context:** After Polar payment, user redirects here. Page saves token, **polls for credits** (webhook may be delayed 0-30 seconds), shows success message, provides citation input.

**Critical:** Webhook may not arrive immediately. Polling ensures credits are available before user tries to use them.

**Files to create:**
- `frontend/frontend/src/pages/Success.jsx`
- `frontend/frontend/src/pages/Success.test.jsx`
- Configure React Router route

**Polling logic:**
```
1. Extract token from URL: ?token=abc-123
2. Save to localStorage
3. Poll /api/credits every 2 seconds
4. When credits > 0: Show success, stop polling
5. Timeout after 30 seconds: Show error
```

**Execution steps:**
1. **Write tests:**
   - Extracts token from URL query param
   - Saves token to localStorage
   - Shows "Activating..." while polling
   - Shows success when credits appear
   - Shows timeout error after 30 seconds
   - Banner stays visible until scroll
2. **Run tests:** `npm test Success.test.jsx`
   - Expect FAILURE
3. **Implement Success.jsx:**
   ```jsx
   import { useState, useEffect } from 'react';
   import { saveToken } from '../utils/creditStorage';

   const Success = () => {
     const [status, setStatus] = useState('activating');  // activating | success | error
     const [credits, setCredits] = useState(0);

     useEffect(() => {
       // Extract token from URL
       const params = new URLSearchParams(window.location.search);
       const token = params.get('token');

       if (!token) {
         setStatus('error');
         return;
       }

       // Save token
       saveToken(token);

       // Poll for credits
       let attempts = 0;
       const maxAttempts = 15;  // 30 seconds (15 * 2s)

       const pollCredits = async () => {
         try {
           const response = await fetch(`/api/credits?token=${token}`);
           const data = await response.json();

           if (data.credits > 0) {
             setCredits(data.credits);
             setStatus('success');
             clearInterval(interval);
           } else if (attempts++ >= maxAttempts) {
             setStatus('error');
             clearInterval(interval);
           }
         } catch (e) {
           console.error('Error polling credits:', e);
         }
       };

       const interval = setInterval(pollCredits, 2000);
       pollCredits();  // Call immediately

       return () => clearInterval(interval);
     }, []);

     if (status === 'activating') {
       return (
         <div className="success-page">
           <div className="activating-spinner">Activating your credits...</div>
         </div>
       );
     }

     if (status === 'error') {
       return (
         <div className="success-page">
           <div className="error-message">
             Error: Credits not activated. Please contact support.
           </div>
         </div>
       );
     }

     return (
       <div className="success-page">
         <div className="success-banner">
           ✅ Payment Successful! You now have {credits} Citation Credits
         </div>
         {/* TODO: Include citation input box here (copy from App.jsx) */}
       </div>
     );
   };

   export default Success;
   ```
4. **Add React Router route:**
   - If using React Router, add route: `<Route path="/success" element={<Success />} />`
   - If not using router, handle route in main App component
5. **Add scroll listener** to hide banner after user scrolls
6. **Run tests:**
   - Expect PASS
7. **Manual testing:**
   - Complete test Polar purchase
   - Should redirect to `/success?token=...`
   - Verify "Activating..." appears
   - Wait for credits to appear
   - Check localStorage has token

**Verification:**
- [ ] Tests pass
- [ ] Polling works correctly
- [ ] Token saved to localStorage
- [ ] Success message displays
- [ ] Error handling works (timeout)

**Commits (2 separate commits):**
1. `test: add success page tests`
2. `feat: create payment success page with credit polling`

**If blocked:** STOP and ask user/architect.

---

### 👨‍💻 DEVELOPER TASK 5.4: Integrate Credit System into Main App

**Context:** Connect all pieces in App.jsx. Check free tier before submission, handle partial results, trigger upgrade modal, send token with requests.

**Files to modify:**
- `frontend/frontend/src/App.jsx`
- `frontend/frontend/src/App.test.jsx`

**Execution steps:**
1. **Update tests:**
   - App sends X-User-Token header in validation requests
   - App shows UpgradeModal when free tier exhausted (>= 10)
   - App displays PartialResults when response.partial === true
   - App increments free usage counter after successful validation
   - App refreshes credits after validation (paid users)
2. **Run tests:** `npm test App.test.jsx`
   - Expect FAILURE
3. **Modify App.jsx:**

   **Add imports:**
   ```javascript
   import { getToken, getFreeUsage, incrementFreeUsage } from './utils/creditStorage';
   import { UpgradeModal } from './components/UpgradeModal';
   import { PartialResults } from './components/PartialResults';
   ```

   **Add state:**
   ```javascript
   const [showUpgradeModal, setShowUpgradeModal] = useState(false);
   ```

   **Before handleSubmit API call (around line 38-52):**
   ```javascript
   const handleSubmit = async (e) => {
     e.preventDefault();

     if (!editor) return;

     const token = getToken();
     const freeUsed = getFreeUsage();

     // Check free tier limit
     if (!token && freeUsed >= 10) {
       setShowUpgradeModal(true);
       return;
     }

     const htmlContent = editor.getHTML();
     const textContent = editor.getText();

     setLoading(true);
     setError(null);
     setResults(null);

     try {
       // Build headers
       const headers = { 'Content-Type': 'application/json' };
       if (token) {
         headers['X-User-Token'] = token;
       }

       // Make API call
       const response = await fetch('/api/validate', {
         method: 'POST',
         headers,
         body: JSON.stringify({ citations: htmlContent, style: 'apa7' }),
       });

       if (!response.ok) {
         const errorData = await response.json();
         throw new Error(errorData.detail || errorData.error || 'Validation failed');
       }

       const data = await response.json();

       // Handle response
       if (data.partial) {
         // Partial results (insufficient credits)
         setResults({ ...data, isPartial: true });
       } else {
         // Full results
         setResults(data);

         // Increment free counter if no token
         if (!token) {
           incrementFreeUsage(data.results.length);
         }
       }
     } catch (err) {
       setError(err.message);
     } finally {
       setLoading(false);
     }
   };
   ```

   **Modify results display section (around line 160-228):**
   ```jsx
   {error && (
     <div className="error">
       <strong>Error:</strong> {error}
     </div>
   )}

   {results && (
     results.isPartial ? (
       <PartialResults
         results={results.results}
         partial={results.partial}
         citations_checked={results.citations_checked}
         citations_remaining={results.citations_remaining}
         onUpgrade={() => setShowUpgradeModal(true)}
       />
     ) : (
       <div className="results">
         {/* Existing full results display - keep as is */}
       </div>
     )
   )}
   ```

   **Add modal to JSX (before closing tag of main div, around line 305):**
   ```jsx
   {showUpgradeModal && (
     <UpgradeModal onClose={() => setShowUpgradeModal(false)} />
   )}
   ```

4. **Run tests:**
   - Expect PASS
5. **End-to-end manual testing:**
   - Clear localStorage
   - Submit 5 citations → check localStorage: `citation_checker_free_used` should be 5
   - Submit 5 more → should be 10
   - Try to submit more → upgrade modal should appear
   - Complete purchase flow (sandbox)
   - Verify paid usage works
   - Test partial results (manually set low credits in DB)

**Verification:**
- [ ] All tests pass
- [ ] Free tier flow works (10 limit)
- [ ] Upgrade modal triggers correctly
- [ ] Paid tier validation works
- [ ] Partial results display correctly
- [ ] Credits deducted properly

**Commits (2 separate commits):**
1. `test: update app integration tests for credit system`
2. `feat: integrate credit system into main app`

**If blocked:** STOP and ask user/architect.

---

## Phase 6: Frontend - Content Redesign

### 👨‍💻 DEVELOPER TASK 6.1: Update Hero Section Copy

**Context:** Revise messaging to emphasize speed, accuracy, competitive advantage.

**Files to modify:**
- `frontend/frontend/src/App.jsx` (hero section around lines 114-127)

**Execution:**
1. **Update title (line ~117):**
   - Change to: `"Stop wasting 5 minutes on every citation"`
2. **Update subtitle (line ~120):**
   - Change to: `"The fastest, most accurate APA citation checker."`
3. **Replace yellow stat banner (lines ~122-125):**
   - Remove: `"⚠️ 90.9% of papers contain formatting errors"`
   - New content:
     ```jsx
     <div className="hero-stat">
       <span className="stat-text">
         ⚡ Instant validation • Catches citation generator errors • No sign up required
       </span>
     </div>
     ```
4. **Visual QA:**
   - Test on mobile (DevTools responsive mode)
   - Test on tablet
   - Test on desktop
   - Verify text wraps properly

**Verification:**
- [ ] New copy displays correctly
- [ ] Responsive on all screen sizes
- [ ] No layout breaks

**Commit:** `feat: update hero section messaging`

**If blocked:** STOP and ask user/architect.

---

### 🤝 COLLABORATIVE TASK 6.2: Create Hero Illustration SVG

**👨‍💻 Developer: Create Placeholder SVG**

**Context:** Need 3-step visual (paste → validate → correct) for hero section. Creating simple placeholder first, can be replaced by professional design later.

**Files to create:**
- `frontend/frontend/src/assets/hero-illustration.svg`

**Execution:**
1. **Create simple placeholder SVG:**
   - 3 vertical sections
   - Section 1: Rectangle with "1. Paste" text
   - Section 2: Rectangle with "2. Validate" text
   - Section 3: Rectangle with "3. Correct" text
   - Arrows connecting them
   - Basic colors (purple/gray)
   - Keep file size < 10KB
2. **Add to App.jsx hero section:**
   ```jsx
   <section className="hero">
     <div className="hero-content">
       <div className="hero-text">
         <h2 className="hero-title">...</h2>
         <p className="hero-subtitle">...</p>
         <div className="hero-stat">...</div>
       </div>
       <div className="hero-illustration">
         <img src="/src/assets/hero-illustration.svg" alt="Citation checking process" />
       </div>
     </div>
   </section>
   ```
3. **Add CSS for layout:**
   ```css
   .hero-content {
     display: flex;
     gap: 2rem;
     align-items: center;
   }

   .hero-text {
     flex: 0 0 70%;
   }

   .hero-illustration {
     flex: 0 0 30%;
   }

   @media (max-width: 768px) {
     .hero-content {
       flex-direction: column;
     }

     .hero-text,
     .hero-illustration {
       flex: 1 1 100%;
     }
   }
   ```
4. **Test responsive behavior**

**Verification:**
- [ ] SVG displays
- [ ] Responsive (stacks on mobile)
- [ ] File size reasonable

**Commit:** `feat: add hero illustration placeholder SVG`

**👤 User: Provide Design Brief to Designer (Optional - Future Enhancement)**

The placeholder SVG can be replaced later with professional design using this brief:

---

**Hero Illustration Design Brief**

**Purpose:** Visual representation of citation checking process for homepage hero

**Placement:** Right side of hero (30% width desktop, below text mobile)

**Concept:** 3-step flow showing:
1. **Input:** Document icon with citation text | Label: "1. Paste citations" | Color: Light purple/gray
2. **Processing:** Magnifying glass/AI with red error marks | Label: "2. AI validates" | Color: Purple + red
3. **Output:** Citation with green checkmarks | Label: "3. Get corrections" | Color: Green

**Flow:** Connect with arrows between steps

**Style:** Professional, academic, modern SVG (not cartoonish)

**Colors:** Purple (brand), Green (success), Red (errors), Gray (neutral)

**Technical:** SVG, ~400-600px wide, <50KB, aria labels

---

**If blocked:** STOP and ask user/architect.

---

### 👨‍💻 DEVELOPER TASK 6.3: Update Input Section Copy

**Context:** Update micro-text below CTA button.

**Files to modify:**
- `frontend/frontend/src/App.jsx` (input section around lines 130-152)

**Execution:**
1. **After "Check My Citations" button (around line 142), add:**
   ```jsx
   <button type="submit" disabled={loading || !editor || hasPlaceholder}>
     {loading ? 'Validating...' : 'Check My Citations'}
   </button>

   <p className="cta-micro-text">
     No login required • Get results in seconds
   </p>

   {/* Feature pills stay below */}
   <div className="feature-pills">...</div>
   ```
2. **Add CSS to App.css:**
   ```css
   .cta-micro-text {
     font-size: 0.85rem;
     color: #6b7280;
     text-align: center;
     margin: 0.5rem 0 1rem 0;
   }
   ```
3. **Visual QA**

**Verification:**
- [ ] Micro-text displays
- [ ] Properly styled
- [ ] Doesn't over-promise "free"

**Commit:** `feat: add CTA micro-text to input section`

**If blocked:** STOP and ask user/architect.

---

### 👨‍💻 DEVELOPER TASK 6.4: Update Benefits Section

**Context:** Replace "Save hours" benefit with accuracy-focused messaging.

**Files to modify:**
- `frontend/frontend/src/App.jsx` (benefits section around lines 231-258)

**Execution:**
1. **Replace benefit #1 (currently "Save hours"):**
   ```jsx
   <div className="benefit-card">
     <div className="benefit-icon">🎯</div>
     <h4 className="benefit-title">Catches 99% of errors</h4>
     <p className="benefit-text">
       Our AI validates against official APA 7th Edition rules — more accurate than any generator or LLM.
     </p>
   </div>
   ```
2. **Update benefit #2 (generator errors):**
   ```jsx
   <div className="benefit-card">
     <div className="benefit-icon">🎯</div>
     <h4 className="benefit-title">Catch generator errors</h4>
     <p className="benefit-text">
       Zotero, EasyBib, and ChatGPT make formatting mistakes. We find them before your professor does.
     </p>
   </div>
   ```
3. **Keep benefit #3 ("Never lose points") as-is**
4. **Add benefit #4:**
   ```jsx
   <div className="benefit-card">
     <div className="benefit-icon">💜</div>
     <h4 className="benefit-title">Trusted by researchers worldwide</h4>
     <p className="benefit-text">
       Join thousands of students and academics who rely on us to perfect their citations.
     </p>
   </div>
   ```
5. **Update grid CSS if needed** (should handle 4 cards)

**Verification:**
- [ ] All 4 cards display
- [ ] Grid balanced
- [ ] Responsive

**Commit:** `feat: update benefits section with accuracy messaging`

**If blocked:** STOP and ask user/architect.

---

### 👨‍💻 DEVELOPER TASK 6.5: Create "Why We're Different" Section

**Context:** New section explaining custom AI, expert verification, competitive advantages.

**Files to modify:**
- `frontend/frontend/src/App.jsx` (add after benefits section, around line 258)
- `frontend/frontend/src/App.css` (add styles)

**Execution:**
1. **After benefits `</section>` closing tag, add:**
   ```jsx
   <section className="why-different">
     <div className="why-different-content">
       <h3 className="why-different-title">Why Citation Format Checker is Different</h3>
       <div className="why-grid">
         <div className="why-card">
           <h4>Custom AI Models</h4>
           <p>Trained on thousands of expert-verified citations for each source type</p>
         </div>
         <div className="why-card">
           <h4>APA Expert Verified</h4>
           <p>Every error type validated against official APA 7th Edition manual</p>
         </div>
         <div className="why-card">
           <h4>99% Accuracy</h4>
           <p>Significantly more accurate than ChatGPT, Zotero, and EasyBib</p>
         </div>
       </div>
       <p className="why-footnote">
         Unlike general AI tools, our models specialize exclusively in citation formatting
       </p>
     </div>
   </section>
   ```
2. **Add CSS to App.css:**
   ```css
   .why-different {
     background-color: #f9fafb;
     padding: 4rem 2rem;
   }

   .why-different-content {
     max-width: 1200px;
     margin: 0 auto;
   }

   .why-different-title {
     font-size: 2rem;
     text-align: center;
     margin-bottom: 2rem;
   }

   .why-grid {
     display: grid;
     grid-template-columns: repeat(3, 1fr);
     gap: 2rem;
     margin-bottom: 1.5rem;
   }

   .why-card {
     background: white;
     padding: 1.5rem;
     border-radius: 8px;
     box-shadow: 0 1px 3px rgba(0,0,0,0.1);
   }

   .why-card h4 {
     font-size: 1.25rem;
     margin-bottom: 0.5rem;
     color: var(--primary-color);
   }

   .why-footnote {
     text-align: center;
     font-size: 0.9rem;
     color: #6b7280;
     font-style: italic;
   }

   @media (max-width: 768px) {
     .why-grid {
       grid-template-columns: 1fr;
     }
   }
   ```
3. **Visual QA**

**Verification:**
- [ ] Section displays
- [ ] 3-column grid (desktop)
- [ ] Stacks on mobile
- [ ] Styling matches site theme

**Commit:** `feat: add 'Why We're Different' section`

**If blocked:** STOP and ask user/architect.

---

### 👨‍💻 DEVELOPER TASK 6.6: Update FAQ Section

**Context:** Update pricing FAQ, add credit-related questions.

**Prerequisites:** User must provide refund policy text (see Prerequisites section).

**Files to modify:**
- `frontend/frontend/src/App.jsx` (FAQ section around lines 261-297)

**Execution:**
1. **Update existing FAQ #2 ("Is this free?"):**
   ```jsx
   <div className="faq-item">
     <h4 className="faq-question">Is this citation checker free?</h4>
     <p className="faq-answer">
       Yes! You get 10 free citation checks to try the tool. For unlimited checking,
       you can purchase 1,000 Citation Credits for $8.99. Credits never expire.
     </p>
   </div>
   ```
2. **Add new FAQ after existing #5:**
   ```jsx
   <div className="faq-item">
     <h4 className="faq-question">What are Citation Credits and how do they work?</h4>
     <p className="faq-answer">
       Each citation you check uses 1 credit. When you purchase 1,000 credits for $8.99,
       you can check 1,000 citations. Credits never expire and can be used anytime.
     </p>
   </div>

   <div className="faq-item">
     <h4 className="faq-question">Do Citation Credits expire?</h4>
     <p className="faq-answer">
       No! Your credits never expire. Use them at your own pace — whether that's all at
       once or over several years.
     </p>
   </div>

   <div className="faq-item">
     <h4 className="faq-question">Can I get a refund?</h4>
     <p className="faq-answer">
       {/* USE EXACT TEXT PROVIDED BY USER IN PREREQUISITES */}
     </p>
   </div>

   <div className="faq-item">
     <h4 className="faq-question">How is this different from ChatGPT or citation generators?</h4>
     <p className="faq-answer">
       ChatGPT and tools like Zotero or EasyBib make formatting errors because they're not
       specialized for citation validation. Our AI models are custom-trained exclusively on
       APA 7th Edition rules with expert verification, achieving 99% accuracy.
     </p>
   </div>
   ```

**Verification:**
- [ ] All FAQs display
- [ ] Refund policy accurate
- [ ] Pricing info correct ($8.99, 1,000 credits)

**Commit:** `feat: update FAQ with credit pricing and comparison questions`

**If blocked (missing refund policy):** STOP and ask user/architect.

---

## Phase 7: Testing & Deployment

### 👨‍💻 DEVELOPER TASK 7.1: End-to-End Local Testing

**Context:** Validate entire premium flow with Polar sandbox before production deployment.

**Prerequisites:**
- ngrok running and configured in Polar
- Backend running with sandbox credentials
- Frontend running

**Execution steps:**

**Setup verification:**
1. Activate venv: `source venv/bin/activate`
2. Verify ngrok running: `ngrok http 8000`
3. Start backend: `python3 backend/app.py`
4. Start frontend: `cd frontend/frontend && npm run dev`
5. Verify Polar webhook points to ngrok URL

**Test 1: Free Tier Flow**
1. Clear localStorage in browser (DevTools → Application → Clear)
2. Paste 5 citations, click "Check My Citations"
3. Verify validation works
4. Check localStorage: `citation_checker_free_used` should be 5
5. Paste 5 more citations, submit
6. Check localStorage: should be 10
7. Try to paste more citations, submit
8. **Expected:** Upgrade modal appears
9. **Result:** PASS / FAIL (if fail, STOP and ask user/architect)

**Test 2: Upgrade Flow**
1. Click "Get Citation Credits" button
2. **Expected:** Modal appears with $8.99 pricing
3. Click "Continue to Checkout"
4. **Expected:** Redirects to Polar sandbox checkout page
5. Fill in test card:
   - Card: 4242 4242 4242 4242
   - Expiry: Any future date
   - CVV: Any 3 digits
   - Name: Test User
6. Complete payment
7. **Expected:** Redirects to /success?token=...
8. **Result:** PASS / FAIL

**Test 3: Credit Activation (Webhook)**
1. On success page, **Expected:** "Activating your credits..." message
2. Wait up to 30 seconds
3. Monitor backend logs in terminal for webhook received
4. **Expected:** Success message appears: "✅ Payment Successful! You now have 1,000 Citation Credits"
5. Check database:
   ```bash
   sqlite3 backend/credits.db "SELECT * FROM users;"
   ```
6. **Expected:** User record with 1,000 credits
7. **Result:** PASS / FAIL

**Test 4: Paid Usage**
1. On success page, paste 5 citations, submit
2. **Expected:** Validation works
3. Check database:
   ```bash
   sqlite3 backend/credits.db "SELECT credits FROM users WHERE token='your-token-here';"
   ```
4. **Expected:** Credits = 995
5. Check header: **Expected:** "Citation Credits: 995" displays
6. **Result:** PASS / FAIL

**Test 5: Partial Results**
1. Manually set credits to 3:
   ```bash
   sqlite3 backend/credits.db "UPDATE users SET credits = 3 WHERE token='your-token-here';"
   ```
2. Paste 10 citations, submit
3. **Expected:** Only 3 results shown with full details
4. **Expected:** "🔒 7 more citations checked" message appears
5. **Expected:** "Upgrade" button visible
6. Click "Upgrade" button
7. **Expected:** Modal appears
8. **Result:** PASS / FAIL

**Test 6: Idempotency (Duplicate Webhook)**
1. Note current credits
2. In Polar dashboard: Webhooks → find recent webhook → "Resend"
3. Wait 5 seconds
4. Check database: `sqlite3 backend/credits.db "SELECT credits FROM users WHERE token='your-token-here';"`
5. **Expected:** Credits unchanged (idempotency working)
6. **Result:** PASS / FAIL

**Document results:**
Create file `backend/test_results_local.md` with:
- All test results (PASS/FAIL)
- Any issues encountered
- Screenshots if helpful

**Verification checklist:**
- [ ] Free tier works (10 limit enforced)
- [ ] Upgrade modal triggers
- [ ] Polar checkout completes
- [ ] Webhook fires within 30 seconds
- [ ] Credits activated
- [ ] Paid validation deducts credits
- [ ] Header shows credit balance
- [ ] Partial results work
- [ ] Idempotency prevents duplicate credits

**Commit:** `test: document local end-to-end testing results`

**If any test FAILS:** STOP and ask user/architect for guidance.

---

### 👤 USER TASK 7.2: Configure Production Polar Environment

**Prerequisites:** Task 7.1 (local testing) must PASS completely before proceeding.

**Steps:**
1. Log in to [polar.sh](https://polar.sh)
2. Toggle OFF "Sandbox Mode"
3. Create production API key (Settings → API Keys)
4. Create production product:
   - Name: "1,000 Citation Credits"
   - Price: $8.99
   - Type: One-time purchase
5. Configure production webhook:
   - URL: `https://citationformatchecker.com/api/polar-webhook`
   - Events: ✅ checkout.created, ✅ checkout.updated, ✅ order.created
6. **Provide to developer:**
   - Production API key (format: `polar_live_...`)
   - Production product ID (format: `prod_...`)
   - Production webhook secret (format: `whsec_...`)

---

### 👨‍💻 DEVELOPER TASK 7.3: Update Production Environment Variables & Code

**Context:** Configure production VPS with Polar production credentials AND remove sandbox API configuration from code.

**Prerequisites:** User must provide production credentials (Task 7.2).

**Execution steps:**

**Part A: Update Environment Variables**
1. SSH to VPS: `ssh deploy@178.156.161.140`
2. Navigate to app: `cd /opt/citations`
3. Edit environment file: `nano backend/.env`
4. Update Polar credentials:
   ```bash
   # Replace sandbox with production values
   POLAR_ACCESS_TOKEN=polar_live_...  # From user (NOT polar_sandbox_...)
   POLAR_PRODUCT_ID=prod_...           # From user
   POLAR_WEBHOOK_SECRET=whsec_...      # From user

   # Update frontend URL
   FRONTEND_URL=https://citationformatchecker.com

   # Keep existing vars
   OPENAI_API_KEY=...  # Don't change
   ```
5. Save and exit (Ctrl+X, Y, Enter)

**Part B: ⚠️ CRITICAL - Remove Sandbox API Configuration**
6. Edit backend code: `nano backend/app.py`
7. Find the Polar client initialization (around line 26-30):
   ```python
   # Current code (SANDBOX - DO NOT USE IN PRODUCTION)
   from polar_sdk import SERVER_SANDBOX
   polar = Polar(
       access_token=os.getenv('POLAR_ACCESS_TOKEN'),
       server=SERVER_SANDBOX  # Use sandbox API endpoint
   )
   ```
8. **Replace with production configuration:**
   ```python
   # Production code (remove SERVER_SANDBOX import and parameter)
   polar = Polar(
       access_token=os.getenv('POLAR_ACCESS_TOKEN')
       # No server parameter = defaults to production API
   )
   ```
9. Save and exit (Ctrl+X, Y, Enter)

**Part C: Verify Configuration**
10. **Verify `.env` is NOT in git:**
    ```bash
    git status  # Should NOT show .env as modified
    ```
11. **If `.env` appears in git status:** STOP and ask user/architect
12. **Commit the code change:**
    ```bash
    git add backend/app.py
    git commit -m "chore: switch Polar client to production API endpoint"
    ```

**Verification:**
- [ ] Production credentials in `.env`
- [ ] FRONTEND_URL updated to production domain
- [ ] `SERVER_SANDBOX` import removed from code
- [ ] `server=SERVER_SANDBOX` parameter removed from Polar()
- [ ] Code change committed to git
- [ ] `.env` not tracked by git

**⚠️ CRITICAL:** If you forget to remove `SERVER_SANDBOX`, production checkouts will fail with "invalid credentials" errors because production tokens won't work with sandbox API.

**Do NOT commit .env file**

**If blocked:** STOP and ask user/architect.

---

### 👨‍💻 DEVELOPER TASK 7.4: Deploy to Production

**Context:** Deploy all changes to production VPS using existing deployment script.

**Prerequisites:**
- All local tests PASS (Task 7.1)
- Production environment configured (Task 7.3)
- All code committed to git

**Execution steps:**
1. **Verify all changes committed locally:**
   ```bash
   git status  # Should show "nothing to commit, working tree clean"
   ```
2. **If uncommitted changes exist:** STOP and commit them first
3. **Push to GitHub:**
   ```bash
   git push origin main
   ```
4. **SSH to VPS:**
   ```bash
   ssh deploy@178.156.161.140
   ```
5. **Navigate to app directory:**
   ```bash
   cd /opt/citations
   ```
6. **Run deployment script:**
   ```bash
   ./deployment/scripts/deploy.sh
   ```
7. **Monitor deployment output for errors**
   - Script should:
     - Pull latest code from GitHub
     - Activate venv
     - Install Python dependencies
     - Install npm dependencies (frontend)
     - Build React app
     - Restart systemd service
8. **Check backend status:**
   ```bash
   sudo systemctl status citations-backend
   ```
   - **Expected:** "active (running)"
9. **Monitor backend logs:**
   ```bash
   sudo journalctl -u citations-backend -f
   ```
   - Look for startup logs
   - Verify no errors
   - Ctrl+C to exit
10. **Test frontend:**
    - Open browser: https://citationformatchecker.com
    - **Expected:** Site loads with new hero messaging
11. **Test backend API:**
    ```bash
    curl https://citationformatchecker.com/health
    ```
    - **Expected:** `{"status": "ok"}`

**Verification checklist:**
- [ ] Deployment script completes without errors
- [ ] Backend service running
- [ ] No errors in logs
- [ ] Frontend loads correctly
- [ ] New hero messaging displays
- [ ] API health check responds

**Commit (after successful deployment):** `chore: deploy premium flow and homepage redesign to production`

**If deployment FAILS:** STOP and ask user/architect. Do NOT proceed to smoke test.

---

### 👤 USER TASK 7.5: Production Smoke Test

**Context:** Complete ONE real purchase to verify production Polar integration works correctly.

**Prerequisites:**
- Task 7.4 (deployment) must PASS
- You are willing to spend $8.99 for testing (can refund if needed)

**Steps:**

**Test Free Tier (Production):**
1. Open https://citationformatchecker.com (incognito window)
2. Paste 3 citations, click "Check My Citations"
3. **Expected:** Validation works
4. **Result:** PASS / FAIL

**Test Upgrade Flow (Production - REAL PAYMENT):**
1. Paste 10 more citations (trigger free tier limit)
2. **Expected:** Upgrade modal appears
3. Click "Get Citation Credits"
4. **Expected:** Redirects to Polar production checkout
5. **⚠️ REAL PAYMENT:** Complete checkout with real card ($8.99 charge)
6. **Expected:** Redirects to success page
7. **Result:** PASS / FAIL

**Test Credit Activation:**
1. On success page, **Expected:** "Activating credits..." message
2. Wait up to 30 seconds
3. **Expected:** "✅ Payment Successful! You now have 1,000 Citation Credits"
4. **Expected:** Header shows "Citation Credits: 1000"
5. **Result:** PASS / FAIL

**Test Paid Usage:**
1. On success page, paste 5 citations, submit
2. **Expected:** Validation works
3. **Expected:** Header shows "Citation Credits: 995"
4. **Result:** PASS / FAIL

**Inform developer:**
- Share all PASS/FAIL results
- If all PASS: **Production launch successful ✅**
- If any FAIL: Developer will investigate (provide error details)

**Optional: Process Refund**
If you want to refund the test purchase:
1. Go to Polar dashboard
2. Find the test order
3. Process refund
4. Note: Credits won't auto-deduct (no refund webhook handler implemented yet - future enhancement)

---

## Summary

**Total Tasks:** 29
- 👤 User tasks: 5 (Polar setup, refund policy, production config, smoke test)
- 👨‍💻 Developer tasks: 23 (implementation + testing)
- 🤝 Collaborative: 1 (hero illustration)

**Estimated Timeline:** 4-6 days for developer

**Git Commits:** ~40 following TDD (test + implementation pairs)

**Key Deliverables:**
- SQLite credit tracking (users + orders tables)
- 3 new backend endpoints (checkout, webhook, credits)
- Credit enforcement in validation
- Free tier (10 citations, localStorage)
- Paid tier (1,000 credits, $8.99, Polar)
- Premium upgrade modal + flow
- Success page with polling
- Partial results UI
- Redesigned homepage (hero, benefits, why different, FAQ)
- Placeholder hero illustration

**Critical Fixes Included:**
✅ Free tier enforcement (frontend-only, gameable but acceptable)
✅ Token transmission (X-User-Token header)
✅ Citation counting (after LLM, count results array)
✅ Webhook race condition (polling on success page)
✅ Database idempotency (orders table with order_id)
✅ Atomic credit operations (SQL WHERE clauses)
✅ Repeat purchases ADD credits
✅ Webhook signature verification
✅ Zero credits error handling
✅ venv activation instructions
✅ Clear user/developer task assignments
✅ Sandbox API configuration (SERVER_SANDBOX parameter)
✅ Webhook signature header (webhook-signature not X-Polar-Signature)
✅ Event type detection (isinstance checks)
✅ Metadata dict access (using .get() method)
✅ Async/sync API consistency (removed unnecessary await)

**User Needs to Provide:**
1. ✅ Polar sandbox credentials (Step 1-3 of Prerequisites)
2. ✅ Refund policy text (Step 4 of Prerequisites)
3. ✅ Polar production credentials (Task 7.2)
4. ✅ Production smoke test (Task 7.5)

**Developer Critical Instruction:**
⚠️ **DO NOT DEVIATE FROM PLAN - STOP AND ASK IF BLOCKED** ⚠️
