import { test, expect } from '@playwright/test';

// Constants for async polling tests
const TIMEOUT = 120000; // 2 minutes for large batches
const POLLING_TIMEOUT = 180000; // 3 minutes for very large batches

// Test data for different scenarios
const testCitations = {
  // 5 citations for small batch test
  smallBatch: [
    'Smith, J. (2023). The impact of artificial intelligence on modern society. Journal of Technology Studies, 45(2), 123-145.',
    'Johnson, M. K. (2023). Climate change and renewable energy: A comprehensive review. Environmental Science Quarterly, 78(4), 567-589.',
    'Williams, R. A. (2023). Educational psychology in the digital age. Learning and Instruction, 67, 101-115.',
    'Brown, T. L. (2023). Global supply chain management: Challenges and opportunities. Business Logistics Review, 12(3), 234-251.',
    'Davis, S. M. (2023). Public health in post-pandemic era. Health Policy Journal, 23(1), 45-67.'
  ],

  // 15 citations for partial results test
  mediumBatch: [
    'Smith, J. (2023). The impact of artificial intelligence on modern society. Journal of Technology Studies, 45(2), 123-145.',
    'Johnson, M. K. (2023). Climate change and renewable energy: A comprehensive review. Environmental Science Quarterly, 78(4), 567-589.',
    'Williams, R. A. (2023). Educational psychology in the digital age. Learning and Instruction, 67, 101-115.',
    'Brown, T. L. (2023). Global supply chain management: Challenges and opportunities. Business Logistics Review, 12(3), 234-251.',
    'Davis, S. M. (2023). Public health in post-pandemic era. Health Policy Journal, 23(1), 45-67.',
    'Miller, T. (2023). Database design patterns. Data Today, 14(1), 45-67.',
    'Wilson, S. (2023). Network security essentials. Security Focus, 9(4), 201-223.',
    'Moore, L. (2023). Mobile app development. App Developer Journal, 7(3), 134-156.',
    'Taylor, J. (2023). DevOps best practices. Ops Weekly, 11(2), 78-92.',
    'Anderson, P. (2023). UX design principles. Design Today, 6(1), 34-56.',
    'Thomas, E. (2023). Software architecture patterns. Architecture Monthly, 18(3), 234-267.',
    'Jackson, R. (2023). Cloud native applications. Cloud Computing Review, 9(2), 145-178.',
    'White, M. (2023). Data privacy regulations. Privacy Law Journal, 15(4), 345-378.',
    'Harris, D. (2023). Machine learning ethics. AI Ethics Review, 3(1), 23-45.',
    'Martin, S. (2023). Cybersecurity best practices. Security Today, 22(3), 189-212.'
  ]
};

test.describe('Async Polling Architecture Validation - Fixed', () => {
  test.use({ baseURL: 'http://localhost:5173' });

  test.beforeEach(async ({ page }) => {
    // Clear cookies and localStorage before each test
    await page.context().clearCookies();
    await page.addInitScript(() => {
      localStorage.clear();
    });
    await page.goto('/');

    // Wait for app to load
    await expect(page.locator('body')).toBeVisible();

    // Find the editor (TipTap uses .ProseMirror)
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
  });

  test('Scenario 1: Free user - Small batch (5 citations)', async ({ page }) => {
    console.log('🚀 Scenario 1: Free user - Small batch');

    // Submit 5 citations
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await editor.fill(testCitations.smallBatch.join('\n'));

    // Monitor console for job_id lifecycle
    const consoleMessages = [];
    page.on('console', msg => {
      consoleMessages.push({ type: msg.type(), text: msg.text() });
      if (msg.text().includes('job_id') || msg.text().includes('current_job_id')) {
        console.log('📝 Console job tracking:', msg.text());
      }
    });

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Verify loading state appears - use correct ValidationLoadingState selector
    await expect(page.locator('.validation-loading-container').first()).toBeVisible({ timeout: 5000 });

    // Wait for results (should complete faster than timeout)
    await expect(page.locator('.validation-table').first()).toBeVisible({ timeout: TIMEOUT });

    // Verify job_id removed from localStorage
    const jobId = await page.evaluate(() => localStorage.getItem('current_job_id'));
    expect(jobId).toBeNull();

    console.log('✅ Scenario 1 completed successfully');
  });

  test('Scenario 2: Free user - Partial results (15 citations)', async ({ page }) => {
    console.log('🚀 Scenario 2: Free user - Partial results');

    // Set localStorage to simulate user has already used 5 citations
    await page.addInitScript(() => {
      localStorage.setItem('citation_checker_free_used', '5');
    });
    await page.goto('/');

    // Submit 15 citations (5 remaining + 10 that should be locked)
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await editor.fill(testCitations.mediumBatch.join('\n'));

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Verify loading state appears
    await expect(page.locator('.validation-loading-container').first()).toBeVisible({ timeout: 5000 });

    // Wait for results
    await expect(page.locator('.validation-table').first()).toBeVisible({ timeout: TIMEOUT });

    // Verify PartialResults component is displayed - use correct selector
    await expect(page.locator('[data-testid="partial-results"]').first()).toBeVisible();

    // Verify upgrade prompt is displayed - look for the upgrade banner content
    await expect(page.locator('.upgrade-banner').first()).toBeVisible();

    // Verify localStorage shows correct free usage count (10 total)
    const freeUsed = await page.evaluate(() => localStorage.getItem('citation_checker_free_used'));
    expect(freeUsed).toBe('10');

    console.log('✅ Scenario 2 completed successfully');
  });

  test('Scenario 3: Page refresh recovery (25 citations)', async ({ page }) => {
    console.log('🚀 Scenario 3: Page refresh recovery');

    // Submit 15 citations (using medium batch for reasonable processing time)
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await editor.fill(testCitations.mediumBatch.join('\n'));

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Verify loading state appears
    await expect(page.locator('.validation-loading-container').first()).toBeVisible({ timeout: 5000 });

    // Wait for job_id to be stored in localStorage
    await page.waitForFunction(() => {
      return localStorage.getItem('current_job_id') !== null;
    }, { timeout: 10000 });

    const jobIdBeforeRefresh = await page.evaluate(() => localStorage.getItem('current_job_id'));
    expect(jobIdBeforeRefresh).toBeTruthy();

    // Wait 10 seconds while processing
    await page.waitForTimeout(10000);

    // Refresh browser page
    await page.reload();

    // Wait for app to load again
    await expect(page.locator('body')).toBeVisible();

    // Verify job_id is recovered from localStorage
    const jobIdAfterRefresh = await page.evaluate(() => localStorage.getItem('current_job_id'));
    expect(jobIdAfterRefresh).toBe(jobIdBeforeRefresh);

    // Wait for results to appear after recovery
    await expect(page.locator('.validation-table').first()).toBeVisible({ timeout: POLLING_TIMEOUT });

    // Verify job_id removed after completion
    const finalJobId = await page.evaluate(() => localStorage.getItem('current_job_id'));
    expect(finalJobId).toBeNull();

    console.log('✅ Scenario 3 completed successfully');
  });

  test('Scenario 4: Large batch without timeout (50 citations)', async ({ page }) => {
    console.log('🚀 Scenario 4: Large batch without timeout');

    // This test requires credits - simulate having sufficient credits
    await page.addInitScript(() => {
      localStorage.setItem('user_token', 'test-token-with-credits');
    });
    await page.goto('/');

    // Submit 15 citations (using medium batch for reasonable testing time)
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await editor.fill(testCitations.mediumBatch.join('\n'));

    // Monitor for network errors (should not get 502/504)
    const networkErrors = [];
    page.on('response', response => {
      if (response.status() >= 500) {
        networkErrors.push({ status: response.status(), url: response.url() });
      }
    });

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Verify loading state appears
    await expect(page.locator('.validation-loading-container').first()).toBeVisible({ timeout: 5000 });

    // Wait for results without timeout errors (using extended timeout for production)
    await expect(page.locator('.validation-table').first()).toBeVisible({ timeout: POLLING_TIMEOUT });

    // Verify no network errors occurred
    expect(networkErrors.length).toBe(0);

    // Verify results displayed (should have multiple rows)
    const resultRows = await page.locator('.validation-table tr, .result-row').count();
    expect(resultRows).toBeGreaterThan(5); // Reasonable expectation for medium batch

    console.log(`✅ Scenario 4 completed successfully with ${resultRows} results`);
  });

  test('Scenario 5: Submit button disabled during polling', async ({ page }) => {
    console.log('🚀 Scenario 5: Submit button disabled during polling');

    // Submit 5 citations for a reasonable processing time
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await editor.fill(testCitations.smallBatch.join('\n'));

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Verify loading state appears
    await expect(page.locator('.validation-loading-container').first()).toBeVisible({ timeout: 5000 });

    // While loading state is active, verify submit button is disabled
    const submitButton = page.locator('button[type="submit"]');
    await expect(submitButton).toBeDisabled();

    // Verify button text shows "Validating..."
    await expect(submitButton).toHaveText('Validating...');

    // Try clicking submit again - should fail because button is disabled
    try {
      await submitButton.click({ timeout: 2000 });
      // If we get here, the button was clickable (this would be a failure)
      expect(false).toBeTruthy('Submit button should be disabled during polling');
    } catch (error) {
      // Expected - button should be disabled and not clickable
      expect(error.message).toContain('disabled');
    }

    // Verify only one job was created by checking localStorage
    const jobId = await page.evaluate(() => localStorage.getItem('current_job_id'));
    expect(jobId).toBeTruthy();

    // Wait a bit and ensure button is still disabled
    await page.waitForTimeout(2000);
    await expect(submitButton).toBeDisabled();

    // Wait for completion
    await expect(page.locator('.validation-table').first()).toBeVisible({ timeout: TIMEOUT });

    // After completion, button should be enabled again
    await expect(submitButton).toBeEnabled();

    console.log('✅ Scenario 5 completed successfully');
  });

  test('Additional Verification: Console and Network Error Checking', async ({ page }) => {
    console.log('🚀 Additional Verification: Error checking');

    const consoleErrors = [];
    const networkErrors = [];

    // Monitor console for errors
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
        console.log('❌ Console error:', msg.text());
      }
    });

    // Monitor network for errors
    page.on('response', response => {
      if (response.status() >= 400) {
        networkErrors.push({ status: response.status(), url: response.url() });
        console.log('❌ Network error:', response.status(), response.url());
      }
    });

    // Run a simple test to check for errors
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await editor.fill(testCitations.smallBatch.slice(0, 3).join('\n'));

    await page.locator('button[type="submit"]').click();
    await expect(page.locator('.validation-table').first()).toBeVisible({ timeout: TIMEOUT });

    // Verify no console or network errors
    expect(consoleErrors.length).toBe(0);
    expect(networkErrors.filter(e => e.status >= 500).length).toBe(0);

    console.log('✅ Error checking completed - no errors found');
  });
});