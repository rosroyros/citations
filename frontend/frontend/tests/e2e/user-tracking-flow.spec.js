/**
 * End-to-End Tests for Complete User Tracking Flow
 * Tests that verify the user tracking system works correctly across all user types
 */

import { test, expect } from '@playwright/test';
import {
  TEST_CONFIG,
  setupAnalyticsCapture,
  buildTestUrl,
  printEventSummary
} from '../analytics/helpers.js';

test.describe('User Tracking - End-to-End Flow', () => {
  let capturedRequests;

  test.beforeEach(async ({ page, context }) => {
    // Setup analytics request interception
    capturedRequests = setupAnalyticsCapture(page);

    // Clear cookies for clean test state
    await context.clearCookies();

    // Create a new context for each test to ensure isolation
    await context.addInitScript(() => {
      // Clear localStorage if possible
      try {
        localStorage.clear();
        sessionStorage.clear();
      } catch (e) {
        // Ignore localStorage access errors
      }
    });
  });

  test('RED: should track free user across multiple sessions with persistent UUID', async ({ page, context }) => {
    console.log('🧪 Testing free user tracking across sessions...');

    // Navigate to home page as a new free user
    const testUrl = buildTestUrl('/');
    await page.goto(testUrl);
    await page.waitForLoadState('networkidle');

    // Wait for initial page view analytics
    await page.waitForTimeout(2000);

    // Start a citation validation to trigger user tracking
    await page.fill('textarea, input[type="text"]', 'Smith, J. (2023). Example citation. Journal Name, 15(2), 123-145.');
    await page.waitForTimeout(1000);

    // Submit the validation
    await page.click('button[type="submit"]');
    await page.waitForTimeout(5000);

    // Extract the free user ID from localStorage
    let freeUserId = await page.evaluate(() => {
      try {
        const freeUserId = localStorage.getItem('freeUserId');
        return freeUserId;
      } catch (e) {
        return null;
      }
    });

    console.log(`🆔 Free User ID from session 1: ${freeUserId}`);

    // Verify free user ID was generated
    expect(freeUserId).toBeTruthy();
    expect(freeUserId).toMatch(/^[a-f0-9-]{36}$/); // UUID format

    // Capture network requests from first session
    const firstSessionRequests = capturedRequests.slice();

    // Check that X-Free-User-ID header was sent in validation requests
    let validationRequestsWithFreeUserId = 0;
    for (const request of firstSessionRequests) {
      const headers = request.headers();
      if (headers['x-free-user-id']) {
        validationRequestsWithFreeUserId++;
        console.log(`📤 Found X-Free-User-ID header: ${headers['x-free-user-id']}`);
      }
    }

    console.log(`📊 Session 1: Found ${validationRequestsWithFreeUserId} requests with X-Free-User-ID header`);

    // Simulate closing browser and returning in new session
    console.log('🔄 Simulating new browser session...');

    // Create new page context (simulates new browser session)
    const newPage = await context.newPage();

    // Navigate back to site without clearing localStorage (simulates returning user)
    await newPage.goto(testUrl);
    await newPage.waitForLoadState('networkidle');
    await newPage.waitForTimeout(2000);

    // Check that free user ID persists in new session
    let persistentFreeUserId = await newPage.evaluate(() => {
      try {
        const freeUserId = localStorage.getItem('freeUserId');
        return freeUserId;
      } catch (e) {
        return null;
      }
    });

    console.log(`🆔 Free User ID from session 2: ${persistentFreeUserId}`);

    // Verify same UUID is used
    expect(persistentFreeUserId).toBe(freeUserId);

    // Perform another validation in new session
    await newPage.fill('textarea, input[type="text"]', 'Doe, J. (2023). Another citation. Test Journal, 10(1), 45-67.');
    await newPage.waitForTimeout(1000);
    await newPage.click('button[type="submit"]');
    await newPage.waitForTimeout(5000);

    // THIS SHOULD FAIL because the complete dashboard user tracking integration is not yet implemented
    // We expect the dashboard to show user IDs for free users, but it won't yet

    // Navigate to dashboard to check user tracking display
    await newPage.goto('/dashboard');
    await newPage.waitForLoadState('networkidle');
    await newPage.waitForTimeout(3000);

    // Look for user ID display in dashboard
    const userColumnVisible = await newPage.locator('th:has-text("User")').isVisible();
    expect(userColumnVisible).toBe(true);

    // Check if any rows show the free user ID
    const freeUserIdInDashboard = await newPage.locator(`text=${freeUserId}`).isVisible();

    // THIS SHOULD FAIL because dashboard doesn't yet display free user IDs
    expect(freeUserIdInDashboard).toBe(true, `Expected to find free user ID ${freeUserId} in dashboard`);

    console.log('✅ Free user tracking across sessions test completed!');
    console.log(`   🆔 Free User ID: ${freeUserId}`);
    console.log(`   📊 Session 1 requests with user ID: ${validationRequestsWithFreeUserId}`);
    console.log(`   🔄 Persistent ID in session 2: ${persistentFreeUserId === freeUserId ? 'YES' : 'NO'}`);
    console.log(`   📋 Dashboard shows user ID: ${freeUserIdInDashboard ? 'YES' : 'NO'}`);
  });

  test('RED: should track paid user with token-based identification', async ({ page, context }) => {
    console.log('🧪 Testing paid user tracking with tokens...');

    // Set up paid user session by setting auth token
    const paidUserToken = 'test-paid-user-token-12345';
    await page.addInitScript((token) => {
      localStorage.setItem('userToken', token);
    }, paidUserToken);

    // Navigate to home page as paid user
    const testUrl = buildTestUrl('/');
    await page.goto(testUrl);
    await page.waitForLoadState('networkidle');

    // Start a citation validation
    await page.fill('textarea, input[type="text"]', 'Johnson, M. (2023). Paid user citation. Premium Journal, 20(3), 300-320.');
    await page.waitForTimeout(1000);

    // Submit the validation
    await page.click('button[type="submit"]');
    await page.waitForTimeout(5000);

    // Check that X-User-Token header was sent (not X-Free-User-ID)
    let requestsWithPaidToken = 0;
    let requestsWithFreeUserId = 0;

    for (const request of capturedRequests) {
      const headers = request.headers();
      if (headers['x-user-token'] === paidUserToken) {
        requestsWithPaidToken++;
      }
      if (headers['x-free-user-id']) {
        requestsWithFreeUserId++;
      }
    }

    console.log(`📊 Paid user requests with X-User-Token: ${requestsWithPaidToken}`);
    console.log(`📊 Paid user requests with X-Free-User-ID: ${requestsWithFreeUserId}`);

    expect(requestsWithPaidToken).toBeGreaterThan(0);
    expect(requestsWithFreeUserId).toBe(0); // Paid users should not send free user ID

    // Navigate to dashboard to check paid user tracking
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Look for paid user identification in dashboard
    // THIS SHOULD FAIL because paid user dashboard display is not fully implemented
    const paidUserTokenVisible = await page.locator(`text=${paidUserToken.substring(0, 8)}`).isVisible();
    expect(paidUserTokenVisible).toBe(true, `Expected to find paid user token prefix ${paidUserToken.substring(0, 8)} in dashboard`);

    console.log('✅ Paid user tracking test completed!');
    console.log(`   🪙 Paid User Token: ${paidUserToken}`);
    console.log(`   📊 Requests with token: ${requestsWithPaidToken}`);
    console.log(`   📋 Dashboard shows token: ${paidUserTokenVisible ? 'YES' : 'NO'}`);
  });

  test('RED: should handle user conversion from free to paid correctly', async ({ page, context }) => {
    console.log('🧪 Testing user conversion free → paid...');

    // Start as free user
    const testUrl = buildTestUrl('/');
    await page.goto(testUrl);
    await page.waitForLoadState('networkidle');

    // Generate free user ID by starting validation
    await page.fill('textarea, input[type="text"]', 'Free user citation. Test Journal, 5(1), 10-20.');
    await page.waitForTimeout(1000);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(5000);

    // Get free user ID
    const freeUserId = await page.evaluate(() => {
      try {
        return localStorage.getItem('freeUserId');
      } catch (e) {
        return null;
      }
    });

    expect(freeUserId).toBeTruthy();
    console.log(`🆔 Free User ID before conversion: ${freeUserId}`);

    // Simulate payment completion (this should trigger free user ID cleanup)
    await page.evaluate(() => {
      // Simulate the payment success callback that should clear free user ID
      if (window.clearFreeUserIdOnPaymentSuccess) {
        window.clearFreeUserIdOnPaymentSuccess();
      }
    });

    // Check that free user ID was cleared
    const freeUserIdAfterPayment = await page.evaluate(() => {
      try {
        return localStorage.getItem('freeUserId');
      } catch (e) {
        return null;
      }
    });

    // THIS SHOULD FAIL because payment cleanup might not be fully implemented
    expect(freeUserIdAfterPayment).toBeNull();

    // Set paid user token
    const paidUserToken = 'converted-user-token-67890';
    await page.evaluate((token) => {
      localStorage.setItem('userToken', token);
    }, paidUserToken);

    // Perform validation as paid user
    await page.fill('textarea, input[type="text"]', 'Converted user citation. Premium Journal, 15(2), 200-220.');
    await page.waitForTimeout(1000);
    await page.click('button[type="submit"]');
    await page.waitForTimeout(5000);

    // Verify requests use paid token, not free user ID
    let paidTokenRequests = 0;
    let freeUserIdRequests = 0;

    for (const request of capturedRequests) {
      const headers = request.headers();
      if (headers['x-user-token'] === paidUserToken) {
        paidTokenRequests++;
      }
      if (headers['x-free-user-id']) {
        freeUserIdRequests++;
      }
    }

    expect(paidTokenRequests).toBeGreaterThan(0);
    expect(freeUserIdRequests).toBe(0);

    console.log('✅ User conversion test completed!');
    console.log(`   🆔 Free User ID (before): ${freeUserId}`);
    console.log(`   🧹 Free User ID (after): ${freeUserIdAfterPayment}`);
    console.log(`   🪙 Paid User Token: ${paidUserToken}`);
    console.log(`   📊 Paid requests: ${paidTokenRequests}, Free requests: ${freeUserIdRequests}`);
  });

  test('RED: should display user tracking information in dashboard with filtering', async ({ page }) => {
    console.log('🧪 Testing dashboard user tracking display...');

    // Navigate to dashboard
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Check that User column exists in the data table
    const userColumnHeader = page.locator('th:has-text("User")');
    await expect(userColumnHeader).toBeVisible();

    // Check that user filter exists
    const userFilter = page.locator('#user');
    await expect(userFilter).toBeVisible();
    await expect(userFilter.getAttribute('placeholder')).resolves.toContain('Filter by user');

    // Mock dashboard data to include user information
    await page.route('/api/dashboard-data', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [
            {
              id: '1',
              timestamp: '2025-12-03T10:00:00Z',
              status: 'completed',
              user: 'free-user-12345',
              user_type: 'free',
              citations: 5,
              errors: 0,
              processing_time: 2.5
            },
            {
              id: '2',
              timestamp: '2025-12-03T10:05:00Z',
              status: 'completed',
              user: 'abc12345',
              user_type: 'paid',
              citations: 3,
              errors: 1,
              processing_time: 1.8
            },
            {
              id: '3',
              timestamp: '2025-12-03T10:10:00Z',
              status: 'failed',
              user: 'free-user-67890',
              user_type: 'free',
              citations: 2,
              errors: 2,
              processing_time: 0.8
            }
          ]
        })
      });
    });

    // Reload dashboard to get mock data
    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Check that user IDs are displayed in the table
    await expect(page.locator('text=free-user-12345')).toBeVisible();
    await expect(page.locator('text=abc12345')).toBeVisible();
    await expect(page.locator('text=free-user-67890')).toBeVisible();

    // Test user filtering functionality
    await page.fill('#user', 'free-user-12345');
    await page.waitForTimeout(1000);

    // Should only show the filtered user's data
    const visibleRows = page.locator('tbody tr');
    await expect(visibleRows).toHaveCount(1);
    await expect(visibleRows.locator('text=free-user-12345')).toBeVisible();

    // Test filtering by paid user token
    await page.fill('#user', 'abc12345');
    await page.waitForTimeout(1000);

    await expect(visibleRows).toHaveCount(1);
    await expect(visibleRows.locator('text=abc12345')).toBeVisible();

    // Test clearing filter
    await page.fill('#user', '');
    await page.waitForTimeout(1000);

    // Should show all rows again
    const allRows = page.locator('tbody tr');
    await expect(allRows).toHaveCount(3);

    console.log('✅ Dashboard user tracking display test completed!');
  });

  test('RED: should maintain user privacy (IP addresses hidden from non-admin users)', async ({ page }) => {
    console.log('🧪 Testing user privacy controls...');

    // Navigate to dashboard as regular user
    await page.goto('/dashboard');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Mock dashboard data with IP addresses
    await page.route('/api/dashboard-data', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [
            {
              id: '1',
              timestamp: '2025-12-03T10:00:00Z',
              status: 'completed',
              user: 'free-user-12345',
              user_type: 'free',
              ip_address: '192.168.1.100', // This should be hidden from regular users
              citations: 5,
              errors: 0,
              processing_time: 2.5
            }
          ]
        })
      });
    });

    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Click on details button to open modal
    await page.click('.details-button');
    await page.waitForTimeout(1000);

    // Check that modal opens
    await expect(page.locator('.modal-overlay')).toBeVisible();

    // IP address should NOT be visible to regular users
    const ipVisible = await page.locator('text=192.168.1.100').isVisible();

    // THIS SHOULD PASS - IP should be hidden from regular users
    expect(ipVisible).toBe(false);

    // But user ID should be visible
    const userIdVisible = await page.locator('text=free-user-12345').isVisible();
    expect(userIdVisible).toBe(true);

    // Close modal
    await page.click('.modal-close');

    console.log('✅ User privacy test completed!');
    console.log(`   🔒 IP Address visible to regular user: ${ipVisible ? 'YES' : 'NO'}`);
    console.log(`   👤 User ID visible to regular user: ${userIdVisible ? 'YES' : 'NO'}`);
  });
});