import { test, expect } from '@playwright/test';

test.describe('Pricing Integration Tests', () => {
  let userId;
  let checkoutId;

  test.beforeEach(async ({ page }) => {
    // Set up base URL to localhost
    await page.goto('http://localhost:5173');
    await waitForPageLoad(page);

    // Get or create user ID
    userId = await page.evaluate(() => {
      let uid = localStorage.getItem('userId');
      if (!uid) {
        uid = 'test_user_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('userId', uid);
      }
      return uid;
    });

    // Intercept Polar checkout redirect to prevent navigation
    await page.route('https://polar.sh/**', (route) => {
      route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/html' },
        body: '<html><body><h1>Mock Checkout Page</h1></body></html>'
      });
    });
  });

  test('complete credits purchase and usage through UI', async ({ page }) => {
    // 1. Exhaust free tier (5 validations)
    for (let i = 1; i <= 6; i++) {
      await page.fill('.ProseMirror', `Citation ${i}: Smith, J. (2023). Test citation ${i}. Journal of Testing.`);
      await page.click('button:has-text("Check My Citations")');

      // Wait for processing
      await page.waitForTimeout(3000);

      if (i <= 5) {
        // Should see results section (might be gated)
        await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 5000 });

        // If gated results overlay is present, click reveal button
        if (await page.locator('[data-testid="gated-results"]').isVisible()) {
          await page.click('button:has-text("View Results")');
          // Wait for reveal to complete
          await page.waitForTimeout(1000);
        }
      }
    }

    // 2. Should see partial results with upgrade button on 6th validation
    await expect(page.locator('[data-testid="partial-results"]')).toBeVisible({ timeout: 5000 });
    await expect(page.locator('button:has-text("Upgrade to Continue")')).toBeVisible();

    // 3. Force variant '1' (Credits) before modal opens
    await page.evaluate(() => {
      localStorage.setItem('experiment_v1', '1');
      console.log('Set localStorage experiment_v1 to:', localStorage.getItem('experiment_v1'));
    });

    // 4. Click upgrade button to show pricing modal
    await page.click('button:has-text("Upgrade to Continue")');
    await expect(page.locator('.pricing-modal')).toBeVisible({ timeout: 5000 });

    // 5. Verify correct variant shown
    const variant = await page.locator('.pricing-table').getAttribute('data-variant');
    console.log('Variant found:', variant);
    expect(['credits', 'passes']).toContain(variant);

    // 6. Select product based on variant
    if (variant === 'credits') {
      await page.click('button:has-text("Buy 500 Credits")');
    } else {
      await page.click('button:has-text("Buy 7-Day Pass")');
    }

    // 6. Wait for navigation to success page
    await page.waitForURL('**/success?token=*&mock=true');

    // 7. Get the token from URL and save it to localStorage
    const url = new URL(page.url());
    const token = url.searchParams.get('token');
    await page.evaluate((token) => {
      localStorage.setItem('citation_checker_token', token);
      console.log('Updated localStorage citation_checker_token to:', token);
    }, token);

    // 8. Navigate back to app to update user status
    await page.goto('http://localhost:5173');
    await waitForPageLoad(page);

    // 9. Reload page to ensure token is read correctly
    await page.reload();
    await waitForPageLoad(page);

    // 10. Wait for credits to be reflected (background webhook runs after delay)
    await page.waitForTimeout(3000);

    // 10. Verify user status updated
    if (variant === 'credits') {
      await expect(page.locator('.credit-display')).toContainText('Citation Credits: 500', { timeout: 5000 });
    } else {
      await expect(page.locator('.credit-display')).toContainText('0/1000', { timeout: 5000 });
    }

    // 10. Submit another validation
    await page.fill('.ProseMirror', 'Paid citation: Wilson, K. (2023). Paid validation. Academic Journal.');
    await page.click('button:has-text("Check My Citations")');
    await page.waitForTimeout(2000);

    // 11. Verify usage updated
    await page.reload();
    await waitForPageLoad(page);

    if (variant === 'credits') {
      await expect(page.locator('.credit-display')).toContainText('Citation Credits: 499');
    } else {
      await expect(page.locator('.credit-display')).toContainText('1/1000');
    }
  });

  test('pass daily limit enforcement', async ({ page }) => {
    // 1. Set daily usage to 999 via test helper
    await page.evaluate(async (userId) => {
      const response = await fetch('http://localhost:8000/test/set-daily-usage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          usage: 999
        })
      });
      return response.json();
    }, userId);

    // 2. Grant pass via test helper
    await page.evaluate(async (userId) => {
      const response = await fetch('http://localhost:8000/test/grant-pass', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          days: 7
        })
      });
      return response.json();
    }, userId);

    // Save the userId to citation_checker_token for the frontend to read
    await page.evaluate((userId) => {
      localStorage.setItem('citation_checker_token', userId);
      console.log('Updated localStorage citation_checker_token to:', userId);
    }, userId);

    // 4. Reload to see updated status
    await page.reload();
    await waitForPageLoad(page);

    // 5. Make a small validation to trigger UserStatus rendering (should show 999/1000)
    await page.fill('.ProseMirror', 'Citation 999: Before limit');
    await page.click('button:has-text("Check My Citations")');

    // Wait for validation to complete and results to appear
    await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 10000 });

    // Wait a moment for UserStatus to be updated after validation
    await page.waitForTimeout(1000);

    // If gated results overlay is present, click reveal button
    if (await page.locator('[data-testid="gated-results"]').isVisible()) {
      await page.click('button:has-text("View Results")');
      await page.waitForTimeout(1000);
    }

    // Debug: Check if UserStatus element exists
    const userStatusExists = await page.locator('.user-status').count();
    console.log(`UserStatus element count: ${userStatusExists}`);

    // Debug: Check entire header status content
    const headerStatusContent = await page.locator('.header-status').textContent();
    console.log(`Header status content: ${headerStatusContent}`);

    // Should show 999/1000
    await expect(page.locator('.user-status')).toContainText('999/1000 used today', { timeout: 5000 });

    // 6. 1000th validation should succeed
    await page.fill('.ProseMirror', 'Citation 1000: Test at limit');
    await page.click('button:has-text("Check My Citations")');
    await expect(page.locator('.validation-results-section')).toBeVisible();

  // If gated results overlay is present, click reveal button
  if (await page.locator('[data-testid="gated-results"]').isVisible()) {
    await page.click('button:has-text("View Results")');
    await page.waitForTimeout(1000);
  }

    // 7. Should show 1000/1000 (user-status only appears after validation)
    await expect(page.locator('.user-status')).toContainText('1000/1000 used today');

    // 8. 1001st validation should fail
    await page.fill('.ProseMirror', 'Citation 1001: Over limit');
    await page.click('button:has-text("Check My Citations")');

    // 9. Error message should appear
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Daily limit (1000) reached');
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Resets in');
  });

  test('pass priority over credits', async ({ page }) => {
    // 1. Grant both credits AND pass
    await page.evaluate(async (userId) => {
      // Grant credits
      await fetch('http://localhost:8000/test/grant-credits', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          amount: 500
        })
      });

      // Grant pass
      await fetch('http://localhost:8000/test/grant-pass', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          days: 7
        })
      });
    }, userId);

    // Save the userId to citation_checker_token for the frontend to read
    await page.evaluate((userId) => {
      localStorage.setItem('citation_checker_token', userId);
      console.log('Updated localStorage citation_checker_token to:', userId);
    }, userId);

    // Wait for DB consistency (SQLite WAL mode in CI environment)
    await page.waitForTimeout(1000);

    // 2. Reload to update status
    await page.reload();
    await waitForPageLoad(page);

    // 3. Should show PASS (not credits)
    await expect(page.locator('.credit-display')).toContainText('7-Day Pass Active');
    await expect(page.locator('.credit-display')).not.toContainText('Citation Credits: 500');

    // 4. Submit validation
    await page.fill('.ProseMirror', 'Priority test: Which is used?');
    await page.click('button:has-text("Check My Citations")');
    await page.waitForTimeout(2000);

    // 5. Reload to check usage
    await page.reload();

    // 6. Pass usage should increment (NOT credits)
    await expect(page.locator('.user-status')).toContainText('1/1000 used today');

    // 7. Verify credits unchanged
    const credits = await page.evaluate(async (userId) => {
      const response = await fetch(`http://localhost:8000/test/get-user?user_id=${userId}`);
      const user = await response.json();
      return user.credits;
    }, userId);

    expect(credits).toBe(500); // Unchanged!
  });

  test('variant assignment persistence', async ({ page }) => {
    // 1. Trigger paywall to see variant
    for (let i = 1; i <= 6; i++) {
      await page.fill('.ProseMirror', `Variant test ${i}: Test citation`);
      await page.click('button:has-text("Check My Citations")');
      await page.waitForTimeout(1000);
    }

    // 2. Click upgrade button to show pricing modal
    await expect(page.locator('button:has-text("Upgrade to Continue")')).toBeVisible();
    await page.click('button:has-text("Upgrade to Continue")');
    await expect(page.locator('.pricing-modal')).toBeVisible();

    // 3. Get initial variant
    const variant1 = await page.locator('.pricing-table').getAttribute('data-variant');

    // 4. Close modal
    await page.click('[data-testid="close-modal"]');

    // 5. Clear cookies (localStorage persists in same context)
    await page.context().clearCookies();

    // 6. Trigger paywall again
    for (let i = 7; i <= 12; i++) {
      await page.fill('.ProseMirror', `Variant test ${i}: Test citation`);
      await page.click('button:has-text("Check My Citations")');
      await page.waitForTimeout(1000);
    }

    // 7. Click upgrade button to show pricing modal again
    await expect(page.locator('button:has-text("Upgrade to Continue")')).toBeVisible();
    await page.click('button:has-text("Upgrade to Continue")');
    await expect(page.locator('.pricing-modal')).toBeVisible();

    // 8. Should be SAME variant
    const variant2 = await page.locator('.pricing-table').getAttribute('data-variant');
    expect(variant2).toBe(variant1);
  });

  test('tracking events fire throughout user journey', async ({ page }) => {
    // 1. Make a validation request first to trigger free user ID generation
    await page.fill('.ProseMirror', 'Initial validation to trigger user ID generation');
    await page.click('button:has-text("Check My Citations")');
    await page.waitForTimeout(1000);

    // 2. Get the actual free user ID that the frontend generates and clear events for it
    // The app stores the free user ID in localStorage under the key 'citation_checker_free_user_id'
    const freeUserId = await page.evaluate(() => {
      return localStorage.getItem('citation_checker_free_user_id');
    });

    // Use the freeUserId for clearing/retrieving events, fallback to userId for compatibility
    const trackingUserId = freeUserId || userId;

    await page.evaluate(async (trackingUserId) => {
      await fetch('http://localhost:8000/test/clear-events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: trackingUserId })
      });
    }, trackingUserId);

    // 3. Exhaust free tier to trigger pricing modal
    for (let i = 1; i <= 6; i++) {
      await page.fill('.ProseMirror', `Tracking test ${i}: Test citation`);
      await page.click('button:has-text("Check My Citations")');
      await page.waitForTimeout(1000);
    }

    // 3. Click upgrade button to show pricing modal
    await expect(page.locator('button:has-text("Upgrade to Continue")')).toBeVisible();
    await page.click('button:has-text("Upgrade to Continue")');
    await expect(page.locator('.pricing-modal')).toBeVisible();
    await page.waitForTimeout(1000); // Wait for tracking

    // 4. Verify pricing_table_shown event
    let events = await page.evaluate(async (trackingUserId) => {
      const response = await fetch(`http://localhost:8000/test/get-events?user_id=${trackingUserId}`);
      return response.json();
    }, trackingUserId);

    expect(events.some(e => e.event_type === 'pricing_table_shown')).toBe(true);

    // 5. Start checkout
    const variant = await page.locator('.pricing-table').getAttribute('data-variant');
    if (variant === 'credits') {
      await page.click('button:has-text("Buy 500 Credits")');
    } else {
      await page.click('button:has-text("Buy 7-Day Pass")');
    }
    await page.waitForTimeout(1000);

    // 6. Verify checkout_started event
    events = await page.evaluate(async (trackingUserId) => {
      const response = await fetch(`http://localhost:8000/test/get-events?user_id=${trackingUserId}`);
      return response.json();
    }, trackingUserId);

    expect(events.some(e => e.event_type === 'checkout_started')).toBe(true);

    // 7. Complete purchase via webhook
    const productId = variant === 'credits' ? 'prod_credits_500' : 'prod_pass_7day';
    await page.evaluate(async ({ productId, checkoutId, trackingUserId, variant }) => {
      await fetch('http://127.0.0.1:8000/webhook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type: 'checkout.completed',
          checkout_id: checkoutId,
          product_id: productId,
          amount: variant === 'credits' ? 500 : 1000,
          metadata: {
            user_id: trackingUserId
          }
        })
      });
    }, { productId, checkoutId, trackingUserId, variant });

    await page.waitForTimeout(1000);

    // 8. Verify purchase_completed event
    events = await page.evaluate(async (trackingUserId) => {
      const response = await fetch(`http://localhost:8000/test/get-events?user_id=${trackingUserId}`);
      return response.json();
    }, trackingUserId);

    expect(events.some(e => e.event_type === 'purchase_completed')).toBe(true);
  });
});

// Helper function for waiting for page load
async function waitForPageLoad(page) {
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000); // Additional wait for React to render
}