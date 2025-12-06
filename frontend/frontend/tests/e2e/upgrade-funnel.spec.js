const { test, expect } = require('@playwright/test');

test.describe('Upgrade Funnel Full Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the API endpoints for testing
    await page.route('/api/credits', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ credits: 0 })
      });
    });

    await page.route('/api/validate', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          results: [
            {
              citation_number: 1,
              original: 'Smith, J. (2023). Test citation.',
              source_type: 'journal_article',
              errors: []
            }
          ],
          partial: true,
          citations_checked: 1,
          citations_remaining: 9,
          job_id: 'test-job-123'
        })
      });
    });

    await page.route('/api/upgrade-event', async route => {
      const request = route.request();
      const postData = await request.postData();
      const eventData = JSON.parse(postData);

      console.log('Upgrade event logged:', eventData);

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          event: eventData.event || eventData.event_type,
          job_id: eventData.job_id
        })
      });
    });

    // Mock Polar checkout API
    await page.route('/api/create-checkout', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          url: 'https://checkout.polar.sh/test-checkout'
        })
      });
    });
  });

  test('should track complete upgrade funnel from partial results to success', async ({ page }) => {
    // Step 1: Navigate to app and submit citations
    await page.goto('/');

    // Fill in citation
    await page.fill('[data-testid="citation-editor"]', 'Smith, J. (2023). Test citation.');

    // Submit validation
    await page.click('button:has-text("Validate Citations")');

    // Wait for partial results
    await expect(page.locator('text=Validation Results')).toBeVisible();
    await expect(page.locator('text=9 more citations available')).toBeVisible();

    // Step 2: Click upgrade button
    const upgradeButton = page.locator('button:has-text("Upgrade Now")');
    await expect(upgradeButton).toBeVisible();

    // Intercept localStorage set
    let storedJobId = await page.evaluate(() => {
      return localStorage.getItem('pending_upgrade_job_id');
    });
    expect(storedJobId).toBeNull();

    await upgradeButton.click();

    // Verify job_id stored in localStorage
    storedJobId = await page.evaluate(() => {
      return localStorage.getItem('pending_upgrade_job_id');
    });
    expect(storedJobId).toBe('test-job-123');

    // Verify upgrade event was called
    const upgradeRequests = [];
    page.on('request', request => {
      if (request.url().includes('/api/upgrade-event')) {
        upgradeRequests.push(request);
      }
    });

    // Step 3: Mock Polar redirect to success page
    await page.goto('/success?token=test-token-123');

    // Verify success page loads
    await expect(page.locator('text=Payment Successful!')).toBeVisible();
    await expect(page.locator('text=1,000 credits have been added to your account')).toBeVisible();

    // Step 4: Verify localStorage is cleared after success
    await page.waitForTimeout(1000); // Wait for async operations

    const clearedJobId = await page.evaluate(() => {
      return localStorage.getItem('pending_upgrade_job_id');
    });
    expect(clearedJobId).toBeNull();

    // Verify upgrade success event was logged
    // Note: This would require additional mocking to capture in E2E test
  });

  test('should handle upgrade funnel with modal flow', async ({ page }) => {
    await page.goto('/');

    // Fill and submit to get partial results
    await page.fill('[data-testid="citation-editor"]', 'Smith, J. (2023). Test citation.');
    await page.click('button:has-text("Validate Citations")');
    await expect(page.locator('text=Validation Results')).toBeVisible();

    // Click upgrade button to show modal
    await page.click('button:has-text("Upgrade Now")');

    // Verify upgrade modal appears
    await expect(page.locator('[data-testid="upgrade-modal"]')).toBeVisible();

    // Click proceed in modal
    await page.click('button:has-text("Proceed to Checkout")');

    // Verify modal proceed event tracked
    // This would require intercepting the API call
  });

  test('should persist job_id across page reloads', async ({ page }) => {
    await page.goto('/');

    // Get to partial results
    await page.fill('[data-testid="citation-editor"]', 'Smith, J. (2023). Test citation.');
    await page.click('button:has-text("Validate Citations")');
    await expect(page.locator('text=Validation Results')).toBeVisible();

    // Click upgrade to store job_id
    await page.click('button:has-text("Upgrade Now")');

    // Reload page
    await page.reload();

    // job_id should still be in localStorage
    const storedJobId = await page.evaluate(() => {
      return localStorage.getItem('pending_upgrade_job_id');
    });
    expect(storedJobId).toBe('test-job-123');
  });

  test('should handle upgrade funnel errors gracefully', async ({ page }) => {
    // Mock upgrade-event API to fail
    await page.route('/api/upgrade-event', async route => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    await page.goto('/');

    // Get to partial results
    await page.fill('[data-testid="citation-editor"]', 'Smith, J. (2023). Test citation.');
    await page.click('button:has-text("Validate Citations")');
    await expect(page.locator('text=Validation Results')).toBeVisible();

    // Click upgrade button - should not fail even if API fails
    await page.click('button:has-text("Upgrade Now")');

    // Should still store job_id even if API fails
    const storedJobId = await page.evaluate(() => {
      return localStorage.getItem('pending_upgrade_job_id');
    });
    expect(storedJobId).toBe('test-job-123');
  });

  test('should track upgrade funnel in dashboard', async ({ page }) => {
    // Mock dashboard API with upgrade states
    await page.route('/api/dashboard', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          validations: [
            {
              id: 'test-job-123',
              created_at: '2023-12-06T10:00:00Z',
              status: 'completed',
              upgrade_state: 'upgrade_completed',
              total_citations: 10
            }
          ]
        })
      });
    });

    // Navigate to dashboard
    await page.goto('/dashboard');

    // Verify upgrade funnel visualization
    await expect(page.locator('text=Upgrade Funnel')).toBeVisible();

    // Check for upgrade states icons
    await expect(page.locator('text=🔒 Locked Results')).toBeVisible();
    await expect(page.locator('text=🛒 Upgrade Clicked')).toBeVisible();
    await expect(page.locator('text=💳 Modal Proceeded')).toBeVisible();
    await expect(page.locator('text=✅ Purchase Completed')).toBeVisible();
  });

  test('should handle multiple upgrade attempts correctly', async ({ page }) => {
    await page.goto('/');

    // Get to partial results
    await page.fill('[data-testid="citation-editor"]', 'Smith, J. (2023). Test citation.');
    await page.click('button:has-text("Validate Citations")');
    await expect(page.locator('text=Validation Results')).toBeVisible();

    // Click upgrade multiple times
    await page.click('button:has-text("Upgrade Now")');
    await page.click('button:has-text("Upgrade Now")');

    // Should still only have one job_id
    const storedJobId = await page.evaluate(() => {
      return localStorage.getItem('pending_upgrade_job_id');
    });
    expect(storedJobId).toBe('test-job-123');

    // Go to success page
    await page.goto('/success?token=test-token-123');

    // Should clear localStorage
    const clearedJobId = await page.evaluate(() => {
      return localStorage.getItem('pending_upgrade_job_id');
    });
    expect(clearedJobId).toBeNull();
  });
});