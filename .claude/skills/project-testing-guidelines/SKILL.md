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

## Test Infrastructure

### Playwright E2E Tests (Frontend)
- **Location**: `frontend/frontend/tests/` (`.spec.js` files)
- **Config**: `frontend/frontend/playwright.config.js`
- **Browsers**: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari

### Pytest (Backend)
- **Location**: `tests/` and `backend/tests/` (Python)
- **Config**: `pytest.ini`
- **Run**: `source venv/bin/activate && pytest`

---

## Critical Patterns

### 1. Serial Execution (Database Concurrency)
Tests run with `workers: 1` to avoid SQLite WAL visibility issues. Never assume parallel execution.

### 2. Database Polling for WAL Visibility
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

### 3. Handle Gated Results Overlay
Always check for and dismiss gated results before asserting on validation results:
```javascript
if (await page.locator('[data-testid="gated-results"]').first().isVisible()) {
  await page.locator('button:has-text("View Results")').first().click();
}
```

### 4. Wait for Page Load
```javascript
async function waitForPageLoad(page) {
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000); // Wait for React to render
}
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
| `/test/health` | GET | - | Health check for test env |

---

## Test Job Indicator
Use `"testtesttest"` in citations to flag test jobs. These are filtered from dashboard metrics.

---

## Anti-Patterns to Avoid

1. **DON'T** assume data is immediately visible after database writes - poll for state
2. **DON'T** use fixed `waitForTimeout` without polling for actual state changes
3. **DON'T** forget to handle gated results overlay in E2E tests
4. **DON'T** run tests in parallel - they share a SQLite database
5. **DON'T** hardcode variant values - use `localStorage.setItem('experiment_v1', 'X')`
6. **DON'T** start backend without `TESTING=true` when running E2E tests

---

## Running Tests

### Playwright E2E
```bash
cd frontend/frontend
npx playwright test                    # All tests
npx playwright test --project=chromium # Single browser
npx playwright test path/to/test.spec.js # Single file
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
