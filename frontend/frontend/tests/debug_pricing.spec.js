import { test, expect } from '@playwright/test';

test('debug pricing table visual', async ({ page }) => {
  // Go to the specific test page
  await page.goto('/test-pricing-table-passes');

  // Wait for the content to be visible
  await page.waitForSelector('.grid');

  // Take a screenshot of the entire page
  await page.screenshot({ path: 'test-results/pricing-debug.png', fullPage: true });
  
  // Also take a screenshot of a single card to see details
  const card = page.locator('.grid > div').first();
  await card.screenshot({ path: 'test-results/pricing-card-debug.png' });

  // Get computed styles for the card title to check font family
  const title = card.locator('h3').first(); // CardTitle renders as div or h3? Shadcn CardTitle is usually a div or h3 depending on usage, but here it's likely a div inside CardHeader.
  // Actually checking the code: CardTitle is a div.
  // <CardTitle className="text-xl font-bold text-gray-900">
  
  const titleLocator = page.locator('.text-xl').first();
  const computedStyle = await titleLocator.evaluate((el) => {
    const style = window.getComputedStyle(el);
    return {
      fontFamily: style.fontFamily,
      fontSize: style.fontSize,
      fontWeight: style.fontWeight,
      color: style.color
    };
  });

  console.log('Computed Styles for Title:', computedStyle);
});
