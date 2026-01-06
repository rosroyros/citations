# Full Integration Test Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a full E2E integration test that verifies the complete system flow using real files, real backend API, and real LLM (Gemini/OpenAI) responses.

**Architecture:**
- Create `frontend/frontend/tests/e2e/e2e-full-flow.spec.cjs` (referenced in `playwright.config.js`)
- Test will upload a real `.docx` file from fixtures
- Test will wait for the async job to complete (polling)
- Test will verify the results match expected citation analysis
- **CRITICAL:** This test will run against the LOCAL backend but that backend must be configured to talk to real LLM APIs (via `.env`).

**Tech Stack:** Playwright, Node.js (test runner), Python/FastAPI (backend target)

---

### Task 1: Create Test Fixtures

**Files:**
- Check: `frontend/frontend/fixtures/real_test_doc.docx` (Create if missing)
- Content: A simple DOCX with 1-2 known citations (e.g., APA 7 style).

**Step 1: Verify/Create Fixture**
- Check if `frontend/frontend/fixtures` exists.
- Create a simple `.docx` file if one doesn't exist for this purpose.
- **Note:** We might need to copy an existing fixture or create a new one.

### Task 2: Implement Full Flow Test

**Files:**
- Create: `frontend/frontend/tests/e2e/e2e-full-flow.spec.cjs`

**Step 1: Write the test skeleton**

```javascript
// frontend/frontend/tests/e2e/e2e-full-flow.spec.cjs
const { test, expect } = require('@playwright/test');
const path = require('path');

test.describe('Full Integration Flow (Real LLM)', () => {
  // Increase timeout for real LLM processing (can take 30s+)
  test.setTimeout(120000);

  test('uploads real DOCX and validates citations via backend', async ({ page }) => {
    // 1. Go to home page
    await page.goto('/');

    // 2. Upload File
    const fileInput = page.locator('input[type="file"]');
    // Use a fixture path - update to match actual location
    const testDocPath = path.join(__dirname, '../../fixtures/test_doc_valid.docx');
    await fileInput.setInputFiles(testDocPath);

    // 3. Wait for "Validating..." state
    await expect(page.locator('.validation-loading-container')).toBeVisible({ timeout: 10000 });

    // 4. Wait for Results (High timeout for LLM)
    // The .validation-results-section appears when job is done
    await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 60000 });

    // 5. Verify Content
    // We expect the table to populate.
    // Since LLM output can vary slightly, we check for structural success (not exact text match of reasoning)
    const resultRows = page.locator('tbody tr.result-row');
    await expect(resultRows).toHaveCount(1); // Assuming 1 citation in fixture

    // Verify status icon presence (Check or Cross)
    await expect(page.locator('.status-icon')).toBeVisible();
  });
});
```

**Step 2: Run test (Expect failure if backend not running/configured)**
- Command: `npx playwright test tests/e2e/e2e-full-flow.spec.cjs --project=production`
- **Note:** This requires the backend to be running with valid API keys.

### Task 3: Verify with Local Backend

**Step 1: Ensure Backend is running**
- Check if `uvicorn` process is running.
- Ensure `.env` has `OPENAI_API_KEY` or `GEMINI_API_KEY`.

**Step 2: Run the test**
- Execute the Playwright command.
- Verify it passes.

### Task 4: Integration with CI/Deploy Script

**Files:**
- Modify: `deploy_prod.sh` (if needed, to include this test run if desired, or keep it separate)
- **Note:** The user asked for the test creation. Integration into CI pipeline might be a separate concern, but ensuring it runs is key.

**Step 1: Check `package.json`**
- Add a script `test:e2e:full` that runs this specific project.

```json
"scripts": {
  "test:e2e:full": "playwright test --project=production"
}
```

---
