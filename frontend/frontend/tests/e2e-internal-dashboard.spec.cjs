const { test, expect } = require('@playwright/test');

test('Internal Dashboard: Load and verify data', async ({ page }) => {
  const internalDashboardUrl = 'http://100.98.211.49:4646';
  console.log(`Testing Internal Dashboard at: ${internalDashboardUrl}`);

  // 1. Visit Internal Dashboard
  await page.goto(internalDashboardUrl);

  // 2. Verify Title
  await expect(page).toHaveTitle(/Internal Dashboard/);

  // 3. Verify Key Elements
  await expect(page.locator('.title')).toHaveText('Internal Dashboard - Citation Validations');
  await expect(page.locator('.filters')).toBeVisible();
  await expect(page.locator('#stats')).toBeVisible();

  // 4. Wait for Data Loading
  // The dashboard shows "Loading data..." initially
  const table = page.locator('#validationsTable');
  await expect(table).toBeVisible();
  
  // Wait for loading to disappear (either data appears or "No validations found")
  // The loading row has class 'loading'
  await expect(page.locator('.loading')).not.toBeVisible({ timeout: 15000 });

  // 5. Verify Data Rows exist (if any)
  // If we just ran a test, there should be data.
  // Check for at least one row that is NOT an error message
  const rows = table.locator('tr');
  const count = await rows.count();
  console.log(`Found ${count} rows in validation table`);
  
  // If we have data, verify structure
  if (count > 0) {
      const firstRow = rows.first();
      await expect(firstRow).toBeVisible();
      // Check for status badge
      await expect(firstRow.locator('span[class^="status-"]')).toBeVisible();
  }

  console.log('Internal Dashboard verification passed!');
});
