import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for E2E testing
 * 
 * Test Categories (via file patterns):
 * - database-tests: pricing-integration, pricing_variants (must run serially)
 * - chromium: All other tests (parallel execution)
 * - Ignored: internal/** (VPN-only), e2e-full-flow (production-only)
 * 
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests',

  // Default to parallel execution for most tests
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Default workers (overridden per project)
  workers: process.env.CI ? 2 : 4,

  // Reporter to use. See https://playwright.dev/docs/test-reporters
  reporter: 'list',

  // Shared settings for all the projects below
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: process.env.BASE_URL || 'http://localhost:5173',

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Take screenshot on failure
    screenshot: 'only-on-failure',

    // Record video on failure
    video: 'retain-on-failure',

    // Global timeout for each action
    actionTimeout: 10000,

    // Global timeout for navigation
    navigationTimeout: 30000,
  },

  // Configure projects for smart parallelization
  projects: [
    // Database tests - MUST run serially to avoid SQLite WAL visibility issues
    // These tests use backend /test/* endpoints that write to the database
    {
      name: 'database-tests',
      testMatch: [
        '**/pricing-integration.spec.js',
        '**/pricing_variants.spec.cjs',
      ],
      fullyParallel: false,
      workers: 1,
      use: { ...devices['Desktop Chrome'] },
    },

    // Main test suite - parallel execution on Chromium
    {
      name: 'chromium',
      testIgnore: [
        '**/internal/**',                    // VPN-only dashboard tests
        '**/pricing-integration.spec.js',    // Handled by database-tests
        '**/pricing_variants.spec.cjs',      // Handled by database-tests
        '**/e2e-full-flow.spec.cjs',         // Production-only (run via deploy script)
      ],
      use: { ...devices['Desktop Chrome'] },
    },

    // Cross-browser testing (optional, run explicitly)
    {
      name: 'firefox',
      testIgnore: [
        '**/internal/**',
        '**/pricing-integration.spec.js',
        '**/pricing_variants.spec.cjs',
        '**/e2e-full-flow.spec.cjs',
      ],
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      testIgnore: [
        '**/internal/**',
        '**/pricing-integration.spec.js',
        '**/pricing_variants.spec.cjs',
        '**/e2e-full-flow.spec.cjs',
      ],
      use: { ...devices['Desktop Safari'] },
    },

    // Mobile viewport tests
    {
      name: 'Mobile Chrome',
      testIgnore: [
        '**/internal/**',
        '**/pricing-integration.spec.js',
        '**/pricing_variants.spec.cjs',
        '**/e2e-full-flow.spec.cjs',
      ],
      use: {
        ...devices['Pixel 5'],
        actionTimeout: 15000,
        navigationTimeout: 45000,
      },
      timeout: 120000,
      expect: {
        timeout: 15000,
      },
    },

    {
      name: 'Mobile Safari',
      testIgnore: [
        '**/internal/**',
        '**/pricing-integration.spec.js',
        '**/pricing_variants.spec.cjs',
        '**/e2e-full-flow.spec.cjs',
      ],
      use: {
        ...devices['iPhone 12'],
        actionTimeout: 15000,
        navigationTimeout: 45000,
      },
      timeout: 120000,
      expect: {
        timeout: 15000,
      },
    },
  ],

  // Test timeout
  timeout: 60000,

  // Expect timeout
  expect: {
    timeout: 10000,
  },
});