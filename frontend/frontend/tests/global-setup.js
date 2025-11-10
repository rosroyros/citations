/**
 * Global setup for Playwright tests
 */

async function globalSetup(config) {
  console.log('🚀 Setting up Playwright test environment...');

  // Any global setup can go here
  // For example: starting services, cleaning up test data, etc.

  console.log('✅ Playwright test environment ready');
}

export default globalSetup;