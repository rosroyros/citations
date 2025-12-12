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

    // Mock LLM validation responses to avoid calling real APIs
    await page.route('**/api/validate/async', async (route) => {
      const request = route.request();
      const postData = JSON.parse(request.postData());

      // Check user's current usage by checking headers
      route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: `test_job_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
          status: 'processing'
        })
      });
    });

    // Mock job polling endpoint
    await page.route('**/api/jobs/**', async (route) => {
      const url = route.request().url();

      // Simulate paywall after 5 validations
      // In real test, we'd track usage, but for simplicity we'll check if this is the 6th job
      if (url.includes('job_6')) {
        // Return partial results to trigger paywall
        route.fulfill({
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            status: 'completed',
            results: [
              {
                text: 'Test citation',
                is_valid: false,
                errors: ['Test error for paywall'],
                suggestions: ['Test suggestion']
              }
            ],
            partial: true,
            usage: {
              remaining: 0,
              limit: 5
            }
          })
        });
      } else {
        // Return full results for first 5 validations
        route.fulfill({
          status: 200,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            status: 'completed',
            results: [
              {
                text: 'Test citation',
                is_valid: true,
                errors: [],
                suggestions: []
              }
            ],
            partial: false,
            usage: {
              remaining: 5 - parseInt(url.match(/job_(\d+)/)?.[1] || '1'),
              limit: 5
            }
          })
        });
      }
    });

    // Mock Polar checkout redirect
    await page.route('**/api/checkout/create', async (route) => {
      checkoutId = `ch_test_${Date.now()}`;
      route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          checkout_id: checkoutId,
          url: `https://polar.sh/checkout/${checkoutId}`
        })
      });
    });
  });

  test('complete credits purchase and usage through UI', async ({ page }) => {
    // 1. Exhaust free tier (5 validations)
    for (let i = 1; i <= 6; i++) {
      await page.fill('[contenteditable="true"]', `Citation ${i}: Smith, J. (2023). Test citation ${i}. Journal of Testing.`);
      await page.click('button:has-text("Check My Citations")');

      // Wait for processing
      await page.waitForTimeout(2000);

      if (i <= 5) {
        // Should see results
        await expect(page.locator('.validation-results')).toBeVisible({ timeout: 5000 });
      }
    }

    // 2. Pricing modal should appear on 6th validation
    await expect(page.locator('.pricing-modal')).toBeVisible({ timeout: 5000 });

    // 3. Verify correct variant shown
    const variant = await page.locator('.pricing-table').getAttribute('data-variant');
    expect(['credits', 'passes']).toContain(variant);

    // 4. Select product based on variant
    if (variant === 'credits') {
      await page.click('[data-testid="credits-500"]');
    } else {
      await page.click('[data-testid="pass-7day"]');
    }

    // 5. Click checkout button
    await page.click('[data-testid="checkout-button"]');

    // 6. Simulate successful webhook
    const productId = variant === 'credits' ? 'prod_credits_500' : 'prod_pass_7day';

    // Call webhook directly (bypassing frontend)
    await page.evaluate(async ({ productId, checkoutId, userId }) => {
      const response = await fetch('http://localhost:8002/webhook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type: 'checkout.completed',
          checkout_id: checkoutId,
          product_id: productId,
          customer_email: 'test@example.com',
          amount: variant === 'credits' ? 500 : 1000,
          metadata: {
            user_id: userId
          }
        })
      });
      return response.json();
    }, { productId, checkoutId, userId });

    // 7. Reload page to update user status
    await page.reload();
    await waitForPageLoad(page);

    // 8. Verify user status updated
    if (variant === 'credits') {
      await expect(page.locator('[data-testid="user-status"]')).toContainText('500 credits', { timeout: 5000 });
    } else {
      await expect(page.locator('[data-testid="user-status"]')).toContainText('0/1000', { timeout: 5000 });
    }

    // 9. Submit another validation
    await page.fill('[contenteditable="true"]', 'Paid citation: Wilson, K. (2023). Paid validation. Academic Journal.');
    await page.click('button:has-text("Check My Citations")');
    await page.waitForTimeout(2000);

    // 10. Verify usage updated
    await page.reload();

    if (variant === 'credits') {
      await expect(page.locator('[data-testid="user-status"]')).toContainText('499 credits');
    } else {
      await expect(page.locator('[data-testid="user-status"]')).toContainText('1/1000');
    }
  });

  test('pass daily limit enforcement', async ({ page }) => {
    // 1. Grant pass via test helper
    await page.evaluate(async (userId) => {
      const response = await fetch('http://localhost:8002/test/grant-pass', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          days: 7
        })
      });
      return response.json();
    }, userId);

    // 2. Set daily usage to 999
    await page.evaluate(async (userId) => {
      const response = await fetch('http://localhost:8002/test/set-daily-usage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          usage: 999
        })
      });
      return response.json();
    }, userId);

    // 3. Reload to see updated status
    await page.reload();
    await waitForPageLoad(page);

    // 4. Should show 999/1000
    await expect(page.locator('[data-testid="user-status"]')).toContainText('999/1000');

    // 5. 1000th validation should succeed
    await page.fill('[contenteditable="true"]', 'Citation 1000: Test at limit');
    await page.click('button:has-text("Check My Citations")');
    await expect(page.locator('.validation-results')).toBeVisible();

    // 6. Should show 1000/1000
    await expect(page.locator('[data-testid="user-status"]')).toContainText('1000/1000');

    // 7. 1001st validation should fail
    await page.fill('[contenteditable="true"]', 'Citation 1001: Over limit');
    await page.click('button:has-text("Check My Citations")');

    // 8. Error message should appear
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Daily limit (1000) reached');
    await expect(page.locator('[data-testid="error-message"]')).toContainText('Resets in');
  });

  test('pass priority over credits', async ({ page }) => {
    // 1. Grant both credits AND pass
    await page.evaluate(async (userId) => {
      // Grant credits
      await fetch('http://localhost:8002/test/grant-credits', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          amount: 500
        })
      });

      // Grant pass
      await fetch('http://localhost:8002/test/grant-pass', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          days: 7
        })
      });
    }, userId);

    // 2. Reload to update status
    await page.reload();
    await waitForPageLoad(page);

    // 3. Should show PASS (not credits)
    await expect(page.locator('[data-testid="user-status"]')).toContainText('0/1000');
    await expect(page.locator('[data-testid="user-status"]')).not.toContainText('500 credits');

    // 4. Submit validation
    await page.fill('[contenteditable="true"]', 'Priority test: Which is used?');
    await page.click('button:has-text("Check My Citations")');
    await page.waitForTimeout(2000);

    // 5. Reload to check usage
    await page.reload();

    // 6. Pass usage should increment (NOT credits)
    await expect(page.locator('[data-testid="user-status"]')).toContainText('1/1000');

    // 7. Verify credits unchanged
    const credits = await page.evaluate(async (userId) => {
      const response = await fetch(`http://localhost:8002/test/get-user?user_id=${userId}`);
      const user = await response.json();
      return user.credits;
    }, userId);

    expect(credits).toBe(500); // Unchanged!
  });

  test('variant assignment persistence', async ({ page }) => {
    // 1. Trigger paywall to see variant
    for (let i = 1; i <= 6; i++) {
      await page.fill('[contenteditable="true"]', `Variant test ${i}: Test citation`);
      await page.click('button:has-text("Check My Citations")');
      await page.waitForTimeout(1000);
    }

    // 2. Pricing modal should appear
    await expect(page.locator('.pricing-modal')).toBeVisible();

    // 3. Get initial variant
    const variant1 = await page.locator('.pricing-table').getAttribute('data-variant');

    // 4. Close modal
    await page.click('[data-testid="close-modal"]');

    // 5. Clear cookies (localStorage persists in same context)
    await page.context().clearCookies();

    // 6. Trigger paywall again
    for (let i = 7; i <= 12; i++) {
      await page.fill('[contenteditable="true"]', `Variant test ${i}: Test citation`);
      await page.click('button:has-text("Check My Citations")');
      await page.waitForTimeout(1000);
    }

    // 7. Should be SAME variant
    const variant2 = await page.locator('.pricing-table').getAttribute('data-variant');
    expect(variant2).toBe(variant1);
  });

  test('tracking events fire throughout user journey', async ({ page }) => {
    // 1. Clear tracking events
    await page.evaluate(async (userId) => {
      await fetch('http://localhost:8002/test/clear-events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId })
      });
    }, userId);

    // 2. Exhaust free tier to trigger pricing modal
    for (let i = 1; i <= 6; i++) {
      await page.fill('[contenteditable="true"]', `Tracking test ${i}: Test citation`);
      await page.click('button:has-text("Check My Citations")');
      await page.waitForTimeout(1000);
    }

    // 3. Pricing modal should appear
    await expect(page.locator('.pricing-modal')).toBeVisible();
    await page.waitForTimeout(1000); // Wait for tracking

    // 4. Verify pricing_table_shown event
    let events = await page.evaluate(async (userId) => {
      const response = await fetch(`http://localhost:8002/test/get-events?user_id=${userId}`);
      return response.json();
    }, userId);

    expect(events.some(e => e.event_type === 'pricing_table_shown')).toBe(true);

    // 5. Start checkout
    const variant = await page.locator('.pricing-table').getAttribute('data-variant');
    if (variant === 'credits') {
      await page.click('[data-testid="credits-500"]');
    } else {
      await page.click('[data-testid="pass-7day"]');
    }

    await page.click('[data-testid="checkout-button"]');
    await page.waitForTimeout(1000);

    // 6. Verify checkout_started event
    events = await page.evaluate(async (userId) => {
      const response = await fetch(`http://localhost:8002/test/get-events?user_id=${userId}`);
      return response.json();
    }, userId);

    expect(events.some(e => e.event_type === 'checkout_started')).toBe(true);

    // 7. Complete purchase via webhook
    const productId = variant === 'credits' ? 'prod_credits_500' : 'prod_pass_7day';
    await page.evaluate(async ({ productId, checkoutId, userId }) => {
      await fetch('http://localhost:8002/webhook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type: 'checkout.completed',
          checkout_id: checkoutId,
          product_id: productId,
          amount: variant === 'credits' ? 500 : 1000,
          metadata: {
            user_id: userId
          }
        })
      });
    }, { productId, checkoutId, userId });

    await page.waitForTimeout(1000);

    // 8. Verify purchase_completed event
    events = await page.evaluate(async (userId) => {
      const response = await fetch(`http://localhost:8002/test/get-events?user_id=${userId}`);
      return response.json();
    }, userId);

    expect(events.some(e => e.event_type === 'purchase_completed')).toBe(true);
  });
});

// Helper function for waiting for page load
async function waitForPageLoad(page) {
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000); // Additional wait for React to render
}