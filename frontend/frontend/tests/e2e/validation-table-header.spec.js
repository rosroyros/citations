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
    console.log('🧪 Testing full results header display');

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

    console.log('✅ Full results header displays correctly');

    // Visual regression check - desktop layout
    await expect(page.locator('.validation-table-container')).toHaveScreenshot('desktop-full-results-header.png', {
      maxDiffPixels: 100
    });
  });

  test('Partial results header displays accurate counts and breakdown', async ({ page }) => {
    console.log('🧪 Testing partial results header display');

    // Simulate user with existing usage to trigger partial results
    await page.addInitScript(() => {
      localStorage.setItem('citation_checker_free_used', '5');
    });
    await page.goto('/');

    // Submit 8 citations (5 used + 8 new = 13 total, should get 10 processed, 3 remaining)
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

    // Verify partial results breakdown
    const statsText = await page.locator('.table-stats').textContent();
    expect(statsText).toContain('8 submitted'); // 8 new submissions
    expect(statsText).toContain('(5 processed • 3 remaining)'); // Free tier limit applied
    expect(statsText).toMatch(/\d+perfect/);
    expect(statsText).toMatch(/\d+need fixes/);

    console.log('✅ Partial results header displays correctly');

    // Visual regression check - desktop partial results layout
    await expect(page.locator('.partial-results-container')).toHaveScreenshot('desktop-partial-results-header.png', {
      maxDiffPixels: 100
    });
  });

  test('Partial results visual styling is applied', async ({ page }) => {
    console.log('🧪 Testing partial results visual styling');

    // Simulate user at free tier limit
    await page.addInitScript(() => {
      localStorage.setItem('citation_checker_free_used', '10');
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

    const partialInfo = page.locator('.partial-info');
    await expect(partialInfo).toBeVisible();

    const partialBreakdown = page.locator('.partial-breakdown');
    await expect(partialBreakdown).toBeVisible();
    await expect(partialBreakdown).toContainText('processed');
    await expect(partialBreakdown).toContainText('remaining');

    console.log('✅ Partial results visual styling applied correctly');

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
    console.log('📱 Testing mobile full results header display');

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

    console.log('✅ Mobile full results header displays correctly');

    // Visual regression check - mobile layout
    await expect(page.locator('.validation-table-container')).toHaveScreenshot('mobile-full-results-header.png', {
      maxDiffPixels: 100
    });
  });

  test('Mobile - Partial results header displays with proper wrapping', async ({ page }) => {
    console.log('📱 Testing mobile partial results header display');

    // Simulate user with existing usage to trigger partial results
    await page.addInitScript(() => {
      localStorage.setItem('citation_checker_free_used', '5');
    });
    await page.goto('/');

    // Submit 8 citations (5 used + 8 new = 13 total, should get 10 processed, 3 remaining)
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
    const partialInfo = page.locator('.partial-info');
    await expect(partialInfo).toBeVisible();

    const partialBreakdown = page.locator('.partial-breakdown');
    await expect(partialBreakdown).toBeVisible();

    console.log('✅ Mobile partial results header displays correctly');

    // Visual regression check - mobile partial results layout
    await expect(page.locator('.partial-results-container')).toHaveScreenshot('mobile-partial-results-header.png', {
      maxDiffPixels: 100
    });
  });

  test('Mobile - Upgrade banner is properly sized and accessible', async ({ page }) => {
    console.log('📱 Testing mobile upgrade banner layout');

    // Simulate user at free tier limit
    await page.addInitScript(() => {
      localStorage.setItem('citation_checker_free_used', '10');
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

    console.log('✅ Mobile upgrade banner properly sized');

    // Visual regression check - mobile upgrade banner
    await expect(page.locator('.upgrade-banner')).toHaveScreenshot('mobile-upgrade-banner.png', {
      maxDiffPixels: 100
    });
  });
});