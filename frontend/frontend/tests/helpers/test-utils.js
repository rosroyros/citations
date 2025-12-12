/**
 * Test utility functions for E2E tests
 */

/**
 * Generate a test token for testing purposes
 * @returns {string} A UUID test token
 */
export function generateTestToken() {
  return 'test-token-' + Math.random().toString(36).substr(2, 9);
}

/**
 * Create a mock webhook payload for testing
 * @param {Object} params - Webhook parameters
 * @returns {Object} Mock webhook payload
 */
export function createMockWebhookPayload(params = {}) {
  const {
    token = generateTestToken(),
    productId = '2a3c8913-2e82-4f12-9eb7-767e4bc98089',
    orderId = 'test-order-' + Math.random().toString(36).substr(2, 9),
    priceAmount = 499,
    status = 'completed'
  } = params;

  return {
    event_type: 'checkout.updated',
    data: {
      status,
      order_id: orderId,
      metadata: { token },
      line_items: [{
        product_id: productId,
        price_amount: priceAmount
      }]
    }
  };
}

/**
 * Wait for a specific console event
 * @param {Page} page - Playwright page instance
 * @param {string} eventType - Type of event to wait for
 * @param {number} timeout - Timeout in milliseconds
 * @returns {Promise<Object>} The console event
 */
export async function waitForConsoleEvent(page, eventType, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const timeoutId = setTimeout(() => {
      reject(new Error(`Timeout waiting for console event: ${eventType}`));
    }, timeout);

    page.on('console', msg => {
      if (msg.text().includes(eventType)) {
        clearTimeout(timeoutId);
        resolve({
          type: msg.type(),
          text: msg.text()
        });
      }
    });
  });
}

/**
 * Extract token from a checkout URL
 * @param {string} checkoutUrl - The checkout URL
 * @returns {string|null} The extracted token
 */
export function extractTokenFromCheckoutUrl(checkoutUrl) {
  const match = checkoutUrl.match(/token=([^&]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}