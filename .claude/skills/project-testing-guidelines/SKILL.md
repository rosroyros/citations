---
name: project-testing-guidelines
description: Guidelines and patterns for writing tests in this project. Use when creating, modifying, or debugging Playwright E2E tests (.spec.js files) or pytest backend tests (test_*.py files).
---

# Project Testing Guidelines

## Starting the Test Environment

### 1. Check if Backend is Running with Test Helpers
```bash
curl -s http://localhost:8000/test/health | grep -q '"testing": true' && echo "✅ Test backend ready" || echo "❌ Test backend not running"
```

### 2. If Not Running, Start Backend
```bash
cd backend
source venv/bin/activate
TESTING=true MOCK_LLM=true python3 -m uvicorn app:app --reload
```

### 3. Check if Frontend is Running
```bash
curl -s http://localhost:5173 > /dev/null && echo "✅ Frontend ready" || echo "❌ Frontend not running"
```

### 4. If Not Running, Start Frontend
```bash
cd frontend/frontend
npm run dev
```

**Environment Variables:**
- `TESTING=true` - **Required** - Enables test helper endpoints (`/test/*`)
- `MOCK_LLM=true` - Optional - Uses mock LLM responses for fast testing (no API calls)

**URLs:**
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`

---

## Test Directory Structure

### Playwright E2E Tests (Frontend)
```
frontend/frontend/tests/
├── analytics/           # GA4 tracking & analytics tests
│   ├── helpers.js       # Analytics capture utilities
│   ├── validate-analytics.spec.js
│   ├── upload-analytics.spec.js
│   └── results-revealed-analytics.spec.js
├── components/          # React component tests
│   ├── pricing-table-credits.spec.js
│   └── pricing-table-passes.spec.js
├── e2e/                 # End-to-end flow tests
│   ├── checkout/        # Payment & upgrade flows
│   │   ├── checkout-flow.spec.js
│   │   ├── pricing-integration.spec.js  # DB tests (serial)
│   │   ├── pricing_variants.spec.cjs    # DB tests (serial)
│   │   ├── upgrade-event.spec.cjs
│   │   ├── upgrade-funnel.spec.cjs
│   │   └── upgrade-tracking.spec.js
│   ├── core/            # Core validation features
│   │   ├── async-polling-validation.spec.js
│   │   ├── auto-scroll.spec.js
│   │   ├── e2e-full-flow.spec.cjs       # Production-only
│   │   ├── error-recovery.spec.js
│   │   └── markdown-formatting.spec.js
│   ├── gated-results/   # Freemium gating tests
│   ├── pseo/            # Programmatic SEO tests
│   │   └── pseo-smoke.spec.js
│   ├── ui/              # UI component integration
│   │   └── validation-table-header.spec.js
│   ├── upload/          # File upload tests
│   │   ├── file-processing.spec.js
│   │   └── upload.spec.js
│   └── user/            # User flow tests
│       ├── user-access.spec.js
│       └── user-tracking-flow.spec.js
├── helpers/             # Shared test utilities
│   └── test-utils.js
├── internal/            # VPN-only dashboard tests
│   └── e2e-internal-dashboard.spec.cjs
├── global-setup.js
└── global-teardown.js
```

### Pytest (Backend)
- **Location**: `tests/` and `backend/tests/` (Python)
- **Config**: `pytest.ini`
- **Run**: `source venv/bin/activate && pytest`

---

## Playwright Project Configuration

The test suite uses smart parallelization via Playwright projects:

| Project | Pattern | Parallel | Workers | Purpose |
|---------|---------|----------|---------|---------|
| `database-tests` | `pricing-integration.spec.js`, `pricing_variants.spec.cjs` | No | 1 | DB tests (SQLite WAL) |
| `chromium` | All others (excluding internal/*) | Yes | 4 | Main test suite |
| `firefox` | All others | Yes | 4 | Cross-browser |
| `webkit` | All others | Yes | 4 | Safari testing |
| `Mobile Chrome` | All others | Yes | 4 | Mobile viewport |
| `Mobile Safari` | All others | Yes | 4 | iOS viewport |

**Always ignored:**
- `**/internal/**` - VPN-only dashboard tests
- `**/e2e-full-flow.spec.cjs` - Production-only (run via deploy script)

---

## Critical Patterns

### 1. Database Tests Must Run Serially
Database tests (`pricing-integration.spec.js`, `pricing_variants.spec.cjs`) must run with `workers: 1` due to SQLite WAL visibility issues. The Playwright config handles this automatically.

### 2. Use Robust Waiting Patterns (Avoid waitForTimeout)
Replace `waitForTimeout` with proper waiting strategies:

```javascript
// ❌ DON'T: Fixed timeout
await page.waitForTimeout(2000);

// ✅ DO: Wait for condition
await expect(submitButton).toBeEnabled();
await expect(page.locator('[data-testid="results"]')).toBeVisible();

// ✅ DO: Wait for network
await page.waitForLoadState('networkidle');

// ✅ DO: Poll for state changes
await expect.poll(async () => {
  const text = await page.locator('.status').textContent();
  return text;
}, { timeout: 30000 }).toBe('Complete');
```

### 3. Database Polling for WAL Visibility
After writing to the database via test helpers, poll until the data is visible:
```javascript
await page.evaluate(async (userId) => {
  for (let i = 0; i < 60; i++) {
    const response = await fetch(`http://localhost:8000/test/get-user?user_id=${userId}`);
    const user = await response.json();
    if (user.has_pass) return;
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  throw new Error('Data not visible within timeout');
}, userId);
```

### 4. Handle Gated Results Overlay
Always check for and dismiss gated results before asserting on validation results:
```javascript
if (await page.locator('[data-testid="gated-results"]').first().isVisible()) {
  await page.locator('button:has-text("View Results")').first().click();
}
```

### 5. Analytics Testing Pattern
Use the analytics helpers for GA4 event testing:
```javascript
import { setupAnalyticsCapture, waitForEvent, getEventsByName } from '../analytics/helpers.js';

const capturedRequests = setupAnalyticsCapture(page);
// ... trigger action ...
const eventCaptured = await waitForEvent(capturedRequests, 'page_view', 5000);
expect(eventCaptured).toBe(true);
```

---

## Test Helper Endpoints

**Base URL**: `http://localhost:8000/test/` (requires `TESTING=true`)

| Endpoint | Method | Body | Purpose |
|----------|--------|------|---------|
| `/test/grant-pass` | POST | `{user_id, days}` | Grant a pass to user |
| `/test/grant-credits` | POST | `{user_id, amount}` | Grant credits |
| `/test/set-daily-usage` | POST | `{user_id, usage}` | Set daily usage count |
| `/test/get-user` | GET | `?user_id=X` | Get user state |
| `/test/get-validation` | GET | `?user_id=X` or `?job_id=X` | Get validation state |
| `/test/reset-user` | POST | `{user_id}` | Reset user to initial state |
| `/test/simulate-webhook` | POST | `{user_id, ...}` | Simulate Polar webhook |
| `/test/health` | GET | - | Health check for test env |

---

## Test Job Indicator
Use `"testtesttest"` in citations to flag test jobs. These are filtered from dashboard metrics.

---

## Anti-Patterns to Avoid

1. **DON'T** use `waitForTimeout` for waiting on state - use `expect.poll()` or `waitFor()`
2. **DON'T** assume data is immediately visible after database writes - poll for state
3. **DON'T** forget to handle gated results overlay in E2E tests
4. **DON'T** modify database tests to run in parallel - they share SQLite
5. **DON'T** hardcode variant values - use `localStorage.setItem('experiment_v1', 'X')`
6. **DON'T** start backend without `TESTING=true` when running E2E tests
7. **DON'T** run internal tests locally - they require VPN access

---

## Running Tests

### Playwright E2E - Common Commands
```bash
cd frontend/frontend

# Run all tests on Chromium (default)
npx playwright test --project=chromium

# Run database tests only (serial execution)
npx playwright test --project=database-tests

# Run a specific test file
npx playwright test tests/e2e/core/auto-scroll.spec.js

# Run tests matching a pattern
npx playwright test -g "auto-scroll"

# Run with headed browser (for debugging)
npx playwright test --headed

# Run cross-browser suite
npx playwright test --project=firefox --project=webkit
```

### Pytest
```bash
source venv/bin/activate
pytest                                 # All tests
pytest tests/test_app.py              # Single file
pytest -k "test_name"                 # By name pattern
```

---

## Related Skills
- `superpowers:test-driven-development` - TDD workflow
- `superpowers:testing-anti-patterns` - Common testing mistakes
