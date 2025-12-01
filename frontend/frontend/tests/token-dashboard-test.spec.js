const { test, expect } = require('@playwright/test');

test('should display token data in dashboard', async ({ page }) => {
  // Navigate to the production dashboard
  await page.goto('http://100.98.211.49:4646/');

  // Wait for the page to load
  await page.waitForTimeout(3000);

  // Check if token column has actual numbers instead of dashes
  const tokenCells = page.locator('td:nth-child(5)'); // 5th column should be tokens

  // Wait for data to load
  await page.waitForSelector('tbody tr', { timeout: 10000 });

  // Get text from token cells
  const tokenTexts = await tokenCells.allTextContents();

  console.log('Token cell contents:', tokenTexts);

  // Check if any cell has a number (not just '-')
  const hasNumbers = tokenTexts.some(text => text.trim() !== '-' && /\d/.test(text));

  console.log('Has token numbers:', hasNumbers);

  // Take a screenshot for verification
  await page.screenshot({ path: 'dashboard-token-test.png' });

  // This test passes if we find any numbers in token cells
  expect(hasNumbers).toBe(true);
});