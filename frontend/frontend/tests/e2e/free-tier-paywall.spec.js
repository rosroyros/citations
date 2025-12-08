import { test, expect } from '@playwright/test';

// Constants
const TIMEOUT = 30000;

// Test data
const citations = {
  valid1: 'Smith, J. (2023). Understanding machine learning. Journal of AI, 15(2), 123-145.',
  valid2: 'Johnson, M. (2023). Data science fundamentals. Tech Review, 8(4), 67-89.',
  valid3: 'Williams, R. (2023). Cloud computing trends. Computing Weekly, 12(1), 23-34.',
  valid4: 'Brown, A. (2023). Software engineering practices. Developer Digest, 20(3), 156-178.',
  valid5: 'Davis, K. (2023). Web development basics. Code Magazine, 5(2), 89-102.',
  valid6: 'Miller, T. (2023). Database design patterns. Data Today, 14(1), 45-67.',
  valid7: 'Wilson, S. (2023). Network security essentials. Security Focus, 9(4), 201-223.',
  valid8: 'Moore, L. (2023). Mobile app development. App Developer Journal, 7(3), 134-156.',
  valid9: 'Taylor, J. (2023). DevOps best practices. Ops Weekly, 11(2), 78-92.',
  valid10: 'Anderson, P. (2023). UX design principles. Design Today, 6(1), 34-56.'
};

// Generate additional citations for the 100 citation test
for (let i = 11; i <= 100; i++) {
  citations[`valid${i}`] = `Author${i}, A. (2023). Research article ${i}. Academic Journal, 1(1), 1-20.`;
}

test.describe('Free Tier Paywall', () => {
  test.use({ baseURL: 'http://localhost:5173' });

  test.beforeEach(async ({ page }) => {
    // Clear local storage before each test to start fresh
    await page.context().clearCookies();
    // Add script to clear localStorage before page loads
    await page.addInitScript(() => {
      localStorage.clear();
    });
    await page.goto('/');
  });

  test('first-time user submits 5 citations', async ({ page }) => {
    // Already navigated to baseURL in beforeEach

    // Wait for app to load
    await expect(page.locator('body')).toBeVisible();

    // Find the editor textarea
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();

    // Submit 5 citations
    const citationText = Object.values(citations).slice(0, 5).join('\n');
    await editor.fill(citationText);

    // Find and click submit button
    const submitButton = page.locator('button').filter({ hasText: /check|validate|submit/i }).first();
    await expect(submitButton).toBeVisible();
    await submitButton.click();

    // Should succeed without paywall (under free tier limit)
    await expect(page.locator('[data-testid="results"]')).toBeVisible({ timeout: TIMEOUT });

    // Verify no upgrade modal is shown
    await expect(page.locator('[data-testid="upgrade-modal"]')).not.toBeVisible();

    // Verify free usage was incremented
    const freeUsage = await page.evaluate(() => parseInt(localStorage.getItem('citation_checker_free_used') || '0', 10));
    expect(freeUsage).toBe(5);
  });

  test('user with 5 used submits 8 citations', async ({ page }) => {
    // Already navigated to baseURL in beforeEach

    // Set up initial state: user has already used 5 citations
    await page.evaluate(() => {
      localStorage.setItem('citation_checker_free_used', '5');
    });

    // Find the editor
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();

    // Submit 8 citations (5 + 8 = 13, which exceeds free tier limit)
    const citationText = Object.values(citations).slice(5, 13).join('\n');
    await editor.fill(citationText);

    // Find and click submit button
    const submitButton = page.locator('button').filter({ hasText: /check|validate|submit/i }).first();
    await expect(submitButton).toBeVisible();
    await submitButton.click();

    // Should show partial results (up to free tier limit)
    await expect(page.locator('[data-testid="partial-results"]')).toBeVisible({ timeout: TIMEOUT });

    // Verify free usage was updated to 10 (5 + 5 allowed)
    const freeUsage = await page.evaluate(() => parseInt(localStorage.getItem('citation_checker_free_used') || '0', 10));
    expect(freeUsage).toBe(10);

    // Modal should NOT auto-show - user must click "Upgrade Now" button
    await expect(page.locator('[data-testid="upgrade-modal"]')).not.toBeVisible();

    // Click "Upgrade Now" button in partial results
    const upgradeButton = page.locator('.upgrade-button').filter({ hasText: /upgrade/i });
    await upgradeButton.click();

    // NOW modal should appear
    await expect(page.locator('[data-testid="upgrade-modal"]')).toBeVisible();
  });

  test('user at limit tries to submit', async ({ page }) => {
    // Already navigated to baseURL in beforeEach

    // Set up initial state: user has already used 5 citations (at free tier limit)
    await page.evaluate(() => {
      localStorage.setItem('citation_checker_free_used', '5');
    });

    // Find the editor
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();

    // Try to submit 1 more citation
    const citationText = citations.valid11;
    await editor.fill(citationText);

    // Find and click submit button
    const submitButton = page.locator('button').filter({ hasText: /check|validate|submit/i }).first();
    await expect(submitButton).toBeVisible();
    await submitButton.click();

    // Should show partial results with 0 results and locked teaser
    await expect(page.locator('[data-testid="partial-results"]')).toBeVisible({ timeout: TIMEOUT });

    // Verify banner shows "1 more citation available"
    await expect(page.locator('.upgrade-banner')).toContainText('1 more citation');

    // Modal should NOT auto-show - requires button click
    await expect(page.locator('[data-testid="upgrade-modal"]')).not.toBeVisible();

    // Click upgrade button to show modal
    const upgradeButton = page.locator('.upgrade-button').filter({ hasText: /upgrade/i });
    await upgradeButton.click();

    // NOW modal appears
    await expect(page.locator('[data-testid="upgrade-modal"]')).toBeVisible();
  });

  test('user submits 100 citations (first time)', async ({ page }) => {
    // Already navigated to baseURL in beforeEach

    // Find the editor
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();

    // Submit 100 citations (far exceeds free tier limit)
    const citationText = Object.values(citations).slice(0, 100).join('\n');
    await editor.fill(citationText);

    // Find and click submit button
    const submitButton = page.locator('button').filter({ hasText: /check|validate|submit/i }).first();
    await expect(submitButton).toBeVisible();
    await submitButton.click();

    // Should show partial results (up to free tier limit)
    await expect(page.locator('[data-testid="partial-results"]')).toBeVisible({ timeout: TIMEOUT });

    // Verify free usage was capped at tier limit
    const freeUsage = await page.evaluate(() => parseInt(localStorage.getItem('citation_checker_free_used') || '0', 10));
    expect(freeUsage).toBe(10); // Exactly at limit

    // Verify banner shows "90 more citations available"
    await expect(page.locator('.upgrade-banner')).toContainText('90 more citation');

    // Modal should NOT auto-show
    await expect(page.locator('[data-testid="upgrade-modal"]')).not.toBeVisible();
  });

  test('backend sync overrides frontend', async ({ page }) => {
    // Already navigated to baseURL in beforeEach

    // Set up conflicting state: frontend shows 5 used, but backend will report different
    await page.evaluate(() => {
      localStorage.setItem('citation_checker_free_used', '5');
    });

    // Mock API response to simulate backend having different count
    await page.route('**/api/credits*', (route) => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          credits: null,
          free_used: 8 // Backend reports 8 used
        })
      });
    });

    // Reload page to trigger credit sync
    await page.goto('/');

    // Find the editor
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();

    // Submit 3 citations (8 + 3 = 11, which exceeds free tier limit by 1)
    const citationText = Object.values(citations).slice(0, 3).join('\n');
    await editor.fill(citationText);

    // Find and click submit button
    const submitButton = page.locator('button').filter({ hasText: /check|validate|submit/i }).first();
    await expect(submitButton).toBeVisible();
    await submitButton.click();

    // Should show partial results (2 citations processed, 1 locked)
    await expect(page.locator('[data-testid="partial-results"]')).toBeVisible({ timeout: TIMEOUT });

    // Verify frontend was updated to 10 (backend synced, then 2 more checked)
    const freeUsage = await page.evaluate(() => parseInt(localStorage.getItem('citation_checker_free_used') || '0', 10));
    expect(freeUsage).toBe(10); // 8 from backend + 2 allowed = 10 at limit
  });
});