const { test, expect } = require('@playwright/test');

// Backend helper to grant credits
async function grantCredits(request, userId, amount) {
  const response = await request.post('http://localhost:8000/test/grant-credits', {
    data: { user_id: userId, amount: amount }
  });
  expect(response.ok()).toBeTruthy();
}

// Backend helper to grant pass
async function grantPass(request, userId, days) {
  const response = await request.post('http://localhost:8000/test/grant-pass', {
    data: { user_id: userId, days: days }
  });
  expect(response.ok()).toBeTruthy();
}

test.describe('Pricing Variants E2E', () => {

  test('Variant 1: Credits Flow', async ({ page, request }) => {
    // 1. Force Variant 1 (Credits)
    await page.goto('http://localhost:5173/');
    await page.evaluate(() => {
      localStorage.setItem('experiment_v1', '1');
    });
    await page.reload();

    // 2. Submit Citation (Mock Mode will return results)
    await page.fill('.ProseMirror', 'Smith, J. (2020). Test citation.');
    await page.click('button[type="submit"]');

    // 3. Wait for Results
    await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 30000 });

    // 4. Submit 6 citations to hit free limit
    await page.fill('.ProseMirror', ''); // Clear
    const citations = Array(6).fill('Smith, J. (2020). Test citation.').join('\n\n');
    await page.fill('.ProseMirror', citations);
    await page.click('button[type="submit"]');

    // Wait for "limit reached" state (Partial Results)
    await expect(page.locator('.upgrade-banner')).toBeVisible({ timeout: 30000 });
    const upgradeButton = page.getByRole('button', { name: 'Upgrade to Unlock Now' });
    await expect(upgradeButton).toBeVisible();

    // 5. Click Upgrade
    await upgradeButton.click();

    // 6. Verify Pricing Table (Credits)
    // Credits table has "100 Credits" etc.
    await expect(page.getByText('100 Credits', { exact: true })).toBeVisible();
    await expect(page.getByText('100 citation validations')).toBeVisible();

    // 7. Click Buy (100 credits)
    // Note: We need to handle the new tab or redirection? 
    // The current implementation uses window.location.href which navigates the current page.
    await page.click('button:has-text("Buy 100 Credits")');

    // 8. Expect Redirect to Success
    await page.waitForURL('**/success?**');

    // 9. Verify Success Page
    const url = page.url();
    const token = new URL(url).searchParams.get('token');
    expect(token).toBeTruthy();

    // Manually grant credits to simulate webhook
    await grantCredits(request, token, 100);

    // Now success message should appear
    await expect(page.getByText('Payment Successful')).toBeVisible();
    await expect(page.getByText('100 Citation Credits')).toBeVisible();
  });

  test('Variant 2: Passes Flow', async ({ page, request }) => {
    // 1. Force Variant 2 (Passes)
    await page.goto('http://localhost:5173/');
    await page.evaluate(() => {
      localStorage.setItem('experiment_v1', '2');
    });
    await page.reload();

    // 2. Submit 6 citations to trigger limit
    const citations = Array(6).fill('Smith, J. (2020). Test citation.').join('\n\n');
    await page.fill('.ProseMirror', citations);
    await page.click('button[type="submit"]');

    // Wait for "limit reached" state
    await expect(page.locator('.upgrade-banner')).toBeVisible({ timeout: 30000 });
    const upgradeButton = page.getByRole('button', { name: 'Upgrade to Unlock Now' });
    await expect(upgradeButton).toBeVisible();

    // 3. Open Upgrade Modal
    await upgradeButton.click();

    // 4. Verify Pricing Table (Passes)
    await expect(page.getByText('7-Day Pass', { exact: true })).toBeVisible();
    await expect(page.getByText('Unlimited validations for 24 hours')).toBeVisible();

    // 5. Click Buy (7-day pass)
    await page.click('button:has-text("Buy 7-Day Pass")');

    // 6. Expect Redirect to Success
    await page.waitForURL('**/success?**');

    // 7. Verify Success
    const url = page.url();
    const token = new URL(url).searchParams.get('token');
    expect(token).toBeTruthy();

    // Manually grant pass
    await grantPass(request, token, 7);

    await expect(page.getByText('Payment Successful')).toBeVisible();
  });

});
