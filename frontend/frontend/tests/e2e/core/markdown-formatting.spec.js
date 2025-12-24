import { test, expect } from '@playwright/test';

/**
 * Markdown Formatting Tests
 * 
 * These tests verify that markdown formatting (bold, italic) renders correctly
 * in the validation results table. The TipTap editor converts markdown to HTML,
 * and that HTML should be preserved and displayed in the results.
 * 
 * Uses route mocking for fast, deterministic execution.
 */

// Helper to set up route mocking
async function setupMockRoutes(page, mockResults) {
  // Mock job creation
  await page.route(/\/api\/validate\/async/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        job_id: 'mock-markdown-job-' + Date.now(),
        status: 'pending',
        experiment_variant: 0
      })
    });
  });

  // Mock job polling - return completed with provided results
  await page.route(/\/api\/jobs\/.*/, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'completed',
        results: {
          results: mockResults,
          user_status: { type: 'free', validations_used: 3, limit: 5 }
        }
      })
    });
  });
}

test.describe('Markdown Formatting in Validation Table', () => {
  test('should display **bold** and _italic_ formatting correctly in validation results', async ({ page }) => {
    // Mock results with HTML formatting (as they would come from the backend after processing TipTap HTML)
    const mockResults = [
      {
        original: 'Smith, J. (2020). <strong>Journal of Testing</strong>, 15(2), 123-145.',
        source_type: 'journal',
        errors: []
      },
      {
        original: 'Brown, A. (2021). <em>Academic Press</em>, New York.',
        source_type: 'book',
        errors: []
      },
      {
        original: 'Wilson, K. (2019). Mixed <strong>bold</strong> and <em>italic</em> formatting.',
        source_type: 'journal',
        errors: []
      }
    ];

    await setupMockRoutes(page, mockResults);

    // Navigate to the citation checker
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Fill in citations (editor will convert markdown to HTML)
    await page.fill('textarea, .ProseMirror, [contenteditable="true"]', `Smith, J. (2020). **Journal of Testing**, 15(2), 123-145.
Brown, A. (2021). _Academic Press_, New York.
Wilson, K. (2019). Mixed **bold** and _italic_ formatting.`);

    // Submit the form
    await page.click('button[type="submit"]');

    // Wait for validation table with actual formatted content to appear
    // This is more robust than just waiting for a container
    await expect(page.locator('.validation-table strong').first()).toBeVisible({ timeout: 15000 });

    // Handle gated results if present - click to reveal full results
    const gatedOverlay = page.locator('[data-testid="gated-results"]');
    if (await gatedOverlay.isVisible()) {
      await page.locator('button:has-text("View Results")').first().click();
      // Wait for the overlay to be hidden after clicking
      await expect(gatedOverlay).not.toBeVisible({ timeout: 10000 });
    }

    // Wait for all expected formatting to be present before checking content
    // This ensures the mock response has fully rendered
    await expect(page.locator('.validation-table strong:has-text("Journal of Testing")')).toBeVisible();
    await expect(page.locator('.validation-table em:has-text("Academic Press")')).toBeVisible();
    await expect(page.locator('.validation-table strong:has-text("bold")')).toBeVisible();
    await expect(page.locator('.validation-table em:has-text("italic")')).toBeVisible();

    // Verify table text content
    const tableContent = await page.locator('.validation-table').textContent();
    expect(tableContent).toContain('Journal of Testing');
    expect(tableContent).toContain('Academic Press');
  });

  test('should handle complex nested markdown formatting', async ({ page }) => {
    // Mock results with nested HTML formatting
    const mockResults = [
      {
        original: 'Davis, M. (2022). <strong><em>Complex nested formatting</em></strong> in citation.',
        source_type: 'journal',
        errors: []
      }
    ];

    await setupMockRoutes(page, mockResults);

    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Test complex nested formatting
    await page.fill('textarea, .ProseMirror, [contenteditable="true"]', `Davis, M. (2022). **_Complex nested formatting_** in citation.`);

    await page.click('button[type="submit"]');

    // Wait for validation table with nested formatted content to appear
    await expect(page.locator('.validation-table strong em, .validation-table em strong').first()).toBeVisible({ timeout: 15000 });

    // Handle gated results if present
    const gatedOverlay = page.locator('[data-testid="gated-results"]');
    if (await gatedOverlay.isVisible()) {
      await page.locator('button:has-text("View Results")').first().click();
      await expect(gatedOverlay).not.toBeVisible({ timeout: 10000 });
    }

    // Verify nested formatting is visible in the table
    // The mock returns <strong><em>Complex nested formatting</em></strong>
    await expect(page.locator('.validation-table strong em:has-text("Complex nested formatting"), .validation-table em strong:has-text("Complex nested formatting")').first()).toBeVisible();
  });
});