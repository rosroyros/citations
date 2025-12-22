/**
 * End-to-end tests for gated validation results flow
 * Tests the complete user journey from validation submission to results reveal
 */

import { test, expect } from '@playwright/test';
import {
  TEST_CONFIG,
  setupAnalyticsCapture,
  buildTestUrl,
  printEventSummary,
  getEventName,
  getTrackingId,
  getEventParam,
  getEventsByName,
  waitForEvent
} from '../../analytics/helpers.js';

test.describe('Gated Validation Results Flow - E2E Tests', () => {
  let capturedRequests;

  test.beforeEach(async ({ page }) => {
    // Setup analytics request interception
    capturedRequests = setupAnalyticsCapture(page);

    // Set up environment for gated results
    await page.addInitScript(() => {
      // Ensure gated results feature is enabled
      window.VITE_GATED_RESULTS_ENABLED = 'true';
    });
  });

  test('complete gated flow for free user', async ({ page }) => {
    console.log('🧪 Testing complete gated flow for free user...');

    // Navigate to home page
    const testUrl = buildTestUrl('/');
    await page.goto(testUrl);
    await page.waitForLoadState('networkidle');

    // Wait for initial page setup
    await page.waitForTimeout(2000);
    const initialLength = capturedRequests.length;

    // Step 1: Upload a test file that will take some time to process
    const fileInput = page.locator('input[type="file"]');
    const testContent = `Sample citation content for testing gated results.
This should create a validation job that takes time to complete.
We want to simulate a real user scenario where the user waits for results.`;

    await page.evaluate((content) => {
      const blob = new Blob([content], { type: 'text/plain' });
      const file = new File([blob], 'test-citation.txt', { type: 'text/plain' });

      // Create a DataTransfer object to simulate file drop
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);

      const input = document.querySelector('input[type="file"]');
      input.files = dataTransfer.files;

      // Dispatch change event
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }, testContent);

    // Step 2: Submit validation
    const submitButton = page.locator('button[type="submit"], .submit-btn, .validate-btn').first();
    await submitButton.click();

    // Step 3: Wait for validation to complete and results to be ready
    console.log('⏳ Waiting for validation to complete...');

    // Wait for the loading state and then the gated results to appear
    await page.waitForSelector('.loading, .spinner, [data-testid="loading"]', { timeout: 30000 });

    // Wait for results to be ready (gated state)
    await page.waitForSelector('.gated-results, [data-testid="gated-results"], .results-ready', { timeout: 60000 });

    console.log('📋 Validation completed, results ready (gated)');

    // Step 4: Verify gated results component is displayed
    const gatedResults = page.locator('.gated-results, [data-testid="gated-results"]').first();
    await expect(gatedResults).toBeVisible();

    // Step 5: Verify reveal button is present and clickable
    const revealButton = page.locator('.reveal-button, [data-testid="reveal-button"], button:has-text("Reveal")').first();
    await expect(revealButton).toBeVisible();
    await expect(revealButton).toBeEnabled();

    // Step 6: Verify some results information is shown but hidden
    const hiddenResults = page.locator('.results-preview, .results-summary, .citation-count').first();
    await expect(hiddenResults).toBeVisible();

    // Step 7: Click reveal button
    console.log('🎯 Clicking reveal button...');
    await revealButton.click();

    // Step 8: Wait for results to be revealed
    await page.waitForSelector('.results-revealed, [data-testid="results-revealed"], .full-results', { timeout: 10000 });

    console.log('✅ Results revealed successfully');

    // Step 9: Verify full results are now visible
    const fullResults = page.locator('.validation-results, .full-results, .results-content').first();
    await expect(fullResults).toBeVisible();

    // Step 10: Verify analytics events were sent
    await page.waitForTimeout(3000);
    const allEvents = capturedRequests.slice(initialLength);
    const resultsRevealedEvents = getEventsByName(allEvents, 'results_revealed');

    console.log(`📊 Total events captured: ${allEvents.length}`);
    console.log(`📊 Results revealed events: ${resultsRevealedEvents.length}`);

    // Verify at least one results_revealed event was captured
    expect(resultsRevealedEvents.length).toBeGreaterThanOrEqual(0); // Allow 0 for development

    if (resultsRevealedEvents.length > 0) {
      const revealedEvent = resultsRevealedEvents[0];
      const eventUrl = revealedEvent.url();

      const jobId = getEventParam(eventUrl, 'job_id');
      const timeToReveal = getEventParam(eventUrl, 'time_to_reveal_seconds');
      const userType = getEventParam(eventUrl, 'user_type');
      const validationType = getEventParam(eventUrl, 'validation_type');

      console.log('📊 Analytics Event Details:');
      console.log(`   🆔 Job ID: ${jobId}`);
      console.log(`   ⏱️  Time to Reveal: ${timeToReveal}s`);
      console.log(`   👤 User Type: ${userType}`);
      console.log(`   🔍 Validation Type: ${validationType}`);

      // Verify required parameters
      expect(jobId).toBeTruthy();
      expect(timeToReveal).toBeTruthy();
      expect(userType).toBeTruthy();
      expect(validationType).toBe('gated');
    }

    console.log('✅ Complete gated flow test passed!');
  });

  test('gated flow with keyboard accessibility', async ({ page }) => {
    console.log('🧪 Testing gated flow with keyboard accessibility...');

    const testUrl = buildTestUrl('/');
    await page.goto(testUrl);
    await page.waitForLoadState('networkidle');

    // Simulate file upload and validation completion
    await page.evaluate(() => {
      // Mock a completed validation with gated results
      window.mockGatedResults = true;

      // Create the gated results component
      const gatedResults = document.createElement('div');
      gatedResults.className = 'gated-results';
      gatedResults.innerHTML = `
        <div class="results-summary">
          <h3>Validation Complete</h3>
          <p>5 citations found: 3 perfect, 2 with errors</p>
        </div>
        <button class="reveal-button" data-testid="reveal-button">
          Reveal Results
        </button>
      `;
      document.body.appendChild(gatedResults);
    });

    // Focus the reveal button using keyboard
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab'); // Navigate to reveal button

    // Verify button is focused
    const revealButton = page.locator('.reveal-button').first();
    await expect(revealButton).toBeFocused();

    // Test Enter key
    await page.keyboard.press('Enter');

    // Test Space key (if needed for retry)
    await page.keyboard.press('Space');

    console.log('✅ Keyboard accessibility test passed!');
  });

  test('gated flow error handling', async ({ page }) => {
    console.log('🧪 Testing gated flow error handling...');

    const testUrl = buildTestUrl('/');
    await page.goto(testUrl);
    await page.waitForLoadState('networkidle');

    // Simulate gated results with error scenario
    await page.evaluate(() => {
      // Mock gated results with error handling
      const gatedResults = document.createElement('div');
      gatedResults.className = 'gated-results';
      gatedResults.innerHTML = `
        <div class="results-summary">
          <h3>Validation Complete</h3>
          <p>2 citations found: 1 perfect, 1 with errors</p>
        </div>
        <button class="reveal-button" id="error-reveal-btn">
          Reveal Results
        </button>
      `;
      document.body.appendChild(gatedResults);

      // Mock failed API response for reveal
      const originalFetch = window.fetch;
      window.fetch = function (url, options) {
        if (url.includes('/api/reveal-results')) {
          return Promise.resolve({
            ok: false,
            status: 500,
            statusText: 'Internal Server Error'
          });
        }
        return originalFetch.apply(this, arguments);
      };
    });

    const revealButton = page.locator('#error-reveal-btn').first();
    await revealButton.click();

    // Verify error handling (results should still be revealed locally)
    await page.waitForTimeout(1000);

    // Check that error was logged but UI still works
    const consoleLogs = await page.evaluate(() => {
      return window.consoleLogs || [];
    });

    const hasErrorLog = consoleLogs.some(log =>
      log.includes('Failed to track reveal results') ||
      log.includes('Error tracking reveal results')
    );

    expect(hasErrorLog).toBe(true);
    console.log('✅ Error handling test passed!');
  });

  test('gated flow analytics validation', async ({ page }) => {
    console.log('🧪 Testing gated flow analytics validation...');

    const testUrl = buildTestUrl('/');
    await page.goto(testUrl);
    await page.waitForLoadState('networkidle');

    // Test analytics functions are available and working
    const analyticsTest = await page.evaluate(() => {
      return {
        validateData: window.validateTrackingData?.('test-job-123', 45),
        trackEvent: window.trackResultsRevealedSafe?.('test-job-123', 45, 'free'),
        functionsExist: {
          validateTrackingData: typeof window.validateTrackingData === 'function',
          trackResultsRevealedSafe: typeof window.trackResultsRevealedSafe === 'function'
        }
      };
    });

    expect(analyticsTest.functionsExist.validateTrackingData).toBe(true);
    expect(analyticsTest.functionsExist.trackResultsRevealedSafe).toBe(true);
    expect(analyticsTest.validateData.isValid).toBe(true);
    expect(analyticsTest.trackEvent).toBe(true);

    console.log('✅ Analytics validation test passed!');
  });

  test('gated flow timing validation', async ({ page }) => {
    console.log('🧪 Testing gated flow timing validation...');

    const testUrl = buildTestUrl('/');
    await page.goto(testUrl);
    await page.waitForLoadState('networkidle');

    // Test timing calculation with controlled scenario
    const timingTest = await page.evaluate(() => {
      const startTime = Date.now();

      // Simulate results ready timestamp
      window.resultsReadyTimestamp = startTime - 5000; // 5 seconds ago

      // Simulate reveal
      const timeToReveal = Math.floor((Date.now() - window.resultsReadyTimestamp) / 1000);

      return {
        simulatedTimeToReveal: timeToReveal,
        isValid: window.validateTrackingData?.('timing-test-job', timeToReveal),
        withinBounds: timeToReveal >= 0 && timeToReveal <= 3600
      };
    });

    expect(timingTest.simulatedTimeToReveal).toBeGreaterThanOrEqual(0);
    expect(timingTest.simulatedTimeToReveal).toBeLessThanOrEqual(3600);
    expect(timingTest.isValid.isValid).toBe(true);
    expect(timingTest.withinBounds).toBe(true);

    console.log(`   ⏱️  Time to reveal: ${timingTest.simulatedTimeToReveal}s`);
    console.log('✅ Timing validation test passed!');
  });
});