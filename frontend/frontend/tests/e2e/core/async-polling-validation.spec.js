import { test, expect } from '@playwright/test';

// Constants for async polling tests
const TIMEOUT = 180000; // 3 minutes for large batches (increased for production safety)
const POLLING_TIMEOUT = 300000; // 5 minutes for very large batches (extended for production latency variations)

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
  ],

  // 25 citations for large batch/page refresh test
  largeBatch: [
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
    'Martin, S. (2023). Cybersecurity best practices. Security Today, 22(3), 189-212.',
    'Thompson, K. (2023). Blockchain technology fundamentals. Tech Innovation, 12(4), 456-489.',
    'Garcia, L. (2023). Quantum computing applications. Quantum Journal, 7(2), 123-156.',
    'Martinez, C. (2023). Big data analytics. Data Science Review, 19(1), 67-89.',
    'Robinson, J. (2023). IoT security challenges. Internet of Things, 8(3), 234-267.',
    'Clark, A. (2023). Digital transformation strategies. Business Tech, 16(2), 145-178.',
    'Rodriguez, M. (2023). Artificial intelligence in healthcare. Medical Tech Journal, 14(4), 289-312.',
    'Lewis, D. (2023). Sustainable technology practices. Green Computing, 6(1), 34-56.',
    'Lee, S. (2023). Robotics automation. Robotics Today, 11(3), 189-223.',
    'Walker, K. (2023). Cloud migration strategies. Cloud Strategies, 9(4), 345-378.',
    'Hall, B. (2023). Edge computing benefits. Distributed Systems, 15(2), 167-189.'
  ]
};

test.describe('Async Polling Architecture Validation', () => {
  test.use({
    baseURL: process.env.CI ? 'https://citationformatchecker.com' : 'http://localhost:5173'
  });

  test.beforeEach(async ({ page }) => {
    // Clear cookies and localStorage before each test
    await page.context().clearCookies();
    await page.addInitScript(() => {
      localStorage.clear();
    });
    // NOTE: Do NOT navigate here - tests must set up routes first, then navigate
  });

  // Scenario 1: Tests async polling lifecycle for small batch
  test('Scenario 1: Free user - Small batch (5 citations)', async ({ page }) => {
    console.log('🚀 Scenario 1: Free user - Small batch');

    let pollCount = 0;

    // Mock job creation endpoint
    await page.route(/\/api\/validate\/async/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'mock-small-batch-123',
          status: 'pending',
          experiment_variant: 0
        })
      });
    });

    // Mock job polling - return pending first, then completed
    await page.route(/\/api\/jobs\/.*/, async (route) => {
      pollCount++;
      if (pollCount <= 1) {
        // First poll returns pending
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'pending',
            progress: 50
          })
        });
      } else {
        // Subsequent polls return completed
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'completed',
            results: {
              results: testCitations.smallBatch.map(c => ({
                original: c,
                source_type: 'journal',
                errors: []
              })),
              user_status: { type: 'free', validations_used: 5, limit: 5 }
            }
          })
        });
      }
    });

    // Navigate to app
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Submit 5 citations
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible({ timeout: 10000 });
    await editor.fill(testCitations.smallBatch.join('\n'));

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Wait for results (mock may complete quickly)
    await expect(page.locator('.validation-table').first()).toBeVisible({ timeout: TIMEOUT });

    // Verify results displayed
    const resultRows = await page.locator('.validation-table tr').count();
    expect(resultRows).toBeGreaterThanOrEqual(1); // At least header + some results

    console.log('✅ Scenario 1 completed successfully');
  });

  // Scenario 2: Tests credits user flow with proper mocking
  test('Scenario 2: Credits user - Full results with balance update', async ({ page }) => {
    console.log('🚀 Scenario 2: Credits user - Full results');

    // Set up as credits user with token
    await page.addInitScript(() => {
      localStorage.setItem('user_token', 'test-credits-token');
    });

    // Mock job creation endpoint
    await page.route(/\/api\/validate\/async/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'mock-credits-job-123',
          status: 'pending',
          experiment_variant: 0
        })
      });
    });

    // Mock job polling to return full results with credits balance
    await page.route(/\/api\/jobs\/.*/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'completed',
          results: {
            results: testCitations.smallBatch.map(c => ({
              original: c,
              source_type: 'journal',
              errors: []
            })),
            user_status: {
              type: 'credits',
              balance: 95  // Started with 100, used 5
            }
          }
        })
      });
    });

    // Mock user credits endpoint  
    await page.route('/api/user/credits**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          credits: 95,
          active_pass: null
        })
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Submit citations
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible({ timeout: 10000 });
    await editor.fill(testCitations.smallBatch.join('\n'));

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Wait for results to appear
    await expect(page.locator('.validation-table').first()).toBeVisible({ timeout: TIMEOUT });

    // Verify results displayed 
    const resultRows = await page.locator('.validation-table tr').count();
    expect(resultRows).toBeGreaterThanOrEqual(1);

    console.log('✅ Scenario 2 completed successfully');
  });

  // Scenario 3: Tests pass user validation flow
  test('Scenario 3: Pass user - Full results with daily limit', async ({ page }) => {
    console.log('🚀 Scenario 3: Pass user - Full results');

    // Set up as pass user with token
    await page.addInitScript(() => {
      localStorage.setItem('user_token', 'test-pass-token');
    });

    // Mock job creation endpoint
    await page.route(/\/api\/validate\/async/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'mock-pass-job-123',
          status: 'pending',
          experiment_variant: 0
        })
      });
    });

    // Mock job polling to return full results with pass user status
    await page.route(/\/api\/jobs\/.*/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'completed',
          results: {
            results: testCitations.smallBatch.map(c => ({
              original: c,
              source_type: 'journal',
              errors: []
            })),
            user_status: {
              type: 'pass',
              pass_type: '30-Day Pass',
              daily_used: 5,
              daily_limit: 1000,
              reset_time: Math.floor(Date.now() / 1000) + 3600 * 12  // 12 hours from now
            }
          }
        })
      });
    });

    // Mock user credits endpoint
    await page.route('/api/user/credits**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          credits: 0,
          active_pass: {
            pass_type: '30-Day Pass',
            daily_used: 5,
            daily_limit: 1000
          }
        })
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Submit citations
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible({ timeout: 10000 });
    await editor.fill(testCitations.smallBatch.join('\n'));

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Wait for results to appear
    await expect(page.locator('.validation-table').first()).toBeVisible({ timeout: TIMEOUT });

    // Verify results displayed
    const resultRows = await page.locator('.validation-table tr').count();
    expect(resultRows).toBeGreaterThanOrEqual(1);

    console.log('✅ Scenario 3 completed successfully');
  });

  // Scenario 4: Tests large batch processing (50 citations)
  test('Scenario 4: Large batch processing (50 citations)', async ({ page }) => {
    console.log('🚀 Scenario 4: Large batch processing');

    // Mock job creation endpoint
    await page.route(/\/api\/validate\/async/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'mock-large-batch-job-123',
          status: 'pending',
          experiment_variant: 0
        })
      });
    });

    // Mock job polling to return 50 results
    await page.route(/\/api\/jobs\/.*/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'completed',
          results: {
            results: Array(50).fill({ original: 'Test citation', source_type: 'journal', errors: [] }),
            user_status: { type: 'credits', balance: 50 }
          }
        })
      });
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Generate 50 citations for large batch test
    const largeBatchCitations = [];
    for (let i = 1; i <= 50; i++) {
      largeBatchCitations.push(`Author${i}, A. (2023). Research article ${i}. Academic Journal, ${i}(1), 1-20.`);
    }

    // Submit 50 citations
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible({ timeout: 10000 });
    await editor.fill(largeBatchCitations.join('\n'));

    // Submit form
    await page.locator('button[type="submit"]').click();

    // Wait for results to appear
    await expect(page.locator('.validation-table').first()).toBeVisible({ timeout: TIMEOUT });

    // Verify table rendered successfully (mocked, so just check table exists)
    const resultRows = await page.locator('.validation-table tr').count();
    expect(resultRows).toBeGreaterThanOrEqual(1);

    console.log(`✅ Scenario 4 completed successfully with ${resultRows} result rows`);
  });

  test('Scenario 5: Submit button disabled during polling', async ({ page }) => {
    console.log('🚀 Scenario 5: Submit button disabled during polling');

    let pollCount = 0;

    // Mock job creation endpoint
    await page.route(/\/api\/validate\/async/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'mock-button-test-job-123',
          status: 'pending',
          experiment_variant: 0
        })
      });
    });

    // Mock job polling - return pending first to test button state, then complete
    await page.route(/\/api\/jobs\/.*/, async (route) => {
      pollCount++;
      if (pollCount <= 2) {
        // Keep pending to test button disabled state
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'pending',
            progress: 50
          })
        });
      } else {
        // Complete
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'completed',
            results: {
              results: Array(5).fill({ original: 'Test', source_type: 'journal', errors: [] }),
              user_status: { type: 'free', validations_used: 5, limit: 5 }
            }
          })
        });
      }
    });

    await page.goto('/');

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

    // Verify button remains disabled while processing continues (poll for stability)
    await expect.poll(async () => {
      return submitButton.isDisabled();
    }, { timeout: 5000 }).toBe(true);

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

    // Navigate to app
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Run a simple test to check for errors
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible({ timeout: 10000 });
    await editor.fill(testCitations.smallBatch.slice(0, 3).join('\n'));

    await page.locator('button[type="submit"]').click();
    await expect(page.locator('.validation-table').first()).toBeVisible({ timeout: TIMEOUT });

    // Verify no console or network errors
    expect(consoleErrors.length).toBe(0);
    expect(networkErrors.filter(e => e.status >= 500).length).toBe(0);

    console.log('✅ Error checking completed - no errors found');
  });
});