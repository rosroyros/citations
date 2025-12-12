import { test, expect } from '@playwright/test';

// Helper function to mock API responses
const mockValidationResponse = (page, userStatus) => {
  return page.route('/api/jobs/**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'completed',
        results: {
          results: [
            {
              original: 'Smith, J. (2023). Test citation. *Journal*, 1(1), 1-10.',
              source_type: 'journal',
              errors: []
            }
          ],
          user_status: userStatus
        }
      })
    });
  });
};

test.describe('UserStatus Display', () => {
  test.use({
    baseURL: 'http://localhost:5173',
    viewport: { width: 1280, height: 720 }
  });

  test.beforeEach(async ({ page }) => {
    // Clear cookies and localStorage before each test
    await page.context().clearCookies();
    await page.addInitScript(() => {
      localStorage.clear();
    });
    await page.goto('/');
  });

  test('displays credits status for credit users', async ({ page }) => {
    // Set up mock response for credit user
    await mockValidationResponse(page, {
      type: 'credits',
      balance: 42
    });

    // Fill and submit form
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
    await editor.fill('Smith, J. (2023). Test citation. *Journal*, 1(1), 1-10.');

    await page.locator('button[type="submit"]').click();

    // Wait for results to load
    await expect(page.locator('.validation-table-container, .validation-table').first()).toBeVisible({ timeout: 30000 });

    // Verify UserStatus appears in header
    const userStatus = page.locator('.user-status');
    await expect(userStatus).toBeVisible();
    await expect(userStatus).toContainText('42 credits remaining');

    // Verify it has success variant styling (green for >10 credits)
    const badgeElement = userStatus.locator('div').first();
    await expect(badgeElement).toHaveClass(/bg-green-100/);
  });

  test('displays pass status with usage for pass users', async ({ page }) => {
    // Set up mock response for pass user
    await mockValidationResponse(page, {
      type: 'pass',
      daily_used: 237,
      daily_limit: 1000,
      reset_time: Math.floor(Date.now() / 1000) + 3600 * 2 // 2 hours from now
    });

    // Fill and submit form
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
    await editor.fill('Smith, J. (2023). Test citation. *Journal*, 1(1), 1-10.');

    await page.locator('button[type="submit"]').click();

    // Wait for results to load
    await expect(page.locator('.validation-table-container, .validation-table').first()).toBeVisible({ timeout: 30000 });

    // Verify UserStatus badge appears in header
    const userStatus = page.locator('.user-status');
    await expect(userStatus).toBeVisible();
    await expect(userStatus).toContainText('237/1000 used today');

    // Verify subtext shows reset time
    const subtext = page.locator('.user-status-subtext');
    await expect(subtext).toBeVisible();
    await expect(subtext).toContainText('resets in');

    // Verify it has success variant styling (green for <70% usage)
    const badgeElementSuccess = userStatus.locator('div').first();
    await expect(badgeElementSuccess).toHaveClass(/bg-green-100/);
  });

  test('displays warning color for high pass usage', async ({ page }) => {
    // Set up mock response for pass user with high usage
    await mockValidationResponse(page, {
      type: 'pass',
      daily_used: 750,
      daily_limit: 1000,
      reset_time: Math.floor(Date.now() / 1000) + 3600 // 1 hour from now
    });

    // Fill and submit form
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
    await editor.fill('Smith, J. (2023). Test citation. *Journal*, 1(1), 1-10.');

    await page.locator('button[type="submit"]').click();

    // Wait for results to load
    await expect(page.locator('.validation-table-container, .validation-table').first()).toBeVisible({ timeout: 30000 });

    // Verify UserStatus badge has warning variant (yellow for 70-90% usage)
    const userStatusWarning = page.locator('.user-status');
    await expect(userStatusWarning).toBeVisible();
    const badgeElementWarning = userStatusWarning.locator('div').first();
    await expect(badgeElementWarning).toHaveClass(/bg-yellow-100/);
  });

  test('displays destructive color for low credits', async ({ page }) => {
    // Set up mock response for user with low credits
    await mockValidationResponse(page, {
      type: 'credits',
      balance: 0
    });

    // Fill and submit form
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
    await editor.fill('Smith, J. (2023). Test citation. *Journal*, 1(1), 1-10.');

    await page.locator('button[type="submit"]').click();

    // Wait for results to load
    await expect(page.locator('.validation-table-container, .validation-table').first()).toBeVisible({ timeout: 30000 });

    // Verify UserStatus badge has destructive variant (red for 0 credits)
    const userStatusDestructive = page.locator('.user-status');
    await expect(userStatusDestructive).toBeVisible();
    const badgeElementDestructive = userStatusDestructive.locator('div').first();
    await expect(badgeElementDestructive).toHaveClass(/bg-destructive/);
  });

  test('displays free tier status for free users', async ({ page }) => {
    // Set up mock response for free user
    await mockValidationResponse(page, {
      type: 'free',
      validations_used: 5,
      limit: 5
    });

    // Fill and submit form
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
    await editor.fill('Smith, J. (2023). Test citation. *Journal*, 1(1), 1-10.');

    await page.locator('button[type="submit"]').click();

    // Wait for results to load
    await expect(page.locator('.validation-table-container, .validation-table').first()).toBeVisible({ timeout: 30000 });

    // Verify UserStatus badge appears with free tier text
    const userStatus = page.locator('.user-status');
    await expect(userStatus).toBeVisible();
    await expect(userStatus).toContainText('Free tier');

    // Verify it has secondary variant styling (neutral color)
    const badgeElement = userStatus.locator('div').first();
    await expect(badgeElement).toHaveClass(/bg-secondary/);
  });

  test('does not display UserStatus when user_status is null', async ({ page }) => {
    // Set up mock response without user_status
    await page.route('/api/jobs/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'completed',
          results: {
            results: [
              {
                original: 'Smith, J. (2023). Test citation. *Journal*, 1(1), 1-10.',
                source_type: 'journal',
                errors: []
              }
            ]
            // No user_status field
          }
        })
      });
    });

    // Fill and submit form
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible();
    await editor.fill('Smith, J. (2023). Test citation. *Journal*, 1(1), 1-10.');

    await page.locator('button[type="submit"]').click();

    // Wait for results to load
    await expect(page.locator('.validation-table-container, .validation-table').first()).toBeVisible({ timeout: 30000 });

    // Verify UserStatus does NOT appear
    await expect(page.locator('.user-status')).not.toBeVisible();
  });
});

// Mobile viewport tests
test.describe('UserStatus Display - Mobile', () => {
  test.use({
    baseURL: 'http://localhost:5173',
    viewport: { width: 375, height: 667 }
  });

  test('UserStatus badge is visible on mobile', async ({ page }) => {
    // Set up mock response
    await mockValidationResponse(page, {
      type: 'credits',
      balance: 15
    });

    // Wait a bit for mobile layout to settle
    await page.waitForTimeout(2000);

    // Fill and submit form
    const editor = page.locator('.ProseMirror').or(page.locator('[contenteditable="true"]')).or(page.locator('textarea'));
    await expect(editor).toBeVisible({ timeout: 20000 });
    await editor.fill('Smith, J. (2023). Test citation. *Journal*, 1(1), 1-10.');

    await page.locator('button[type="submit"]').click();

    // Wait for results to load
    await expect(page.locator('.validation-table-container, .validation-table').first()).toBeVisible({ timeout: 30000 });

    // Verify UserStatus badge is visible on mobile
    const userStatus = page.locator('.user-status');
    await expect(userStatus).toBeVisible();
    await expect(userStatus).toContainText('15 credits remaining');
  });
});