const { test, expect } = require('@playwright/test');

test('simple test', async ({ page }) => {
  await page.goto('http://localhost:5174');
  const title = await page.title();
  expect(title).toBe('Vite + React');
});
