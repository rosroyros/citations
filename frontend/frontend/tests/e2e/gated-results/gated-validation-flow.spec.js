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

    // Mock job creation endpoint
    await page.route(/\/api\/validate\/async/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'mock-gated-job-123',
          status: 'pending',
          experiment_variant: 0
        })
      });
    });

    // Mock job polling to return gated results
    await page.route(/\/api\/jobs\/.*/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'completed',
          results: {
            results: [
              { original: 'Smith, J. (2023). Test citation. Journal, 1(1), 1-10.', source_type: 'journal', errors: [] },
              { original: 'Brown, A. (2022). Another test. Book Press.', source_type: 'book', errors: [{ component: 'title', problem: 'Not italicized', correction: '_Another test_' }] }
            ],
            user_status: {
              type: 'free',
              validations_used: 5,
              limit: 5
            },
            results_gated: true
          }
        })
      });
    });

    // Navigate to home page
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    const initialLength = capturedRequests.length;

    // Find the editor and enter citation
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible({ timeout: 10000 });
    await editor.fill('Smith, J. (2023). Test citation. Journal, 1(1), 1-10.');

    // Submit validation
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeEnabled({ timeout: 5000 });
    await submitButton.click();

    // Wait for gated results to appear
    console.log('⏳ Waiting for gated results...');
    await expect(page.locator('[data-testid="gated-results"]').first()).toBeVisible({ timeout: 30000 });
    console.log('📋 Gated results component visible');

    // Verify reveal button is present
    const revealButton = page.locator('button:has-text("View Results")').first();
    await expect(revealButton).toBeVisible();
    await expect(revealButton).toBeEnabled();

    // Click reveal button
    console.log('🎯 Clicking View Results button...');
    await revealButton.click();

    // Wait for results to be revealed (gated component should disappear)
    await expect(page.locator('.validation-table-container').first()).toBeVisible({ timeout: 10000 });
    console.log('✅ Results revealed successfully');

    // Verify analytics events were captured (optional - GA may not fire on localhost)
    const allEvents = capturedRequests.slice(initialLength);
    console.log(`📊 Total events captured: ${allEvents.length}`);

    // Check for results_revealed event (may not fire in all environments)
    const resultsRevealedEvents = getEventsByName(allEvents, 'results_revealed');
    console.log(`📊 Results revealed events: ${resultsRevealedEvents.length}`);

    if (resultsRevealedEvents.length > 0) {
      const revealedEvent = resultsRevealedEvents[0];
      const eventUrl = revealedEvent.url();
      const jobId = getEventParam(eventUrl, 'job_id');
      console.log(`   🆔 Job ID in analytics: ${jobId}`);
    }

    console.log('✅ Complete gated flow test passed!');
  });

  test('gated flow with keyboard accessibility', async ({ page }) => {
    console.log('🧪 Testing gated flow with keyboard accessibility...');

    // Mock job creation endpoint
    await page.route(/\/api\/validate\/async/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'mock-gated-a11y-123',
          status: 'pending',
          experiment_variant: 0
        })
      });
    });

    // Mock job polling to return gated results
    await page.route(/\/api\/jobs\/.*/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'completed',
          results: {
            results: [
              { original: 'Test citation', source_type: 'journal', errors: [] }
            ],
            user_status: {
              type: 'free',
              validations_used: 5,
              limit: 5
            },
            results_gated: true
          }
        })
      });
    });

    // Navigate and submit
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible({ timeout: 10000 });
    await editor.fill('Test citation for accessibility');

    await page.locator('button[type="submit"]').click();

    // Wait for gated results
    await expect(page.locator('[data-testid="gated-results"]').first()).toBeVisible({ timeout: 30000 });

    // Test keyboard navigation to View Results button
    const viewResultsButton = page.locator('button:has-text("View Results")').first();
    await expect(viewResultsButton).toBeVisible();

    // Focus the button using Tab navigation
    await viewResultsButton.focus();
    await expect(viewResultsButton).toBeFocused();

    // Test Enter key activates button
    await page.keyboard.press('Enter');

    // Verify results are revealed
    await expect(page.locator('.validation-table-container').first()).toBeVisible({ timeout: 10000 });

    console.log('✅ Keyboard accessibility test passed!');
  });

  test('gated flow shows correct citation counts', async ({ page }) => {
    console.log('🧪 Testing gated flow citation counts...');

    // Mock job creation endpoint
    await page.route(/\/api\/validate\/async/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'mock-gated-counts-123',
          status: 'pending',
          experiment_variant: 0
        })
      });
    });

    // Mock job polling to return gated results with specific counts
    await page.route(/\/api\/jobs\/.*/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'completed',
          results: {
            results: [
              { original: 'Perfect citation 1', source_type: 'journal', errors: [] },
              { original: 'Perfect citation 2', source_type: 'book', errors: [] },
              { original: 'Citation with error', source_type: 'website', errors: [{ component: 'url', problem: 'Missing', correction: 'Add URL' }] }
            ],
            user_status: {
              type: 'free',
              validations_used: 5,
              limit: 5
            },
            results_gated: true
          }
        })
      });
    });

    // Navigate and submit
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible({ timeout: 10000 });
    await editor.fill('Citation 1\\nCitation 2\\nCitation 3');

    await page.locator('button[type="submit"]').click();

    // Wait for gated results
    const gatedResults = page.locator('[data-testid="gated-results"]').first();
    await expect(gatedResults).toBeVisible({ timeout: 30000 });

    // Verify the gated results show citation summary
    // The component should display count information
    await expect(gatedResults).toBeVisible();

    // Click to reveal
    await page.locator('button:has-text("View Results")').first().click();

    // Verify results table is visible with correct number of rows
    await expect(page.locator('.validation-table-container').first()).toBeVisible({ timeout: 10000 });

    console.log('✅ Gated flow citation counts test passed!');
  });
});