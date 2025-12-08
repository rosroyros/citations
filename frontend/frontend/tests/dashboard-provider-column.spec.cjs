const { test, expect } = require('@playwright/test');

test('Dashboard: Provider Column and Detail View', async ({ page }) => {
  // Console logging
  page.on('console', msg => console.log(`PAGE LOG: ${msg.text()}`));
  page.on('pageerror', err => console.log(`PAGE ERROR: ${err}`));

  // Mock the Dashboard API response
  await page.route('**/api/dashboard?*', async route => {
    console.log('Intercepted dashboard request:', route.request().url());
    const json = {
      jobs: [
        {
          id: 'job-1',
          validation_id: 'val-1',
          session_id: 'sess-1',
          timestamp: '2023-10-27T10:00:00Z',
          status: 'completed',
          user: 'user@example.com',
          ip_address: '127.0.0.1',
          provider: 'model_a', // OpenAI
          source_type: 'text',
          api_version: 'v1',
          citation_count: 5,
          errors: 0,
          token_usage: { total: 100 },
          processing_time: '1.2s',
          revealed: 'No'
        },
        {
          id: 'job-2',
          validation_id: 'val-2',
          session_id: 'sess-2',
          timestamp: '2023-10-27T10:05:00Z',
          status: 'completed',
          user: 'user2@example.com',
          ip_address: '127.0.0.1',
          provider: 'model_b', // Gemini
          source_type: 'text',
          api_version: 'v1',
          citation_count: 3,
          errors: 1,
          token_usage: { total: 150 },
          processing_time: '0.8s',
          revealed: 'Yes'
        },
        {
          id: 'job-3',
          validation_id: 'val-3',
          session_id: 'sess-3',
          timestamp: '2023-10-27T10:10:00Z',
          status: 'failed',
          user: 'user3@example.com',
          ip_address: '127.0.0.1',
          provider: null, // Unknown
          source_type: 'text',
          api_version: 'v1',
          citation_count: 0,
          errors: null,
          token_usage: null,
          processing_time: null,
          revealed: 'N/A'
        }
      ]
    };
    await route.fulfill({ json });
  });

  // Mock Stats API
  await page.route('**/api/dashboard/stats', async route => {
    console.log('Intercepted stats request:', route.request().url());
    await route.fulfill({
      json: {
        total_requests: 3,
        completed: 2,
        failed: 1,
        total_citations: 8,
        total_errors: 1,
        avg_processing_time: '1.0s'
      }
    });
  });

  // Navigate to Dashboard
  // We assume the app is running on localhost:5173
  await page.goto('/dashboard');
  
  // Wait for loading to finish
  await expect(page.locator('.loading-state')).not.toBeVisible({ timeout: 5000 }).catch(() => console.log('Loading state still visible after 5s'));
  
  // Check for error state
  const errorState = page.locator('.error-state');
  if (await errorState.isVisible()) {
      console.log('Error state visible:', await errorState.textContent());
  }

  // Verify Provider Column Header
  await expect(page.getByRole('columnheader', { name: 'Provider' })).toBeVisible();

  // Verify Data Rows
  const rows = page.locator('table.data-table tbody tr');
  await expect(rows).toHaveCount(3);

  // Row 1: model_a -> OpenAI
  await expect(rows.nth(0).locator('.provider-cell')).toHaveText('OpenAI');
  
  // Row 2: model_b -> Gemini
  await expect(rows.nth(1).locator('.provider-cell')).toHaveText('Gemini');

  // Row 3: null -> Unknown
  await expect(rows.nth(2).locator('.provider-cell')).toHaveText('Unknown');

  // Verify Detail View for OpenAI
  await rows.nth(0).getByRole('button', { name: 'Details' }).click();
  const modal = page.locator('.modal-content');
  await expect(modal).toBeVisible();
  
  // Check Model Provider field in modal
  await expect(modal.locator('.detail-group').filter({ hasText: 'Model Provider' })).toContainText('OpenAI');
  
  // Close modal
  await modal.locator('.modal-close').click();
  await expect(modal).not.toBeVisible();

  // Verify Detail View for Gemini
  await rows.nth(1).getByRole('button', { name: 'Details' }).click();
  await expect(modal).toBeVisible();
  await expect(modal.locator('.detail-group').filter({ hasText: 'Model Provider' })).toContainText('Gemini');
});
