const { test, expect } = require('@playwright/test');

test.describe('Gated Results Overlay', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5174');
  });

  test('should show gated overlay when validation completes', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Look for gated results overlay
    const overlay = page.locator('[data-testid="gated-results"]');
    await expect(overlay).toBeVisible();

    // Check that overlay covers the entire validation table
    const overlayBox = await overlay.boundingBox();
    const container = page.locator('.validation-table-container').first();
    const containerBox = await container.boundingBox();

    expect(overlayBox.x).toBeLessThanOrEqual(containerBox.x);
    expect(overlayBox.y).toBeLessThanOrEqual(containerBox.y);
    expect(overlayBox.width).toBeGreaterThanOrEqual(containerBox.width);
    expect(overlayBox.height).toBeGreaterThanOrEqual(containerBox.height);
  });

  test('should have glassmorphism styling', async ({ page }) => {
    const overlay = page.locator('[data-testid="gated-results"]');
    await expect(overlay).toBeVisible();

    // Check for backdrop blur effect
    const backdrop = page.locator('.gated-overlay-backdrop');
    await expect(backdrop).toBeVisible();

    // Check for glassmorphic content
    const content = page.locator('.gated-overlay-content');
    await expect(content).toBeVisible();

    // Check completion icon
    const icon = page.locator('.completion-icon');
    await expect(icon).toBeVisible();
    await expect(icon).toContainText('✓');

    // Check title
    const title = page.locator('.completion-title');
    await expect(title).toBeVisible();
    await expect(title).toContainText('Your citation validation is complete');

    // Check reveal button
    const button = page.locator('.reveal-button');
    await expect(button).toBeVisible();
    await expect(button).toContainText('View Results');
  });

  test('should adapt to different table sizes', async ({ page }) => {
    // Test with single citation
    await page.evaluate(() => {
      // Simulate single citation validation
      window.dispatchEvent(new CustomEvent('validation-complete', {
        detail: {
          results: [
            {
              id: '1',
              text: 'Single citation test',
              status: 'valid',
              errors: []
            }
          ]
        }
      }));
    });

    const overlay = page.locator('[data-testid="gated-results"]');
    await expect(overlay).toBeVisible();

    // Overlay should adapt to single citation size
    const overlayBox = await overlay.boundingBox();
    expect(overlayBox.height).toBeGreaterThan(100);
    expect(overlayBox.height).toBeLessThan(800);
  });

  test('should handle multiple citations', async ({ page }) => {
    // Test with multiple citations
    await page.evaluate(() => {
      // Simulate multiple citation validation
      window.dispatchEvent(new CustomEvent('validation-complete', {
        detail: {
          results: Array(10).fill(null).map((_, i) => ({
            id: `${i + 1}`,
            text: `Citation ${i + 1} test text`,
            status: i % 2 === 0 ? 'valid' : 'error',
            errors: i % 2 === 0 ? [] : ['Test error']
          }))
        }
      }));
    });

    const overlay = page.locator('[data-testid="gated-results"]');
    await expect(overlay).toBeVisible();

    // Overlay should expand for multiple citations
    const overlayBox = await overlay.boundingBox();
    expect(overlayBox.height).toBeGreaterThan(300);
  });

  test('reveal button should be clickable', async ({ page }) => {
    const button = page.locator('.reveal-button');
    await expect(button).toBeVisible();

    // Check button is enabled
    await expect(button).toBeEnabled();

    // Test button styling
    const buttonBox = await button.boundingBox();
    expect(buttonBox.height).toBeGreaterThan(40); // Accessibility: minimum touch target
  });
});