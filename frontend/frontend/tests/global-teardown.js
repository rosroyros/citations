/**
 * Global teardown for Playwright tests
 */

async function globalTeardown(config) {
  console.log('🧹 Cleaning up Playwright test environment...');

  // Any global cleanup can go here
  // For example: stopping services, cleaning up test data, etc.

  console.log('✅ Playwright test environment cleaned up');
}

export default globalTeardown;