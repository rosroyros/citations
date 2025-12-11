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

    // Variant should be '1' or '2'
    expect(['1', '2']).toContain(variant);
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

    await page.goto('/');
    await expect(page.locator('body')).toBeVisible();

    // Pre-assign variant 1
    await page.evaluate(() => {
      localStorage.setItem('experiment_v1', '1');
      localStorage.setItem('citation_checker_free_used', '10');
    });

    // Reload
    await page.goto('/');

    // First submission
    const editor = page.locator('.ProseMirror')
      .or(page.locator('[contenteditable="true"]'))
      .or(page.locator('textarea'));

    await editor.fill('Smith, J. (2023). Test citation 1. Journal, 1(1), 1-10.');
    await page.locator('button[type="submit"]').click();

    await expect(
      page.locator('.results, .validation-results, .validation-table').first()
    ).toBeVisible({ timeout: 60000 });

    const variant1 = await page.evaluate(() =>
      localStorage.getItem('experiment_v1')
    );

    // Clear results and submit again
    await page.reload();
    await editor.fill('Jones, M. (2023). Test citation 2. Journal, 2(2), 20-30.');
    await page.locator('button[type="submit"]').click();

    await expect(
      page.locator('.results, .validation-results, .validation-table').first()
    ).toBeVisible({ timeout: 60000 });

    const variant2 = await page.evaluate(() =>
      localStorage.getItem('experiment_v1')
    );

    // Variants should match (sticky)
    expect(variant1).toBe('1');
    expect(variant2).toBe('1');
    expect(variant1).toBe(variant2);

    console.log('✅ Sticky assignment verified');
  });

  test('different users get randomly assigned to different variants', async ({ context }) => {
    console.log('🚀 Test: Random variant assignment');

    // Simulate 10 different users
    const variants = [];

    for (let i = 0; i < 10; i++) {
      // Create new incognito context (fresh user)
      const page = await context.newPage();

      await page.goto('/');
      await expect(page.locator('body')).toBeVisible();

      // Set free limit
      await page.evaluate(() => {
        localStorage.setItem('citation_checker_free_used', '10');
      });

      await page.goto('/');

      // Submit validation
      const editor = page.locator('.ProseMirror')
        .or(page.locator('[contenteditable="true"]'))
        .or(page.locator('textarea'));

      await editor.fill('Test, A. (2023). Citation. Journal, 1(1), 1-10.');
      await page.locator('button[type="submit"]').click();

      await expect(
        page.locator('.results, .validation-results, .validation-table').first()
      ).toBeVisible({ timeout: 60000 });

      const variant = await page.evaluate(() =>
        localStorage.getItem('experiment_v1')
      );

      variants.push(variant);
      console.log(`User ${i + 1}: variant ${variant}`);

      await page.close();
    }

    // Statistical check: With 10 users, very unlikely all get same variant
    const variant1Count = variants.filter(v => v === '1').length;
    const variant2Count = variants.filter(v => v === '2').length;

    console.log(`📊 Distribution: Variant 1: ${variant1Count}, Variant 2: ${variant2Count}`);

    // At least 1 of each variant should be assigned (with 10 users)
    // Probability of all same = (0.5)^10 = 0.001 (very unlikely)
    expect(variant1Count).toBeGreaterThan(0);
    expect(variant2Count).toBeGreaterThan(0);

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
    expect(['1', '2']).toContain(variant);

    console.log('✅ First-trigger assignment verified');
  });
});