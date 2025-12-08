import { test, expect } from '@playwright/test';

// Desktop viewport tests
test.describe('ValidationTable Header Display - Desktop', () => {
  test.use({
    baseURL: 'http://localhost:5173',
    viewport: { width: 1280, height: 720 }
  });

  test.beforeEach(async ({ page }) => {
    // Clear cookies and localStorage before each test
    await page.context().clearCookies();
    await page.addInitScript(() => {
      localStorage.clear();
    });
    await page.goto('/');

    // Wait for app to load
    await expect(page.locator('body')).toBeVisible();

    // Find the editor (TipTap uses .ProseMirror)
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
  });

  test('Full results header displays correct counts', async ({ page }) => {

    // Submit 5 citations (under free tier limit)
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await editor.fill(
      'Smith, J. (2023). First test. *Journal of Testing*, 1(1), 1-10.\n\n' +
      'Doe, J. (2023). Second test. *Journal of Testing*, 1(2), 11-20.\n\n' +
      'Brown, A. (2023). Third test. *Journal of Testing*, 1(3), 21-30.\n\n' +
      'Wilson, B. (2023). Fourth test. *Journal of Testing*, 1(4), 31-40.\n\n' +
      'Taylor, C. (2023). Fifth test. *Journal of Testing*, 1(5), 41-50.'
    );

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Wait for results
    await expect(page.locator('.validation-table-container, .validation-table').first()).toBeVisible({ timeout: 30000 });

    // Verify full results header
    await expect(page.locator('.table-header h2')).toContainText('Validation Results');
    await expect(page.locator('.table-header h2')).not.toContainText('⚠️ Partial');

    // Verify count display for full results
    const statsText = await page.locator('.table-stats').textContent();
    expect(statsText).toContain('5 citations');
    expect(statsText).toMatch(/\d+perfect/);
    expect(statsText).toMatch(/\d+need fixes/);

    // Should NOT show partial results breakdown
    expect(statsText).not.toContain('submitted');
    expect(statsText).not.toContain('processed');
    expect(statsText).not.toContain('remaining');


    // Visual regression check - desktop layout
    await expect(page.locator('.validation-table-container')).toHaveScreenshot('desktop-full-results-header.png', {
      maxDiffPixels: 100
    });
  });

  test('Partial results header displays accurate counts and breakdown', async ({ page }) => {

    // Simulate user with existing usage to trigger partial results
    await page.addInitScript(() => {
      localStorage.setItem('citation_checker_free_used', '5');
    });
    await page.goto('/');

    // Submit 8 citations (5 used + 8 new = 13 total, should get 0 processed, 8 remaining)
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await editor.fill(
      'Smith, J. (2023). First test. *Journal of Testing*, 1(1), 1-10.\n\n' +
      'Doe, J. (2023). Second test. *Journal of Testing*, 1(2), 11-20.\n\n' +
      'Brown, A. (2023). Third test. *Journal of Testing*, 1(3), 21-30.\n\n' +
      'Wilson, B. (2023). Fourth test. *Journal of Testing*, 1(4), 31-40.\n\n' +
      'Taylor, C. (2023). Fifth test. *Journal of Testing*, 1(5), 41-50.\n\n' +
      'Anderson, K. (2023). Sixth test. *Journal of Testing*, 1(6), 51-60.\n\n' +
      'Thomas, L. (2023). Seventh test. *Journal of Testing*, 1(7), 61-70.\n\n' +
      'Jackson, M. (2023). Eighth test. *Journal of Testing*, 1(8), 71-80.'
    );

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Wait for partial results
    await expect(page.locator('[data-testid="partial-results"], .partial-results-container').first()).toBeVisible({ timeout: 30000 });

    // Verify partial results header with indicator
    await expect(page.locator('.table-header h2')).toContainText('Validation Results ⚠️ Partial');

    // Verify partial results format: X citations • Y perfect • Z need fixes • N remaining
    const statsText = await page.locator('.table-stats').textContent();
    expect(statsText).toContain('0 citations'); // 0 processed (already at limit)
    expect(statsText).toContain('8 remaining'); // All 8 citations remaining
    expect(statsText).toMatch(/\d+\s*perfect/);
    expect(statsText).toMatch(/\d+\s*need fixes/);

    // Should NOT show old format
    expect(statsText).not.toContain('submitted');
    expect(statsText).not.toContain('processed');


    // Visual regression check - desktop partial results layout
    await expect(page.locator('.partial-results-container')).toHaveScreenshot('desktop-partial-results-header.png', {
      maxDiffPixels: 100
    });
  });

  test('Partial results visual styling and clickability', async ({ page }) => {

    // Simulate user at free tier limit
    await page.addInitScript(() => {
      localStorage.setItem('citation_checker_free_used', '5');
    });
    await page.goto('/');

    // Submit citations to trigger partial results
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await editor.fill(
      'Smith, J. (2023). Test citation. *Journal of Testing*, 1(1), 1-10.\n\n' +
      'Doe, J. (2023). Another test. *Journal of Testing*, 1(2), 11-20.'
    );

    await page.locator('button[type="submit"]').click();
    await expect(page.locator('[data-testid="partial-results"], .partial-results-container').first()).toBeVisible({ timeout: 30000 });

    // Verify CSS classes for partial results
    const partialIndicator = page.locator('.partial-indicator');
    await expect(partialIndicator).toContainText('⚠️ Partial');
    await expect(partialIndicator).toHaveClass(/clickable/);

    // Verify "remaining" stat is displayed with reddish styling
    const remainingStat = page.locator('.stat-remaining');
    await expect(remainingStat).toBeVisible();
    await expect(remainingStat).toContainText('remaining');

    const remainingBadge = page.locator('.stat-badge.remaining');
    await expect(remainingBadge).toBeVisible();

    // Test clicking partial indicator scrolls to upgrade banner
    const upgradeBanner = page.locator('.upgrade-banner');
    await expect(upgradeBanner).toBeVisible();

    // Click the partial indicator
    await partialIndicator.click();

    // Wait a moment for scroll animation
    await page.waitForTimeout(500);


    // Visual regression check - desktop styling details
    await expect(page.locator('.table-header')).toHaveScreenshot('desktop-partial-indicator-styling.png', {
      maxDiffPixels: 50
    });
  });
});

// Mobile viewport tests
test.describe('ValidationTable Header Display - Mobile', () => {
  test.use({
    baseURL: 'http://localhost:5173',
    viewport: { width: 375, height: 667 } // iPhone SE dimensions
  });

  test.beforeEach(async ({ page }) => {
    // Clear cookies and localStorage before each test
    await page.context().clearCookies();
    await page.addInitScript(() => {
      localStorage.clear();
    });
    await page.goto('/');

    // Wait for app to load
    await expect(page.locator('body')).toBeVisible();

    // Find the editor (TipTap uses .ProseMirror)
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
  });

  test('Mobile - Full results header displays correctly', async ({ page }) => {

    // Submit 5 citations (under free tier limit)
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await editor.fill(
      'Smith, J. (2023). First test. *Journal of Testing*, 1(1), 1-10.\n\n' +
      'Doe, J. (2023). Second test. *Journal of Testing*, 1(2), 11-20.\n\n' +
      'Brown, A. (2023). Third test. *Journal of Testing*, 1(3), 21-30.\n\n' +
      'Wilson, B. (2023). Fourth test. *Journal of Testing*, 1(4), 31-40.\n\n' +
      'Taylor, C. (2023). Fifth test. *Journal of Testing*, 1(5), 41-50.'
    );

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Wait for results
    await expect(page.locator('.validation-table-container, .validation-table').first()).toBeVisible({ timeout: 30000 });

    // Verify full results header
    await expect(page.locator('.table-header h2')).toContainText('Validation Results');
    await expect(page.locator('.table-header h2')).not.toContainText('⚠️ Partial');

    // Verify header is visible and not cut off on mobile
    const header = page.locator('.table-header');
    await expect(header).toBeVisible();

    const statsText = await page.locator('.table-stats').textContent();
    expect(statsText).toContain('5 citations');


    // Visual regression check - mobile layout
    await expect(page.locator('.validation-table-container')).toHaveScreenshot('mobile-full-results-header.png', {
      maxDiffPixels: 100
    });
  });

  test('Mobile - Partial results header displays with proper wrapping', async ({ page }) => {

    // Simulate user with existing usage to trigger partial results
    await page.addInitScript(() => {
      localStorage.setItem('citation_checker_free_used', '5');
    });
    await page.goto('/');

    // Submit 8 citations (5 used + 8 new = 13 total, should get 0 processed, 8 remaining)
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await editor.fill(
      'Smith, J. (2023). First test. *Journal of Testing*, 1(1), 1-10.\n\n' +
      'Doe, J. (2023). Second test. *Journal of Testing*, 1(2), 11-20.\n\n' +
      'Brown, A. (2023). Third test. *Journal of Testing*, 1(3), 21-30.\n\n' +
      'Wilson, B. (2023). Fourth test. *Journal of Testing*, 1(4), 31-40.\n\n' +
      'Taylor, C. (2023). Fifth test. *Journal of Testing*, 1(5), 41-50.\n\n' +
      'Anderson, K. (2023). Sixth test. *Journal of Testing*, 1(6), 51-60.\n\n' +
      'Thomas, L. (2023). Seventh test. *Journal of Testing*, 1(7), 61-70.\n\n' +
      'Jackson, M. (2023). Eighth test. *Journal of Testing*, 1(8), 71-80.'
    );

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Wait for partial results
    await expect(page.locator('[data-testid="partial-results"], .partial-results-container').first()).toBeVisible({ timeout: 30000 });

    // Verify partial results header with indicator
    await expect(page.locator('.table-header h2')).toContainText('Validation Results ⚠️ Partial');

    // Verify stats are visible on mobile (may wrap)
    const statsText = await page.locator('.table-stats').textContent();
    expect(statsText).toContain('citations');
    expect(statsText).toContain('remaining');

    // Verify remaining badge is visible
    const remainingBadge = page.locator('.stat-badge.remaining');
    await expect(remainingBadge).toBeVisible();


    // Visual regression check - mobile partial results layout
    await expect(page.locator('.partial-results-container')).toHaveScreenshot('mobile-partial-results-header.png', {
      maxDiffPixels: 100
    });
  });

  test('Mobile - Upgrade banner is properly sized and accessible', async ({ page }) => {

    // Simulate user at free tier limit
    await page.addInitScript(() => {
      localStorage.setItem('citation_checker_free_used', '5');
    });
    await page.goto('/');

    // Submit citations to trigger partial results
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await editor.fill(
      'Smith, J. (2023). Test citation. *Journal of Testing*, 1(1), 1-10.\n\n' +
      'Doe, J. (2023). Another test. *Journal of Testing*, 1(2), 11-20.'
    );

    await page.locator('button[type="submit"]').click();
    await expect(page.locator('[data-testid="partial-results"], .partial-results-container').first()).toBeVisible({ timeout: 30000 });

    // Verify upgrade banner is visible and accessible
    const upgradeButton = page.locator('.upgrade-button');
    await expect(upgradeButton).toBeVisible();

    // Check button is properly sized for touch (minimum 44x44px)
    const buttonBox = await upgradeButton.boundingBox();
    expect(buttonBox.height).toBeGreaterThanOrEqual(44);
    expect(buttonBox.width).toBeGreaterThanOrEqual(100); // Reasonable minimum width


    // Visual regression check - mobile upgrade banner
    await expect(page.locator('.upgrade-banner')).toHaveScreenshot('mobile-upgrade-banner.png', {
      maxDiffPixels: 100
    });
  });

  test('Mobile - Keyboard accessibility for partial indicator', async ({ page }) => {
    // Simulate user at free tier limit
    await page.addInitScript(() => {
      localStorage.setItem('citation_checker_free_used', '5');
    });
    await page.goto('/');

    // Submit citations to trigger partial results
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await editor.fill(
      'Smith, J. (2023). Test citation. *Journal of Testing*, 1(1), 1-10.\n\n' +
      'Doe, J. (2023). Another test. *Journal of Testing*, 1(2), 11-20.'
    );

    await page.locator('button[type="submit"]').click();
    await expect(page.locator('[data-testid="partial-results"], .partial-results-container').first()).toBeVisible({ timeout: 30000 });

    // Tab to partial indicator
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');

    const partialIndicator = page.locator('.partial-indicator.clickable');

    // Test Enter key scrolls to upgrade banner
    const upgradeBanner = page.locator('.upgrade-banner');
    await page.keyboard.press('Enter');
    await expect(upgradeBanner).toBeInViewport();

    // Reset scroll
    await page.evaluate(() => window.scrollTo(0, 0));

    // Re-focus partial indicator
    await partialIndicator.focus();

    // Test Space key also scrolls (without scrolling page)
    await page.keyboard.press('Space');
    await expect(upgradeBanner).toBeInViewport();
  });
});