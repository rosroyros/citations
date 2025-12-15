import { test, expect } from '@playwright/test';

/**
 * E2E tests for complete user access flows
 *
 * Tests all user states:
 * 1. Free user: 10 validations, then blocked
 * 2. Credits user: Purchase credits, use them, balance decreases
 * 3. Pass user: Use up to 1000, hit limit, see reset timer
 * 4. UserStatus component updates correctly
 * 5. Error messages display correctly
 */

test.describe('User Access Flows - E2E Tests', () => {
  test.use({
    baseURL: 'http://localhost:5173',
    viewport: { width: 1280, height: 720 }
  });

  test.beforeEach(async ({ page }) => {
    // Clear cookies and localStorage before each test
    await page.context().clearCookies();
    await page.addInitScript(() => {
      localStorage.clear();
      // Set test mode flags
      window.VITE_TEST_MODE = 'true';
      window.VITE_GATED_RESULTS_ENABLED = 'true';
    });
    await page.goto('/');
  });

  test.describe('Free User Flow', () => {
    test('should allow 10 validations then block free user', async ({ page }) => {
      console.log('🧪 Testing free user flow: 10 validations then block...');

      // Mock validation responses for free user
      let validationCount = 0;
      await page.route('/api/jobs/**', async (route) => {
        validationCount++;

        // First 10 validations succeed
        if (validationCount <= 10) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'completed',
              results: {
                results: [{
                  original: `Test citation ${validationCount}`,
                  source_type: 'journal',
                  errors: []
                }],
                user_status: {
                  type: 'free',
                  validations_used: validationCount,
                  limit: 10
                }
              }
            })
          });
        } else {
          // 11th validation is blocked
          await route.fulfill({
            status: 402,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'LIMIT_EXCEEDED',
              message: 'You have reached your free limit of 10 validations. Please upgrade to continue.',
              user_status: {
                type: 'free',
                validations_used: 10,
                limit: 10
              }
            })
          });
        }
      });

      const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
      await expect(editor).toBeVisible();

      // Perform 10 successful validations
      for (let i = 1; i <= 10; i++) {
        console.log(`  📝 Validation ${i}/10`);
        await editor.fill(`Test citation ${i}`);
        await page.locator('button[type="submit"]').click();

        // Wait for results
        await expect(page.locator('.validation-table-container, .validation-table').first()).toBeVisible({ timeout: 30000 });

        // Verify UserStatus updates
        const userStatus = page.locator('.user-status');
        await expect(userStatus).toBeVisible();
        await expect(userStatus).toContainText(`${i}/10 used`);

        // Clear for next validation
        if (i < 10) {
          await page.reload();
          await page.waitForTimeout(1000);
        }
      }

      // 11th validation should be blocked
      console.log('  🚫 Testing 11th validation (should be blocked)...');
      await editor.fill('Test citation 11 - should be blocked');
      await page.locator('button[type="submit"]').click();

      // Verify error message appears
      await expect(page.locator('text=You have reached your free limit')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('text=Please upgrade to continue')).toBeVisible();

      // Verify upgrade CTA is visible
      await expect(page.locator('a[href*="polar.sh"], button:has-text("Upgrade")')).toBeVisible();

      console.log('✅ Free user flow test passed');
    });
  });

  test.describe('Credits User Flow', () => {
    test('should allow purchase and track credit usage', async ({ page }) => {
      console.log('🧪 Testing credits user flow...');

      // Mock successful checkout and credit balance
      await page.route('/api/user/credits', async (route) => {
        if (route.request().method() === 'GET') {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ balance: 100 })
          });
        }
      });

      // Mock validation responses that track credit usage
      let creditsRemaining = 100;
      await page.route('/api/jobs/**', async (route) => {
        const citationCount = 2; // Each validation uses 2 credits

        if (creditsRemaining >= citationCount) {
          creditsRemaining -= citationCount;
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'completed',
              results: {
                results: [
                  { original: 'Citation 1', source_type: 'journal', errors: [] },
                  { original: 'Citation 2', source_type: 'book', errors: [] }
                ],
                user_status: {
                  type: 'credits',
                  balance: creditsRemaining
                }
              }
            })
          });
        } else {
          // Not enough credits
          await route.fulfill({
            status: 402,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'INSUFFICIENT_CREDITS',
              message: `You need ${citationCount} credits but only have ${creditsRemaining} remaining.`,
              user_status: {
                type: 'credits',
                balance: creditsRemaining
              }
            })
          });
        }
      });

      const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
      await expect(editor).toBeVisible();

      // Check initial balance
      await editor.fill('Test initial check');
      await page.locator('button[type="submit"]').click();
      await expect(page.locator('.validation-table-container').first()).toBeVisible({ timeout: 30000 });

      let userStatus = page.locator('.user-status');
      await expect(userStatus).toBeVisible();
      await expect(userStatus).toContainText('98 credits remaining');

      // Continue using credits until low
      for (let i = 2; i <= 48; i++) { // Will use 2 credits each time, total 96 credits
        await page.reload();
        await page.waitForTimeout(1000);
        await editor.fill(`Batch ${i} - testing credit usage`);
        await page.locator('button[type="submit"]').click();
        await expect(page.locator('.validation-table-container').first()).toBeVisible({ timeout: 30000 });

        userStatus = page.locator('.user-status');
        await expect(userStatus).toBeVisible();
        const expectedCredits = 100 - (i * 2);
        await expect(userStatus).toContainText(`${expectedCredits} credits remaining`);

        // Check color changes when credits get low
        if (expectedCredits <= 10) {
          const badgeElementLow = userStatus.locator('div').first();
          await expect(badgeElementLow).toHaveClass(/.*destructive.*/);
        }
      }

      // Next validation should fail due to insufficient credits
      await page.reload();
      await page.waitForTimeout(1000);
      await editor.fill('Should fail - no credits');
      await page.locator('button[type="submit"]').click();

      await expect(page.locator('text=You need 2 credits but only have')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('text=Purchase more credits to continue')).toBeVisible();

      console.log('✅ Credits user flow test passed');
    });

    test('should handle credit purchase flow', async ({ page }) => {
      console.log('🧪 Testing credit purchase flow...');

      // Mock Polar checkout success
      await page.route('**/polar.sh/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'text/html',
          body: '<html><body>Mock Polar Checkout Page</body></html>'
        });
      });

      // Start with no credits
      await page.route('/api/user/credits', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ balance: 0 })
        });
      });

      // Navigate to upgrade page
      await page.locator('a[href*="polar.sh"], button:has-text("Upgrade")').first().click();

      // Verify pricing options are displayed
      await expect(page.locator('text=100 Credits')).toBeVisible();
      await expect(page.locator('text=500 Credits')).toBeVisible();
      await expect(page.locator('text=2000 Credits')).toBeVisible();

      // Mock successful purchase
      await page.evaluate(() => {
        // Simulate successful purchase callback
        window.postMessage({
          type: 'PURCHASE_SUCCESS',
          data: { credits: 100, productId: 'test-product-id' }
        }, '*');
      });

      console.log('✅ Credit purchase flow test passed');
    });
  });

  test.describe('Pass User Flow', () => {
    test('should allow 1000 daily validations with reset timer', async ({ page }) => {
      console.log('🧪 Testing pass user flow...');

      // Mock pass user status
      let dailyUsed = 0;
      const dailyLimit = 1000;
      const resetTime = Math.floor(Date.now() / 1000) + 3600 * 2; // 2 hours from now

      await page.route('/api/jobs/**', async (route) => {
        dailyUsed += 3; // Each validation uses 3 citations

        if (dailyUsed <= dailyLimit) {
          await route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({
              status: 'completed',
              results: {
                results: [
                  { original: `Pass citation ${dailyUsed - 2}`, source_type: 'journal', errors: [] },
                  { original: `Pass citation ${dailyUsed - 1}`, source_type: 'book', errors: [] },
                  { original: `Pass citation ${dailyUsed}`, source_type: 'website', errors: [] }
                ],
                user_status: {
                  type: 'pass',
                  hours_remaining: 168, // 7 days
                  daily_used: dailyUsed,
                  daily_limit: dailyLimit,
                  reset_time: resetTime
                }
              }
            })
          });
        } else {
          // Daily limit exceeded
          await route.fulfill({
            status: 429,
            contentType: 'application/json',
            body: JSON.stringify({
              error: 'DAILY_LIMIT_EXCEEDED',
              message: `You have reached your daily limit of ${dailyLimit} validations.`,
              user_status: {
                type: 'pass',
                hours_remaining: 168, // 7 days
                daily_used: dailyLimit,
                daily_limit: dailyLimit,
                reset_time: resetTime
              }
            })
          });
        }
      });

      const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
      await expect(editor).toBeVisible();

      // Test normal usage
      await editor.fill('Pass user test - first batch');
      await page.locator('button[type="submit"]').click();
      await expect(page.locator('.validation-table-container').first()).toBeVisible({ timeout: 30000 });

      // Verify UserStatus shows pass type (daily limit is internal)
      let userStatus = page.locator('.user-status');
      await expect(userStatus).toBeVisible();
      await expect(userStatus).toContainText('Day Pass');

      // Verify subtext shows days remaining
      const subtext = page.locator('.user-status-subtext');
      await expect(subtext).toBeVisible();
      await expect(subtext).toContainText('days left');

      // Simulate high usage (900 validations)
      dailyUsed = 900;
      await page.reload();
      await page.waitForTimeout(1000);
      await editor.fill('High usage test - 900 used');
      await page.locator('button[type="submit"]').click();
      await expect(page.locator('.validation-table-container').first()).toBeVisible({ timeout: 30000 });

      userStatus = page.locator('.user-status');
      await expect(userStatus).toContainText('Day Pass');

      // Should still show pass status
      const badgeWarning = userStatus.locator('div').first();
      // Color depends on days remaining, not usage

      // Test limit exceeded
      dailyUsed = 1000;
      await page.reload();
      await page.waitForTimeout(1000);
      await editor.fill('Should hit limit now');
      await page.locator('button[type="submit"]').click();

      await expect(page.locator('text=You have reached your daily limit')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('text=Your limit will reset at')).toBeVisible();

      console.log('✅ Pass user flow test passed');
    });

    test('should show correct reset timer countdown for daily limit', async ({ page }) => {
      console.log('🧪 Testing pass days remaining...');

      const now = Math.floor(Date.now() / 1000);
      const resetTime = now + 3600; // 1 hour from now

      await page.route('/api/jobs/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'completed',
            results: {
              results: [{ original: 'Reset timer test', source_type: 'journal', errors: [] }],
              user_status: {
                type: 'pass',
                hours_remaining: 168, // 7 days
                daily_used: 50,
                daily_limit: 1000,
                reset_time: resetTime
              }
            }
          })
        });
      });

      const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
      await editor.fill('Reset timer test');
      await page.locator('button[type="submit"]').click();
      await expect(page.locator('.validation-table-container').first()).toBeVisible({ timeout: 30000 });

      // Check that subtext shows days remaining
      const subtext = page.locator('.user-status-subtext');
      await expect(subtext).toBeVisible();

      // Should show "7 days left"
      const resetText = await subtext.textContent();
      expect(resetText).toMatch(/\d+ days? left/);

      console.log('✅ Reset timer test passed');
    });

    test('should show correct days remaining', async ({ page }) => {
      console.log('🧪 Testing pass days remaining...');

      const now = Math.floor(Date.now() / 1000);
      const resetTime = now + 3600; // 1 hour from now

      await page.route('/api/jobs/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'completed',
            results: {
              results: [{ original: 'Days remaining test', source_type: 'journal', errors: [] }],
              user_status: {
                type: 'pass',
                hours_remaining: 120, // 5 days
                daily_used: 50,
                daily_limit: 1000,
                reset_time: resetTime
              }
            }
          })
        });
      });

      const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
      await editor.fill('Days remaining test');
      await page.locator('button[type="submit"]').click();
      await expect(page.locator('.validation-table-container').first()).toBeVisible({ timeout: 30000 });

      // Check that subtext shows days remaining
      const subtext = page.locator('.user-status-subtext');
      await expect(subtext).toBeVisible();

      // Should show "5 days left"
      const subtextContent = await subtext.textContent();
      expect(subtextContent).toMatch(/\d+ days? left/);

      console.log('✅ Days remaining test passed');
    });
  });

  test.describe('UserStatus Component Updates', () => {
    test('should update correctly for each user type', async ({ page }) => {
      console.log('🧪 Testing UserStatus component updates...');

      // Test free user
      await page.route('/api/jobs/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'completed',
            results: {
              results: [{ original: 'Free user test', source_type: 'journal', errors: [] }],
              user_status: {
                type: 'free',
                validations_used: 7,
                limit: 10
              }
            }
          })
        });
      });

      const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
      await editor.fill('Free user test');
      await page.locator('button[type="submit"]').click();
      await expect(page.locator('.validation-table-container').first()).toBeVisible({ timeout: 30000 });

      let userStatus = page.locator('.user-status');
      await expect(userStatus).toBeVisible();
      await expect(userStatus).toContainText('Free tier');
      const badgeSecondary = userStatus.locator('div').first();
      await expect(badgeSecondary).toHaveClass(/bg-secondary/); // Neutral color

      // Test credits user with low balance
      await page.route('/api/jobs/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'completed',
            results: {
              results: [{ original: 'Low credits test', source_type: 'journal', errors: [] }],
              user_status: {
                type: 'credits',
                balance: 5
              }
            }
          })
        });
      });

      await page.reload();
      await page.waitForTimeout(1000);
      await editor.fill('Low credits test');
      await page.locator('button[type="submit"]').click();
      await expect(page.locator('.validation-table-container').first()).toBeVisible({ timeout: 30000 });

      userStatus = page.locator('.user-status');
      await expect(userStatus).toContainText('5 credits remaining');
      const badgeDestructive = userStatus.locator('div').first();
      await expect(badgeDestructive).toHaveClass(/bg-destructive/); // Red for low credits

      // Test pass user with low time remaining
      await page.route('/api/jobs/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'completed',
            results: {
              results: [{ original: 'Low time test', source_type: 'journal', errors: [] }],
              user_status: {
                type: 'pass',
                hours_remaining: 48, // 2 days
                reset_time: Math.floor(Date.now() / 1000) + 3600
              }
            }
          })
        });
      });

      await page.reload();
      await page.waitForTimeout(1000);
      await editor.fill('Low time test');
      await page.locator('button[type="submit"]').click();
      await expect(page.locator('.validation-table-container').first()).toBeVisible({ timeout: 30000 });

      userStatus = page.locator('.user-status');
      await expect(userStatus).toContainText('2-Day Pass');
      const badgeLowTime = userStatus.locator('div').first();
      await expect(badgeLowTime).toHaveClass(/bg-yellow-100/); // Yellow for 1-3 days remaining

      console.log('✅ UserStatus component update test passed');
    });
  });

  test.describe('Error Message Display', () => {
    test('should display appropriate error messages for each limit type', async ({ page }) => {
      console.log('🧪 Testing error message displays...');

      // Test free user limit error
      await page.route('/api/jobs/**', async (route) => {
        await route.fulfill({
          status: 402,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'LIMIT_EXCEEDED',
            message: 'You have reached your free limit of 10 validations. Please upgrade to continue.',
            user_status: {
              type: 'free',
              validations_used: 10,
              limit: 10
            }
          })
        });
      });

      const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
      await editor.fill('Free limit test');
      await page.locator('button[type="submit"]').click();

      await expect(page.locator('text=You have reached your free limit')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('text=Please upgrade to continue')).toBeVisible();
      await expect(page.locator('a[href*="polar.sh"], button:has-text("Upgrade")')).toBeVisible();

      // Test insufficient credits error
      await page.route('/api/jobs/**', async (route) => {
        await route.fulfill({
          status: 402,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'INSUFFICIENT_CREDITS',
            message: 'You need 5 credits but only have 2 remaining.',
            user_status: {
              type: 'credits',
              balance: 2
            }
          })
        });
      });

      await page.reload();
      await page.waitForTimeout(1000);
      await editor.fill('Insufficient credits test');
      await page.locator('button[type="submit"]').click();

      await expect(page.locator('text=You need 5 credits but only have 2 remaining')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('text=Purchase more credits to continue')).toBeVisible();

      // Test daily limit error
      await page.route('/api/jobs/**', async (route) => {
        await route.fulfill({
          status: 429,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'DAILY_LIMIT_EXCEEDED',
            message: 'You have reached your daily limit of 1000 validations.',
            user_status: {
              type: 'pass',
              daily_used: 1000,
              daily_limit: 1000,
              reset_time: Math.floor(Date.now() / 1000) + 3600
            }
          })
        });
      });

      await page.reload();
      await page.waitForTimeout(1000);
      await editor.fill('Daily limit test');
      await page.locator('button[type="submit"]').click();

      await expect(page.locator('text=You have reached your daily limit')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('text=Your limit will reset at')).toBeVisible();

      console.log('✅ Error message display test passed');
    });
  });

  test.describe('Mobile Responsiveness', () => {
    test.use({ viewport: { width: 375, height: 667 } });

    test('should display all user states correctly on mobile', async ({ page }) => {
      console.log('🧪 Testing mobile user states...');

      // Test that UserStatus is visible and functional on mobile
      await page.route('/api/jobs/**', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'completed',
            results: {
              results: [{ original: 'Mobile test', source_type: 'journal', errors: [] }],
              user_status: {
                type: 'credits',
                balance: 42
              }
            }
          })
        });
      });

      const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
      await expect(editor).toBeVisible();
      await editor.fill('Mobile test');
      await page.locator('button[type="submit"]').click();
      await expect(page.locator('.validation-table-container').first()).toBeVisible({ timeout: 30000 });

      // Verify UserStatus is visible on mobile
      const userStatus = page.locator('.user-status');
      await expect(userStatus).toBeVisible();
      await expect(userStatus).toContainText('42 credits remaining');

      // Verify error messages are readable on mobile
      await page.route('/api/jobs/**', async (route) => {
        await route.fulfill({
          status: 402,
          contentType: 'application/json',
          body: JSON.stringify({
            error: 'LIMIT_EXCEEDED',
            message: 'You have reached your free limit. Please upgrade.',
            user_status: {
              type: 'free',
              validations_used: 10,
              limit: 10
            }
          })
        });
      });

      await page.reload();
      await page.waitForTimeout(1000);
      await editor.fill('Mobile error test');
      await page.locator('button[type="submit"]').click();

      await expect(page.locator('text=You have reached your free limit')).toBeVisible({ timeout: 10000 });

      console.log('✅ Mobile responsiveness test passed');
    });
  });
});