import { test, expect } from '@playwright/test';

test.describe('Inline Pricing A/B Test', () => {
  test.beforeEach(async ({ page }) => {
    // Set experiment variant to 1.2 (Credits + Inline)
    await page.goto('http://localhost:5173');
    await page.evaluate(() => {
      localStorage.setItem('experimentVariant', '1.2');
    });
    await page.reload();
    await page.waitForLoadState('networkidle');
  });

  test('should show inline pricing for variant 1.2', async ({ page }) => {
    // Fill in more than 5 citations to trigger paywall
    await page.fill('.ProseMirror', `Smith, J. (2023). The first citation. Journal of Testing, 45(2), 123-145.
Johnson, M. (2024). Another test citation. Academic Review, 78(3), 456-489.
Williams, R. (2023). Third citation example. Research Papers, 12(4), 789-801.
Brown, A. (2024). Fourth test reference. Scientific Journal, 56(1), 234-250.
Davis, L. (2023). Fifth citation for testing. Education Today, 34(2), 567-580.
Miller, K. (2024). Sixth citation to trigger paywall. Medical Research, 89(3), 901-915.`);

    // Click validate button
    await page.click('button:has-text("Check My Citations")');

    // Wait for partial results
    await page.waitForSelector('[data-testid="partial-results"]', { timeout: 30000 });

    // Check that inline pricing container is visible
    await expect(page.locator('.inline-pricing-container')).toBeVisible();

    // Check that upgrade button is NOT visible (inline variant)
    await expect(page.locator('.upgrade-button')).not.toBeVisible();

    // Check that pricing table is visible
    await expect(page.locator('[data-testid="pricing-card"]')).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'test-results/inline-pricing-variant-1.2.png' });
  });

  test('should show button for variant 1.1', async ({ page }) => {
    // Set to button variant
    await page.evaluate(() => {
      localStorage.setItem('experimentVariant', '1.1');
    });
    await page.reload();
    await page.waitForLoadState('networkidle');

    // Fill in citations
    await page.fill('.ProseMirror', `Smith, J. (2023). The first citation. Journal of Testing, 45(2), 123-145.
Johnson, M. (2024). Another test citation. Academic Review, 78(3), 456-489.
Williams, R. (2023). Third citation example. Research Papers, 12(4), 789-801.
Brown, A. (2024). Fourth test reference. Scientific Journal, 56(1), 234-250.
Davis, L. (2023). Fifth citation for testing. Education Today, 34(2), 567-580.
Miller, K. (2024). Sixth citation to trigger paywall. Medical Research, 89(3), 901-915.`);

    // Click validate button
    await page.click('button:has-text("Check My Citations")');

    // Wait for partial results
    await page.waitForSelector('[data-testid="partial-results"]', { timeout: 30000 });

    // Check that upgrade button IS visible (button variant)
    await expect(page.locator('.upgrade-button')).toBeVisible();

    // Check that inline pricing container is NOT visible
    await expect(page.locator('.inline-pricing-container')).not.toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'test-results/button-pricing-variant-1.1.png' });
  });

  test('should track pricing_viewed analytics event', async ({ page }) => {
    // Listen for network requests
    const pricingViewedPromise = page.waitForRequest(request =>
      request.url().includes('/api/track-event') &&
      request.postDataJSON().event === 'pricing_viewed'
    );

    // Fill in citations and submit
    await page.fill('.ProseMirror', `Smith, J. (2023). Test citation. Journal of Testing, 45(2), 123-145.`);
    await page.click('button:has-text("Check My Citations")');
    await page.waitForSelector('[data-testid="partial-results"]', { timeout: 30000 });

    // Wait for pricing_viewed event
    const request = await pricingViewedPromise;
    const postData = request.postDataJSON();

    expect(postData.event).toBe('pricing_viewed');
    expect(postData.properties.interaction_type).toBe('auto');
    expect(postData.properties.variant).toBe('1.2');
  });

  test('should be mobile responsive', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 812 });

    // Fill in citations
    await page.fill('.ProseMirror', `Smith, J. (2023). Test citation. Journal of Testing, 45(2), 123-145.`);
    await page.click('button:has-text("Check My Citations")');
    await page.waitForSelector('[data-testid="partial-results"]', { timeout: 30000 });

    // Check inline pricing container fits on mobile
    const containerBox = await page.locator('.inline-pricing-container').boundingBox();
    expect(containerBox.width).toBeLessThanOrEqual(375);

    // Take screenshot
    await page.screenshot({ path: 'test-results/inline-pricing-mobile.png', fullPage: true });
  });
});