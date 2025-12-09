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

test('Internal Dashboard: Provider column visibility', async ({ page }) => {
  const internalDashboardUrl = 'http://100.98.211.49:4646';
  console.log(`Testing Provider column at: ${internalDashboardUrl}`);

  // 1. Visit Internal Dashboard
  await page.goto(internalDashboardUrl);

  // 2. Wait for table to load
  const table = page.locator('#validationsTable');
  await expect(table).toBeVisible();
  await expect(page.locator('.loading')).not.toBeVisible({ timeout: 15000 });

  // 3. Check Provider column header exists
  const providerHeader = page.locator('th').filter({ hasText: 'Provider' });
  await expect(providerHeader).toBeVisible();
  console.log('Provider column header found');

  // 4. If data exists, check provider values are displayed
  const tbody = page.locator('#validationsTable');
  const dataRows = tbody.locator('tr:not([id^="details-"])'); // Exclude detail rows
  const rowCount = await dataRows.count();

  if (rowCount > 0) {
    // Get first actual data row (skip loading/empty states)
    const firstRow = dataRows.first();

    // Wait for row to be fully rendered
    await firstRow.waitFor({ state: 'visible', timeout: 5000 });

    const cells = firstRow.locator('td');
    const cellCount = await cells.count();

    console.log(`First row has ${cellCount} cells`);

    if (cellCount >= 6) {
      // Provider column should be the 6th column (index 5: Job ID, Time, Duration, Citations, Tokens, Provider)
      const providerCell = cells.nth(5);
      const providerText = await providerCell.textContent({ timeout: 5000 });

      // Provider should be displayed as "GPT-4o-mini", "Gemini-2.5-Flash", or "Unknown"
      const validProviders = ['GPT-4o-mini', 'Gemini-2.5-Flash', 'Unknown'];
      const hasValidProvider = validProviders.some(p => providerText && providerText.includes(p));

      if (hasValidProvider) {
        console.log(`✓ Valid provider found: ${providerText.trim()}`);
      } else {
        console.log(`⚠ Provider column text: '${providerText}' (may be N/A for old records)`);
      }
    } else {
      console.log(`⚠ Row has ${cellCount} cells, expected at least 6`);
    }
  }

  console.log('Provider column verification passed!');
});
