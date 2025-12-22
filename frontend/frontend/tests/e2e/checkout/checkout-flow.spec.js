import { test, expect } from '@playwright/test';

test.describe('Checkout Flow E2E', () => {
  test.use({ baseURL: 'http://localhost:5173' });

  test.beforeEach(async ({ page }) => {
    // Clear cookies and localStorage before each test
    await page.context().clearCookies();
    await page.addInitScript(() => {
      localStorage.clear();

      // Mock the Polar Embed SDK
      // The actual SDK is dynamically imported, so we need to mock at window level
      window.__polarCheckoutHandlers = {};
      window.__polarCheckoutCreated = false;
      window.__polarCheckoutUrl = null;
      window.__polarCheckoutClosed = false;

      window.PolarEmbedCheckout = {
        create: async (url, options) => {
          window.__polarCheckoutCreated = true;
          window.__polarCheckoutUrl = url;
          return {
            // The real SDK uses addEventListener, not on()
            addEventListener: (event, handler) => {
              window.__polarCheckoutHandlers[event] = handler;
            },
            // Support legacy on() for any code that might use it
            on: (event, handler) => {
              window.__polarCheckoutHandlers[event] = handler;
            },
            // The close() method is called after success
            close: () => {
              window.__polarCheckoutClosed = true;
            }
          };
        }
      };
    });
  });

  // Helper to trigger mock checkout success
  async function triggerCheckoutSuccess(page) {
    await page.evaluate(() => {
      if (window.__polarCheckoutHandlers?.success) {
        window.__polarCheckoutHandlers.success();
      }
    });
  }

  // Helper to trigger mock checkout close (abandonment)
  async function triggerCheckoutClose(page) {
    await page.evaluate(() => {
      if (window.__polarCheckoutHandlers?.close) {
        window.__polarCheckoutHandlers.close();
      }
    });
  }

  // Helper to check if embed checkout was created
  async function wasEmbedCheckoutCreated(page) {
    return await page.evaluate(() => window.__polarCheckoutCreated);
  }

  test.describe('Variant 1 - Credits Purchase Flow', () => {
    // Skip on Firefox - console event timing is flaky
    test.skip(({ browserName }) => browserName === 'firefox', 'Firefox console timing flaky');

    test('complete purchase flow for 500 credits', async ({ page }) => {
      // Set up console event listeners before navigation
      const consoleMessages = [];
      page.on('console', msg => {
        consoleMessages.push({
          type: msg.type(),
          text: msg.text()
        });
      });

      // Mock the checkout API to return a success response
      await page.route('/api/create-checkout', async (route) => {
        const postData = await route.request().postDataJSON();

        // Verify the request contains correct data
        expect(postData.productId).toBe('2a3c8913-2e82-4f12-9eb7-767e4bc98089'); // 500 credits product ID
        expect(postData.variantId).toBe('1');

        // Return mock checkout URL
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            checkout_url: 'https://checkout.polar.sh/test-checkout-credits'
          })
        });
      });

      // Navigate to credits pricing page
      await page.goto('/test-pricing-table');
      await expect(page.getByText('100 Credits').first()).toBeVisible();
      await expect(page.getByText('500 Credits').first()).toBeVisible();
      await expect(page.getByText('2,000 Credits').first()).toBeVisible();

      // Wait for pricing_table_shown console event using polling
      await expect.poll(
        () => consoleMessages.filter(msg => msg.text.includes('pricing_table_shown')).length,
        { timeout: 5000 }
      ).toBeGreaterThan(0);

      const pricingTableShownEvents = consoleMessages.filter(msg =>
        msg.text.includes('pricing_table_shown')
      );

      // Check the last logged event for correctness
      const lastEvent = pricingTableShownEvents[pricingTableShownEvents.length - 1];
      expect(lastEvent.text).toContain('pricing_table_shown');

      // Click on 500 credits (recommended tier)
      const buy500Button = page.getByRole('button', { name: 'Buy 500 Credits' });
      await expect(buy500Button).toBeVisible();

      // Set up request promise before clicking
      const requestPromise = page.waitForRequest(request =>
        request.url().includes('/api/create-checkout') && request.method() === 'POST'
      );

      // Click the button
      await buy500Button.click();

      // Wait for and verify the actual request
      const request = await requestPromise;
      const postData = JSON.parse(request.postData());

      // Verify the request contains correct data
      expect(postData.productId).toBe('2a3c8913-2e82-4f12-9eb7-767e4bc98089');
      expect(postData.variantId).toBe('1');

      // Wait for embed checkout to be created using polling
      await expect.poll(() => wasEmbedCheckoutCreated(page), { timeout: 5000 }).toBe(true);

      // Verify checkout_embed_opened event was logged
      expect(consoleMessages.some(msg =>
        msg.text.includes('checkout_embed_opened')
      )).toBeTruthy();

      // Trigger mock success event
      await triggerCheckoutSuccess(page);

      // Wait for checkout to be closed after success
      await expect.poll(() => page.evaluate(() => window.__polarCheckoutClosed), { timeout: 5000 }).toBe(true);

      // Verify checkout_completed event was logged
      expect(consoleMessages.some(msg =>
        msg.text.includes('checkout_completed') &&
        msg.text.includes(postData.productId)
      )).toBeTruthy();

      // Test verifies embedded checkout flow works without redirect
    });
  });

  test.describe('Variant 2 - Passes Purchase Flow', () => {
    // Skip on Firefox - console event timing is flaky
    test.skip(({ browserName }) => browserName === 'firefox', 'Firefox console timing flaky');

    test('complete purchase flow for 7-day pass', async ({ page }) => {
      // Set up console event listeners before navigation
      const consoleMessages = [];
      page.on('console', msg => {
        consoleMessages.push({
          type: msg.type(),
          text: msg.text()
        });
      });

      // Mock the checkout API
      await page.route('/api/create-checkout', async (route) => {
        const postData = await route.request().postDataJSON();

        // Verify the request contains correct data
        expect(postData.productId).toBe('5b311653-7127-41b5-aed6-496fb713149c'); // 7-day pass product ID
        expect(postData.variantId).toBe('2');

        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            checkout_url: 'https://checkout.polar.sh/test-checkout-pass'
          })
        });
      });

      // Navigate to passes pricing page
      await page.goto('/test-pricing-table-passes');
      await expect(page.getByText('1-Day Pass').first()).toBeVisible();
      await expect(page.getByText('7-Day Pass').first()).toBeVisible();
      await expect(page.getByText('30-Day Pass').first()).toBeVisible();

      // Wait for pricing_table_shown console event using polling
      await expect.poll(
        () => consoleMessages.filter(msg => msg.text.includes('pricing_table_shown')).length,
        { timeout: 5000 }
      ).toBeGreaterThan(0);

      const pricingTableShownEvents = consoleMessages.filter(msg =>
        msg.text.includes('pricing_table_shown')
      );

      const lastEvent = pricingTableShownEvents[pricingTableShownEvents.length - 1];
      expect(lastEvent.text).toContain('pricing_table_shown');

      // Click on 7-day pass (recommended tier)
      const buy7DayButton = page.getByRole('button', { name: 'Buy 7-Day Pass' });
      await expect(buy7DayButton).toBeVisible();

      // Set up request promise before clicking
      const requestPromise = page.waitForRequest(request =>
        request.url().includes('/api/create-checkout') && request.method() === 'POST'
      );

      await buy7DayButton.click();

      // Wait for and verify the actual request
      const request = await requestPromise;
      const postData = JSON.parse(request.postData());

      // Verify the request contains correct data
      expect(postData.productId).toBe('5b311653-7127-41b5-aed6-496fb713149c');
      expect(postData.variantId).toBe('2');

      // Wait for embed checkout to be created using polling
      await expect.poll(() => wasEmbedCheckoutCreated(page), { timeout: 5000 }).toBe(true);

      // Verify checkout_embed_opened event was logged
      expect(consoleMessages.some(msg =>
        msg.text.includes('checkout_embed_opened')
      )).toBeTruthy();

      // Trigger mock success event
      await triggerCheckoutSuccess(page);

      // Wait for checkout to be closed after success
      await expect.poll(() => page.evaluate(() => window.__polarCheckoutClosed), { timeout: 5000 }).toBe(true);

      // Verify checkout_completed event was logged
      expect(consoleMessages.some(msg =>
        msg.text.includes('checkout_completed') &&
        msg.text.includes(postData.productId)
      )).toBeTruthy();

      // Test verifies embedded checkout flow works without redirect
    });
  });


  test.describe('Error Handling', () => {
    test('handles checkout API failure gracefully', async ({ page }) => {

      // Mock checkout API to return an error
      await page.route('/api/create-checkout', async (route) => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Internal server error' })
        });
      });

      await page.goto('/test-pricing-table');

      const buy100Button = page.getByRole('button', { name: 'Buy 100 Credits' });
      await buy100Button.click();

      // Wait for error message to appear (either from PricingTableCredits or test page)
      // The error could say "Failed to open checkout" or contain the API error
      await expect(
        page.locator('text=/Failed|Error|error/i').first()
      ).toBeVisible({ timeout: 5000 });

      // Verify button is re-enabled after error
      await expect(buy100Button).toBeEnabled();
    });

    test('handles SDK initialization failure gracefully', async ({ page }) => {
      // Override the mock to throw an error
      await page.addInitScript(() => {
        window.PolarEmbedCheckout = {
          create: async () => {
            throw new Error('SDK initialization failed');
          }
        };
      });

      // Mock checkout API to succeed (error happens in SDK)
      await page.route('/api/create-checkout', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            checkout_url: 'https://checkout.polar.sh/test'
          })
        });
      });

      await page.goto('/test-pricing-table');

      const buy100Button = page.getByRole('button', { name: 'Buy 100 Credits' });
      await buy100Button.click();

      // Wait for error message to appear (flexible matching)
      await expect(
        page.locator('text=/Failed|Error|error/i').first()
      ).toBeVisible({ timeout: 5000 });

      // Verify button is re-enabled after error
      await expect(buy100Button).toBeEnabled();
    });
  });

  test.describe('Checkout Abandonment', () => {
    test('handles checkout abandonment (user closes)', async ({ page }) => {
      // Set up console event listeners
      const consoleMessages = [];
      page.on('console', msg => {
        consoleMessages.push({
          type: msg.type(),
          text: msg.text()
        });
      });

      // Mock the checkout API
      await page.route('/api/create-checkout', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            checkout_url: 'https://checkout.polar.sh/test-checkout'
          })
        });
      });

      await page.goto('/test-pricing-table');

      const buy100Button = page.getByRole('button', { name: 'Buy 100 Credits' });
      await buy100Button.click();

      // Wait for embed checkout to be created using polling
      await expect.poll(() => wasEmbedCheckoutCreated(page), { timeout: 5000 }).toBe(true);

      // Trigger close event (user abandonment)
      await triggerCheckoutClose(page);

      // Wait for checkout close event to be handled
      await expect.poll(() => page.evaluate(() => window.__polarCheckoutClosed), { timeout: 5000 }).toBe(true);

      // Verify checkout_abandoned event was logged
      expect(consoleMessages.some(msg =>
        msg.text.includes('checkout_abandoned')
      )).toBeTruthy();

      // Verify button is still functional (can try again)
      await expect(buy100Button).toBeEnabled();
    });
  });
});