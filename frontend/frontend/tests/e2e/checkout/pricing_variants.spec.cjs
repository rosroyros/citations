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

  test('Variant 1.1 (Credits Button) - Regression Test', async ({ page, request }) => {
    // 1. Force Variant 1.1 (Credits + Button)
    await page.goto('http://localhost:5173/');
    await page.evaluate(() => {
      localStorage.setItem('experiment_v1', '1.1');
    });
    await page.reload();

    // 2. Submit 6 citations to hit free limit
    const citations = Array(6).fill('Smith, J. (2020). Test citation.').join('\n\n');
    await page.fill('.ProseMirror', citations);
    await page.click('button[type="submit"]');

    // Wait for results to be processed and displayed
    await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 30000 });

    // Check if results are gated and click through if necessary
    const viewResultsButton = page.getByRole('button', { name: /View Results/i });
    if (await viewResultsButton.isVisible()) {
      await viewResultsButton.click();
    }

    // Now check for PartialResults with upgrade banner
    const upgradeBanner = page.locator('.partial-results-container .upgrade-banner');
    await expect(upgradeBanner).toBeVisible({ timeout: 5000 });
    const upgradeButton = page.getByRole('button', { name: 'Upgrade to Unlock Now' });
    await expect(upgradeButton).toBeVisible();

    // 3. Verify pricing table is NOT visible yet (button variant)
    await expect(page.locator('.inline-pricing-container')).not.toBeVisible();

    // 4. Click Upgrade
    await upgradeButton.click();

    // 5. Verify Pricing Modal (Credits)
    await expect(page.locator('.upgrade-modal-container')).toBeVisible();
    await expect(page.getByText('100 Credits', { exact: true })).toBeVisible();
    await expect(page.getByText('For occasional users.')).toBeVisible();

    // 6. Click Buy (100 credits) - find button within the card containing "100 Credits"
    const credits100Card = page.locator('h3:has-text("100 Credits")').locator('..');
    await credits100Card.getByRole('button').click();

    // 7. Expect Redirect to Success
    await page.waitForURL('**/success?**');

    // 8. Verify Success Page
    const url = page.url();
    const token = new URL(url).searchParams.get('token');
    expect(token).toBeTruthy();

    // Manually grant credits to simulate webhook
    await grantCredits(request, token, 100);

    await expect(page.getByText('Payment Successful')).toBeVisible();
    await expect(page.getByText('100 Citation Credits')).toBeVisible();
  });

  test('Variant 1.2 (Credits Inline)', async ({ page, request }) => {
    // 1. Force Variant 1.2 (Credits + Inline)
    await page.goto('http://localhost:5173/');
    await page.evaluate(() => {
      localStorage.setItem('experiment_v1', '1.2');
    });
    await page.reload();

    // 2. Submit 6 citations to hit free limit
    const citations = Array(6).fill('Smith, J. (2020). Test citation.').join('\n\n');
    await page.fill('.ProseMirror', citations);
    await page.click('button[type="submit"]');

    // 3. Wait for validation results section to appear
    await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 30000 });

    // Check if results are gated and click through if necessary
    const viewResultsButton = page.getByRole('button', { name: /View Results/i });
    if (await viewResultsButton.isVisible()) {
      await viewResultsButton.click();
    }

    // Wait for PartialResults to render
    await expect(page.locator('.partial-results-container')).toBeVisible();

    // 4. Verify upgrade banner text is visible (but no button)
    await expect(page.getByText(/upgrade/i)).toBeVisible();
    const upgradeButton = page.getByRole('button', { name: 'Upgrade to Unlock Now' });
    await expect(upgradeButton).not.toBeVisible();

    // 5. Verify Credits pricing table is visible inline
    await expect(page.locator('.inline-pricing-container')).toBeVisible();
    await expect(page.getByText('100 Credits', { exact: true })).toBeVisible();
    await expect(page.getByText('For occasional users.')).toBeVisible();
    await expect(page.getByText('500 Credits', { exact: true })).toBeVisible();
    await expect(page.getByText('2000 Credits', { exact: true })).toBeVisible();

    // 6. Click Buy (100 credits) - find button within the card containing "100 Credits"
    const credits100Card = page.locator('h3:has-text("100 Credits")').locator('..');
    await credits100Card.getByRole('button').click();

    // 7. Expect Redirect to Success
    await page.waitForURL('**/success?**');

    // 8. Verify Success Page
    const url = page.url();
    const token = new URL(url).searchParams.get('token');
    expect(token).toBeTruthy();

    // Manually grant credits to simulate webhook
    await grantCredits(request, token, 100);

    await expect(page.getByText('Payment Successful')).toBeVisible();
    await expect(page.getByText('100 Citation Credits')).toBeVisible();
  });

  test('Variant 2.1 (Passes Button) - Regression Test', async ({ page, request }) => {
    // 1. Force Variant 2.1 (Passes + Button)
    await page.goto('http://localhost:5173/');
    await page.evaluate(() => {
      localStorage.setItem('experiment_v1', '2.1');
    });
    await page.reload();

    // 2. Submit 6 citations to trigger limit
    const citations = Array(6).fill('Smith, J. (2020). Test citation.').join('\n\n');
    await page.fill('.ProseMirror', citations);
    await page.click('button[type="submit"]');

    // Wait for validation results section to appear
    await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 30000 });

    // Wait for PartialResults to render
    await expect(page.locator('.partial-results-container')).toBeVisible();
    const upgradeButton = page.getByRole('button', { name: 'Upgrade to Unlock Now' });
    await expect(upgradeButton).toBeVisible();

    // 3. Verify pricing table is NOT visible yet (button variant)
    await expect(page.locator('.inline-pricing-container')).not.toBeVisible();

    // 4. Open Upgrade Modal
    await upgradeButton.click();

    // 5. Verify Pricing Modal (Passes)
    await expect(page.locator('.upgrade-modal-container')).toBeVisible();
    await expect(page.getByText('7-Day Pass', { exact: true })).toBeVisible();
    await expect(page.getByText('Unlimited validations for 7 days')).toBeVisible();

    // 6. Click Buy (7-day pass) - find button within the card containing "7-Day Pass"
    const pass7DayCard = page.locator('h3:has-text("7-Day Pass")').locator('..');
    await pass7DayCard.getByRole('button').click();

    // 7. Expect Redirect to Success
    await page.waitForURL('**/success?**');

    // 8. Verify Success
    const url = page.url();
    const token = new URL(url).searchParams.get('token');
    expect(token).toBeTruthy();

    // Manually grant pass
    await grantPass(request, token, 7);

    await expect(page.getByText('Payment Successful')).toBeVisible();
  });

  test('Variant 2.2 (Passes Inline)', async ({ page, request }) => {
    // 1. Force Variant 2.2 (Passes + Inline)
    await page.goto('http://localhost:5173/');
    await page.evaluate(() => {
      localStorage.setItem('experiment_v1', '2.2');
    });
    await page.reload();

    // 2. Submit 6 citations to trigger limit
    const citations = Array(6).fill('Smith, J. (2020). Test citation.').join('\n\n');
    await page.fill('.ProseMirror', citations);
    await page.click('button[type="submit"]');

    // 3. Wait for validation results section to appear
    await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 30000 });

    // Check if results are gated and click through if necessary
    if (await viewResultsButton.isVisible()) {
      await viewResultsButton.click();
    }

    // Wait for PartialResults to render
    await expect(page.locator('.partial-results-container')).toBeVisible();

    // 4. Verify upgrade banner text is visible (but no button)
    await expect(page.getByText(/upgrade/i)).toBeVisible();
    const upgradeButton = page.getByRole('button', { name: 'Upgrade to Unlock Now' });
    await expect(upgradeButton).not.toBeVisible();

    // 5. Verify Passes pricing table is visible inline
    await expect(page.locator('.inline-pricing-container')).toBeVisible();
    await expect(page.getByText('1-Day Pass', { exact: true })).toBeVisible();
    await expect(page.getByText('Unlimited validations for 24 hours')).toBeVisible();
    await expect(page.getByText('7-Day Pass', { exact: true })).toBeVisible();
    await expect(page.getByText('30-Day Pass', { exact: true })).toBeVisible();

    // 6. Click Buy (7-day pass) - find button within the card containing "7-Day Pass"
    const pass7DayCard = page.locator('h3:has-text("7-Day Pass")').locator('..');
    await pass7DayCard.getByRole('button').click();

    // 7. Expect Redirect to Success
    await page.waitForURL('**/success?**');

    // 8. Verify Success
    const url = page.url();
    const token = new URL(url).searchParams.get('token');
    expect(token).toBeTruthy();

    // Manually grant pass
    await grantPass(request, token, 7);

    await expect(page.getByText('Payment Successful')).toBeVisible();
  });

  // Legacy tests for backward compatibility
  test('Legacy Variant 1 (Credits) - Should migrate to 4-variant scheme', async ({ page, request }) => {
    // 1. Force old Variant 1 format
    await page.goto('http://localhost:5173/');
    await page.evaluate(() => {
      localStorage.setItem('experiment_v1', '1');
    });
    await page.reload();

    // 2. Submit 6 citations to hit free limit
    const citations = Array(6).fill('Smith, J. (2020). Test citation.').join('\n\n');
    await page.fill('.ProseMirror', citations);
    await page.click('button[type="submit"]');

    // Wait for validation results section to appear
    await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 30000 });

    // Wait for PartialResults to render - should be one of the 4 variants now
    await expect(page.locator('.partial-results-container')).toBeVisible();

    // 3. Check that we have a valid 4-variant assignment
    const variant = await page.evaluate(() => localStorage.getItem('experiment_v1'));
    expect(['1.1', '1.2', '2.1', '2.2']).toContain(variant);
  });

  test('Legacy Variant 2 (Passes) - Should migrate to 4-variant scheme', async ({ page, request }) => {
    // 1. Force old Variant 2 format
    await page.goto('http://localhost:5173/');
    await page.evaluate(() => {
      localStorage.setItem('experiment_v1', '2');
    });
    await page.reload();

    // 2. Submit 6 citations to trigger limit
    const citations = Array(6).fill('Smith, J. (2020). Test citation.').join('\n\n');
    await page.fill('.ProseMirror', citations);
    await page.click('button[type="submit"]');

    // Wait for validation results section to appear
    await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 30000 });

    // Wait for PartialResults to render - should be one of the 4 variants now
    await expect(page.locator('.partial-results-container')).toBeVisible();

    // 3. Check that we have a valid 4-variant assignment
    const variant = await page.evaluate(() => localStorage.getItem('experiment_v1'));
    expect(['1.1', '1.2', '2.1', '2.2']).toContain(variant);
  });

});
