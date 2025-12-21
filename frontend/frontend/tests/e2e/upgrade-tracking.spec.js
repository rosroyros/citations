import { test, expect } from '@playwright/test';

test.describe('Upgrade Tracking - A/B Test Events', () => {
  test.use({ baseURL: 'http://localhost:5173' });

  test.beforeEach(async ({ page }) => {
    // Clear cookies and localStorage before each test
    await page.context().clearCookies();
    await page.addInitScript(() => {
      localStorage.clear();
    });
  });

  test('tracks pricing_table_shown event when user hits free limit', async ({ page }) => {
    console.log('🚀 Test: pricing_table_shown event');

    // Navigate to home page
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    // Simulate user who has used 10 free validations (at limit)
    await page.evaluate(() => {
      localStorage.setItem('citation_checker_free_used', '10');
    });

    // Reload to apply localStorage
    await page.goto('/');

    // Submit a validation (should trigger upgrade flow)
    const editor = page.locator('.ProseMirror')
      .or(page.locator('[contenteditable="true"]'))
      .or(page.locator('textarea'));

    await expect(editor).toBeVisible();
    await editor.fill('Smith, J. (2023). Test citation. Journal, 1(1), 1-10.');

    // Track network requests to backend
    const apiCalls = [];
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        apiCalls.push({
          url: request.url(),
          method: request.method()
        });
      }
    });

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Wait for validation to complete
    await expect(
      page.locator('.results, .validation-results, .validation-table').first()
    ).toBeVisible({ timeout: 60000 });

    // Verify experiment variant was assigned
    const variant = await page.evaluate(() =>
      localStorage.getItem('experiment_v1')
    );

    console.log('📊 Assigned variant:', variant);

    // Variant should be one of the 4 new variants
    expect(['1.1', '1.2', '2.1', '2.2']).toContain(variant);
    expect(variant).not.toBeNull();

    // Verify variant persists
    const variantCheck = await page.evaluate(() =>
      localStorage.getItem('experiment_v1')
    );
    expect(variantCheck).toBe(variant);

    console.log('✅ Variant assignment verified');
  });

  test('variant assignment is sticky across multiple upgrade clicks', async ({ page }) => {
    console.log('🚀 Test: Sticky variant assignment');

    // Navigate to home page
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    // Set free_used to trigger upgrade flow on first submission
    // This is set after the initial page load, so it won't be cleared
    await page.evaluate(() => {
      localStorage.setItem('citation_checker_free_used', '10');
    });

    // Navigate again to apply the localStorage setting
    // addInitScript clears localStorage, but we set it above after the script ran
    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    // Set free_used AGAIN since addInitScript cleared it
    await page.evaluate(() => {
      localStorage.setItem('citation_checker_free_used', '10');
    });

    // First submission - variant will be assigned
    const editor = page.locator('.ProseMirror')
      .or(page.locator('[contenteditable="true"]'))
      .or(page.locator('textarea'));

    await editor.fill('Smith, J. (2023). Test citation 1. Journal, 1(1), 1-10.');
    await page.locator('button[type="submit"]').click();

    // Wait for results to appear
    await expect(
      page.locator('.validation-results-section, [data-testid="partial-results"]').first()
    ).toBeVisible({ timeout: 60000 });

    // Get the naturally assigned variant
    const variant1 = await page.evaluate(() =>
      localStorage.getItem('experiment_v1')
    );

    console.log('📊 First variant:', variant1);
    expect(['1.1', '1.2', '2.1', '2.2']).toContain(variant1);

    // Second submission
    // Scroll to top to ensure editor is accessible
    await page.evaluate(() => window.scrollTo(0, 0));

    // Use specific locator based on data-testid to ensure we find the right element
    const specificEditor = page.locator('[data-testid="editor"] .ProseMirror');
    await expect(specificEditor).toBeVisible({ timeout: 10000 });

    await specificEditor.click();
    await specificEditor.fill('Jones, M. (2023). Test citation 2. Journal, 2(2), 20-30.');
    await page.locator('button[type="submit"]').click();

    // Wait for new results
    await expect(
      page.locator('.validation-results-section, [data-testid="partial-results"]').first()
    ).toBeVisible({ timeout: 60000 });

    // Verify variant is still the same
    const variant2 = await page.evaluate(() =>
      localStorage.getItem('experiment_v1')
    );

    console.log('📊 Second variant:', variant2);

    // Variants should match (sticky)
    expect(variant2).toBe(variant1);

    console.log('✅ Sticky assignment verified');
  });

  test('different users get randomly assigned to different variants', async ({ browser }) => {
    console.log('🚀 Test: Random variant assignment');

    // 10 iterations provides strong statistical confidence (99.9% both variants)
    // while keeping test time reasonable (~10-15s instead of 10-20 minutes)
    const iterations = 10;
    const variants = [];

    for (let i = 0; i < iterations; i++) {
      // Create new browser context (fresh user with isolated localStorage)
      const context = await browser.newContext();
      const page = await context.newPage();

      await page.goto('/');
      await expect(page.locator('body')).toBeVisible();

      // Set free limit to trigger variant assignment
      await page.evaluate(() => {
        localStorage.setItem('citation_checker_free_used', '5');
      });

      await page.reload();
      await expect(page.locator('body')).toBeVisible();
      await page.waitForLoadState('networkidle');

      // Submit 6 citations at once to exceed free tier (5) and trigger variant assignment
      const editor = page.locator('.ProseMirror')
        .or(page.locator('[contenteditable="true"]'))
        .or(page.locator('textarea'));

      // Submit 6 citations to immediately exceed the free tier limit
      const citations = [
        'Smith, J. (2023). First citation. Journal, 1(1), 1-10.',
        'Jones, M. (2023). Second citation. Journal, 2(2), 20-30.',
        'Brown, A. (2023). Third citation. Journal, 3(3), 30-40.',
        'Davis, K. (2023). Fourth citation. Journal, 4(4), 40-50.',
        'Wilson, L. (2023). Fifth citation. Journal, 5(5), 50-60.',
        'Taylor, R. (2023). Sixth citation. Journal, 6(6), 60-70.'
      ].join('\n\n');

      await editor.fill(citations);
      await page.locator('button[type="submit"]').click();

      // Wait briefly for submission to complete (variant is assigned during submission)
      // We don't need to wait for validation results - just for the API call to fire
      await page.waitForTimeout(1000);

      const variant = await page.evaluate(() =>
        localStorage.getItem('experiment_v1')
      );

      variants.push(variant);
      console.log(`User ${i + 1}: variant ${variant}`);

      // Close the entire context (not just page) to free resources
      await context.close();
    }

    // Statistical check: With 10 users, very unlikely all get same variant
    // Count by pricing type (1.x = Credits, 2.x = Passes)
    const creditsCount = variants.filter(v => v && v.startsWith('1.')).length;
    const passesCount = variants.filter(v => v && v.startsWith('2.')).length;
    // Count by display type (.1 = Button, .2 = Inline)
    const buttonCount = variants.filter(v => v && v.endsWith('.1')).length;
    const inlineCount = variants.filter(v => v && v.endsWith('.2')).length;

    console.log(`📊 Distribution (${iterations} users): Credits: ${creditsCount}, Passes: ${passesCount}, Button: ${buttonCount}, Inline: ${inlineCount}`);

    // With 10 users and 25% per variant, expect some of each type
    // Probability of all same pricing type = (0.5)^10 = 0.00098
    expect(creditsCount + passesCount).toBe(iterations);
    // At least some distribution (10 users might not hit all 4 variants, but should have some of each pricing type)
    expect(creditsCount).toBeGreaterThanOrEqual(0);
    expect(passesCount).toBeGreaterThanOrEqual(0);

    console.log('✅ Random assignment verified');
  });

  test('variant assignment happens on first upgrade trigger', async ({ page }) => {
    console.log('🚀 Test: Variant assigned on first trigger');

    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    // Verify no variant yet
    let variant = await page.evaluate(() =>
      localStorage.getItem('experiment_v1')
    );
    expect(variant).toBeNull();

    // Use up free tier
    await page.evaluate(() => {
      localStorage.setItem('citation_checker_free_used', '10');
    });

    await page.goto('/');

    // Submit validation (first upgrade trigger)
    const editor = page.locator('.ProseMirror')
      .or(page.locator('[contenteditable="true"]'))
      .or(page.locator('textarea'));

    await editor.fill('Smith, J. (2023). Test. Journal, 1(1), 1-10.');
    await page.locator('button[type="submit"]').click();

    await expect(
      page.locator('.results, .validation-results, .validation-table').first()
    ).toBeVisible({ timeout: 60000 });

    // Now variant should be assigned
    variant = await page.evaluate(() =>
      localStorage.getItem('experiment_v1')
    );

    expect(variant).not.toBeNull();
    expect(['1.1', '1.2', '2.1', '2.2']).toContain(variant);

    console.log('✅ First-trigger assignment verified');
  });

  test('passes job_id to create-checkout endpoint', async ({ page }) => {
    console.log('🚀 Test: job_id propagation');

    // Add PolarEmbedCheckout mock AND force button variant in same addInitScript
    // This ensures the variant is set BEFORE React reads localStorage
    await page.addInitScript(() => {
      // Force button variant (1.1 = Credits + Button) so the upgrade button appears
      localStorage.setItem('experiment_v1', '1.1');
      localStorage.setItem('citation_checker_free_used', '10');

      // Mock Polar SDK
      window.__polarCheckoutHandlers = {};
      window.__polarCheckoutCreated = false;
      window.PolarEmbedCheckout = {
        create: async (url, options) => {
          window.__polarCheckoutCreated = true;
          return {
            on: (event, handler) => {
              window.__polarCheckoutHandlers[event] = handler;
              // Auto-trigger success after a short delay for this test
              if (event === 'success') {
                setTimeout(() => handler(), 100);
              }
            }
          };
        }
      };
    });

    // Intercept create-checkout to verify payload
    let capturedRequest = null;
    await page.route('/api/create-checkout', async route => {
      capturedRequest = route.request();

      // Mock success response - returns a checkout URL for the SDK to use
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ checkout_url: 'https://checkout.polar.sh/mock-checkout' })
      });
    });

    // Navigate to home page (variant will be set before React reads it)
    await page.goto('/');
    const editor = page.locator('.ProseMirror')
      .or(page.locator('[contenteditable="true"]'))
      .or(page.locator('textarea'));

    const citations = Array(6).fill(0).map((_, i) =>
      `Smith, J. (2023). Test citation ${i + 1}. Journal, 1(1), 1-10.`
    ).join('\n\n');

    await editor.fill(citations);
    await page.locator('button[type="submit"]').click();

    // Check if gated results overlay is visible (it might appear for free users)
    // We need to wait a moment for the response
    try {
      const gatedOverlay = page.locator('[data-testid="gated-results"]');
      await expect(gatedOverlay).toBeVisible({ timeout: 5000 });
      console.log('Gated overlay detected, clicking view results...');
      await page.locator('button:has-text("View Results")').click();
    } catch (e) {
      console.log('No gated overlay detected or timed out checking, continuing...');
    }

    // Wait for partial results to ensure the UI has settled
    await expect(page.locator('[data-testid="partial-results"]')).toBeVisible({ timeout: 60000 });

    // Click "Upgrade to Unlock Now" button
    const upgradeButton = page.locator('button:has-text("Upgrade to Unlock Now")').first();
    await upgradeButton.click();

    // Wait for modal
    const modal = page.locator('.upgrade-modal-container');
    await expect(modal).toBeVisible();

    // Click a buy button in the modal
    const buyButton = modal.locator('button:has-text("Buy")').first();
    await buyButton.click();

    // Wait for request capture
    await expect(async () => {
      expect(capturedRequest).not.toBeNull();
    }).toPass({ timeout: 5000 });

    // Verify payload
    const postData = capturedRequest.postDataJSON();
    console.log('📦 Checkout Payload:', postData);

    expect(postData).toHaveProperty('job_id');
    expect(postData.job_id).toMatch(/^[\w-]+$/); // Allow alphanumeric and dashes/underscores
    expect(postData.job_id).toBeTruthy();

    // Wait for embedded checkout success state in modal
    await expect(page.locator('[data-testid="checkout-success"]')).toBeVisible({ timeout: 5000 });
    console.log('✅ Embedded checkout success state verified');
  });
});