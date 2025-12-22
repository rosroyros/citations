const { test, expect } = require('@playwright/test');

test.describe('Upgrade Success Event Logging', () => {
  test('logs success event when pending_upgrade_job_id exists', async ({ page }) => {
    // Mock the API endpoint
    let upgradeEventRequest = null;
    await page.route('/api/upgrade-event', async route => {
      upgradeEventRequest = route.request();
      await route.fulfill({ status: 200, body: JSON.stringify({ success: true }) });
    });

    // Mock the credits endpoint to avoid errors/delays
    await page.route('/api/credits?token=*', async route => {
      await route.fulfill({ status: 200, body: JSON.stringify({ credits: 10 }) });
    });

    // Set up localStorage before navigation
    const jobId = 'job_12345';
    await page.addInitScript((id) => {
      localStorage.setItem('pending_upgrade_job_id', id);
    }, jobId);

    // Navigate to Success page with token
    await page.goto('/success?token=test_token');

    // Wait for localStorage to be processed
    await expect(page.evaluate(() => localStorage.getItem('pending_upgrade_job_id'))).resolves.toBeNull();

    // Verify request was made
    expect(upgradeEventRequest).not.toBeNull();
    expect(upgradeEventRequest.method()).toBe('POST');
    const postData = upgradeEventRequest.postDataJSON();
    expect(postData).toEqual({
      job_id: jobId,
      event: 'success'
    });

    // Verify headers
    const headers = upgradeEventRequest.headers();
    expect(headers['x-user-token']).toBe('test_token');

    // Verify localStorage is cleared
    const storedJobId = await page.evaluate(() => localStorage.getItem('pending_upgrade_job_id'));
    expect(storedJobId).toBeNull();
  });

  test('does not log event when pending_upgrade_job_id is missing', async ({ page }) => {
    // Mock the API endpoint
    let requestMade = false;
    await page.route('/api/upgrade-event', async route => {
      requestMade = true;
      await route.fulfill({ status: 200 });
    });

    // Mock the credits endpoint
    await page.route('/api/credits?token=*', async route => {
      await route.fulfill({ status: 200, body: JSON.stringify({ credits: 10 }) });
    });

    // Navigate to Success page with token (no localStorage set)
    await page.goto('/success?token=test_token');

    // Wait by checking localStorage is still null
    await expect.poll(() => page.evaluate(() => localStorage.getItem('pending_upgrade_job_id')), { timeout: 3000 }).toBeNull();

    // Verify no request was made
    expect(requestMade).toBe(false);
  });

  test('clears localStorage even if API call fails', async ({ page }) => {
    // Mock the API endpoint to fail
    await page.route('/api/upgrade-event', async route => {
      await route.fulfill({ status: 500 });
    });

    // Mock the credits endpoint
    await page.route('/api/credits?token=*', async route => {
      await route.fulfill({ status: 200, body: JSON.stringify({ credits: 10 }) });
    });

    // Set up localStorage
    const jobId = 'job_fail_test';
    await page.addInitScript((id) => {
      localStorage.setItem('pending_upgrade_job_id', id);
    }, jobId);

    // Navigate to Success page
    await page.goto('/success?token=test_token');

    // Wait for localStorage to be cleared even after API failure
    await expect.poll(() => page.evaluate(() => localStorage.getItem('pending_upgrade_job_id')), { timeout: 3000 }).toBeNull();

    // Verify localStorage is cleared
    const storedJobId = await page.evaluate(() => localStorage.getItem('pending_upgrade_job_id'));
    expect(storedJobId).toBeNull();
  });
});
