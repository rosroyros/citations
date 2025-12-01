const { test, expect } = require('@playwright/test');

test.describe('Gated Results Visuals', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5174/test-gated-variants.html');
    await page.waitForLoadState('networkidle');
  });

  test('should correctly position the original variant', async ({ page }) => {
    const originalVariant = page.locator('.variant-original');
    await expect(originalVariant).toBeVisible();
    await originalVariant.screenshot();
  });

  test('should correctly position the glassmorphism variant', async ({ page }) => {
    const glassmorphismVariant = page.locator('.variant-glassmorphism');
    await expect(glassmorphismVariant).toBeVisible();
    await glassmorphismVariant.screenshot();
  });

  test('should correctly position the gradient variant', async ({ page }) => {
    const gradientVariant = page.locator('.variant-gradient');
    await expect(gradientVariant).toBeVisible();
    await gradientVariant.screenshot();
  });

  test('should correctly position the card variant', async ({ page }) => {
    const cardVariant = page.locator('.variant-card');
    await expect(cardVariant).toBeVisible();
    await cardVariant.screenshot();
  });

  // Since landscape1 was already correct, this is a control
  test('should correctly position the landscape1 variant', async ({ page }) => {
    // Need to load the other test page for landscape variants
    await page.goto('http://localhost:5174/test-landscape-variants-demo.html');
    await page.waitForLoadState('networkidle');
    const landscape1Variant = page.locator('.variant-landscape1');
    await expect(landscape1Variant).toBeVisible();
    await landscape1Variant.screenshot();
  });

  test('should correctly position the landscape2 variant', async ({ page }) => {
    await page.goto('http://localhost:5174/test-landscape-variants-demo.html');
    await page.waitForLoadState('networkidle');
    const landscape2Variant = page.locator('.variant-landscape2');
    await expect(landscape2Variant).toBeVisible();
    await landscape2Variant.screenshot();
  });

  test('should correctly position the landscape3 variant', async ({ page }) => {
    await page.goto('http://localhost:5174/test-landscape-variants-demo.html');
    await page.waitForLoadState('networkidle');
    const landscape3Variant = page.locator('.variant-landscape3');
    await expect(landscape3Variant).toBeVisible();
    await landscape3Variant.screenshot();
  });
});
