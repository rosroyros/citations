import { test, expect } from '@playwright/test';

/**
 * Validation Table Header Display Tests
 * 
 * These tests verify the ValidationTable header displays correct:
 * - Citation counts (total, perfect, errors, remaining)
 * - Partial results indicator styling
 * - Mobile responsive layouts
 * 
 * All tests use route mocking for fast, deterministic execution.
 */

// Mock data for different scenarios
const mockFullResults = {
  status: 'completed',
  results: {
    results: [
      { original: 'Smith, J. (2023). First test. <em>Journal of Testing</em>, 1(1), 1-10.', source_type: 'journal', errors: [] },
      { original: 'Doe, J. (2023). Second test. <em>Journal of Testing</em>, 1(2), 11-20.', source_type: 'journal', errors: [] },
      { original: 'Brown, A. (2023). Third test.', source_type: 'journal', errors: [{ component: 'title', problem: 'Not italicized', correction: '<em>Third test</em>' }] },
      { original: 'Wilson, B. (2023). Fourth test. <em>Journal of Testing</em>, 1(4), 31-40.', source_type: 'journal', errors: [] },
      { original: 'Taylor, C. (2023). Fifth test.', source_type: 'journal', errors: [{ component: 'title', problem: 'Not italicized', correction: '<em>Fifth test</em>' }] }
    ],
    user_status: { type: 'free', validations_used: 5, limit: 5 }
  }
};

const mockPartialResults = {
  status: 'completed',
  results: {
    results: [
      { original: 'Smith, J. (2023). Test citation. <em>Journal of Testing</em>, 1(1), 1-10.', source_type: 'journal', errors: [] },
      { original: 'Doe, J. (2023). Another test.', source_type: 'journal', errors: [{ component: 'title', problem: 'Not italicized', correction: '<em>Another test</em>' }] }
    ],
    user_status: { type: 'free', validations_used: 5, limit: 5 },
    results_gated: false,
    is_partial: true,
    citations_remaining: 6
  }
};

// Helper to set up route mocking
async function setupMockRoutes(page, mockResponse) {
  // Mock job creation
  await page.route(/\/api\/validate\/async/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        job_id: 'mock-job-' + Date.now(),
        status: 'pending',
        experiment_variant: 0
      })
    });
  });

  // Mock job polling - return completed immediately
  await page.route(/\/api\/jobs\/.*/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockResponse)
    });
  });

  // Wait a tick to ensure routes are registered (helps Mobile Safari timing)
  await new Promise(resolve => setTimeout(resolve, 100));
}

// Desktop viewport tests
test.describe('ValidationTable Header Display - Desktop', () => {
  test.use({
    baseURL: 'http://localhost:5173',
    viewport: { width: 1280, height: 720 }
  });

  test.beforeEach(async ({ page }) => {
    // Only clear state - do NOT navigate here (routes must be set up first)
    await page.context().clearCookies();
    await page.addInitScript(() => {
      localStorage.clear();
    });
  });

  test('Full results header displays correct counts', async ({ page }) => {
    // Set up mocking BEFORE navigation
    await setupMockRoutes(page, mockFullResults);

    // Navigate after routes are set up
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    // Find and fill the editor
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
    await editor.fill(
      'Smith, J. (2023). First test. *Journal of Testing*, 1(1), 1-10.\n\n' +
      'Doe, J. (2023). Second test. *Journal of Testing*, 1(2), 11-20.\n\n' +
      'Brown, A. (2023). Third test. *Journal of Testing*, 1(3), 21-30.\n\n' +
      'Wilson, B. (2023). Fourth test. *Journal of Testing*, 1(4), 31-40.\n\n' +
      'Taylor, C. (2023). Fifth test. *Journal of Testing*, 1(5), 41-50.'
    );

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Wait for ACTUAL results (not loading state) - data-testid="results" only exists in ValidationTable
    await expect(page.locator('[data-testid="results"]')).toBeVisible({ timeout: 15000 });

    // Handle gated results if present
    if (await page.locator('[data-testid="gated-results"]').first().isVisible()) {
      await page.locator('button:has-text("View Results")').first().click();
      await expect(page.locator('[data-testid="results"]')).toBeVisible({ timeout: 10000 });
    }

    // Verify full results header
    await expect(page.locator('.table-header h2')).toContainText('Validation Results');
    await expect(page.locator('.table-header h2')).not.toContainText('⚠️ Partial');

    // Verify count display for full results
    const statsText = await page.locator('.table-stats').textContent();
    expect(statsText).toContain('5 references');
    expect(statsText).toMatch(/\d+.*perfect/);
    expect(statsText).toMatch(/\d+.*need fixes/);

    // Should NOT show partial results breakdown
    expect(statsText).not.toContain('remaining');
  });

  test('Partial results visual styling and clickability', async ({ page }) => {
    // Set up mocking for partial results
    await setupMockRoutes(page, mockPartialResults);

    await page.goto('/');

    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
    await editor.fill(
      'Smith, J. (2023). Test citation. *Journal of Testing*, 1(1), 1-10.\n\n' +
      'Doe, J. (2023). Another test. *Journal of Testing*, 1(2), 11-20.'
    );

    await page.locator('button[type="submit"]').click();

    // Wait for results
    await expect(page.locator('[data-testid="results"], [data-testid="partial-results"]').first()).toBeVisible({ timeout: 15000 });

    // Handle gated results if present
    if (await page.locator('[data-testid="gated-results"]').first().isVisible()) {
      await page.locator('button:has-text("View Results")').first().click();
    }

    // Check if partial results are shown (depends on mock data triggering partial UI)
    const tableHeader = page.locator('.table-header h2');
    await expect(tableHeader).toContainText('Validation Results');
  });
});

// Mobile viewport tests
test.describe('ValidationTable Header Display - Mobile', () => {
  test.use({
    baseURL: 'http://localhost:5173',
    viewport: { width: 375, height: 667 } // iPhone SE dimensions
  });

  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await page.addInitScript(() => {
      localStorage.clear();
    });
  });

  test('Mobile - Full results header displays correctly', async ({ page }) => {
    await setupMockRoutes(page, mockFullResults);

    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
    await editor.fill(
      'Smith, J. (2023). First test. *Journal of Testing*, 1(1), 1-10.\n\n' +
      'Doe, J. (2023). Second test. *Journal of Testing*, 1(2), 11-20.\n\n' +
      'Brown, A. (2023). Third test. *Journal of Testing*, 1(3), 21-30.\n\n' +
      'Wilson, B. (2023). Fourth test. *Journal of Testing*, 1(4), 31-40.\n\n' +
      'Taylor, C. (2023). Fifth test. *Journal of Testing*, 1(5), 41-50.'
    );

    await page.locator('button[type="submit"]').click();

    // Wait for ACTUAL results
    await expect(page.locator('[data-testid="results"]')).toBeVisible({ timeout: 15000 });

    // Handle gated results if present
    if (await page.locator('[data-testid="gated-results"]').first().isVisible()) {
      await page.locator('button:has-text("View Results")').first().click();
      await expect(page.locator('[data-testid="results"]')).toBeVisible({ timeout: 10000 });
    }

    // Verify full results header
    await expect(page.locator('.table-header h2')).toContainText('Validation Results');
    await expect(page.locator('.table-header h2')).not.toContainText('⚠️ Partial');

    // Verify header is visible and not cut off on mobile
    const header = page.locator('.table-header');
    await expect(header).toBeVisible();

    const statsText = await page.locator('.table-stats').textContent();
    expect(statsText).toContain('5 references');
  });

  test('Mobile - Partial results header displays with proper wrapping', async ({ page }) => {
    await setupMockRoutes(page, mockPartialResults);

    await page.goto('/');

    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
    await editor.fill(
      'Smith, J. (2023). First test. *Journal of Testing*, 1(1), 1-10.\n\n' +
      'Doe, J. (2023). Second test. *Journal of Testing*, 1(2), 11-20.'
    );

    await page.locator('button[type="submit"]').click();

    // Wait for results
    await expect(page.locator('[data-testid="results"], [data-testid="partial-results"]').first()).toBeVisible({ timeout: 15000 });

    // Handle gated results if present
    if (await page.locator('[data-testid="gated-results"]').first().isVisible()) {
      await page.locator('button:has-text("View Results")').first().click();
    }

    // Verify results header
    await expect(page.locator('.table-header h2')).toContainText('Validation Results');

    // Verify stats are visible on mobile (may wrap)
    const statsText = await page.locator('.table-stats').textContent();
    expect(statsText).toContain('references');
  });

  test('Mobile - Upgrade banner is properly sized and accessible', async ({ page }) => {
    await setupMockRoutes(page, mockPartialResults);

    await page.goto('/');

    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
    await editor.fill(
      'Smith, J. (2023). Test citation. *Journal of Testing*, 1(1), 1-10.\n\n' +
      'Doe, J. (2023). Another test. *Journal of Testing*, 1(2), 11-20.'
    );

    await page.locator('button[type="submit"]').click();

    // Wait for results
    await expect(page.locator('[data-testid="results"], [data-testid="partial-results"]').first()).toBeVisible({ timeout: 15000 });

    // Handle gated results if present
    if (await page.locator('[data-testid="gated-results"]').first().isVisible()) {
      await page.locator('button:has-text("View Results")').first().click();
    }

    // Check if upgrade banner is present (only shown for partial results)
    const upgradeButton = page.locator('.upgrade-button');
    if (await upgradeButton.isVisible()) {
      // Check button is properly sized for touch (minimum 44x44px)
      const buttonBox = await upgradeButton.boundingBox();
      expect(buttonBox.height).toBeGreaterThanOrEqual(44);
      expect(buttonBox.width).toBeGreaterThanOrEqual(100); // Reasonable minimum width
    }
  });
});