const { test, expect } = require('@playwright/test');

test.describe('Dashboard Upgrade Funnel Visualization', () => {
  test.beforeEach(async ({ page }) => {
    // Mock the dashboard API endpoint with test data
    await page.route('/api/validations*', async route => {
      const mockData = {
        validations: [
          {
            job_id: 'test-job-no-upgrade',
            created_at: '2025-12-06T10:00:00Z',
            duration_seconds: 5.2,
            citation_count: 3,
            token_usage_total: 1500,
            user_type: 'free',
            free_user_id: 'free-user-123',
            paid_user_id: null,
            status: 'completed',
            results_gated: false,
            results_revealed_at: null,
            upgrade_state: null
          },
          {
            job_id: 'test-job-gated',
            created_at: '2025-12-06T10:05:00Z',
            duration_seconds: 7.8,
            citation_count: 5,
            token_usage_total: 2300,
            user_type: 'free',
            free_user_id: 'free-user-456',
            paid_user_id: null,
            status: 'completed',
            results_gated: true,
            results_revealed_at: null,
            upgrade_state: 'results_gated'
          },
          {
            job_id: 'test-job-initiated',
            created_at: '2025-12-06T10:10:00Z',
            duration_seconds: 6.1,
            citation_count: 4,
            token_usage_total: 1900,
            user_type: 'free',
            free_user_id: 'free-user-789',
            paid_user_id: null,
            status: 'completed',
            results_gated: true,
            results_revealed_at: null,
            upgrade_state: 'results_gated,upgrade_initiated'
          },
          {
            job_id: 'test-job-completed',
            created_at: '2025-12-06T10:15:00Z',
            duration_seconds: 8.5,
            citation_count: 6,
            token_usage_total: 2800,
            user_type: 'free',
            free_user_id: 'free-user-012',
            paid_user_id: null,
            status: 'completed',
            results_gated: true,
            results_revealed_at: null,
            upgrade_state: 'results_gated,upgrade_initiated,upgrade_completed'
          },
          {
            job_id: 'test-job-revealed',
            created_at: '2025-12-06T10:20:00Z',
            duration_seconds: 9.2,
            citation_count: 7,
            token_usage_total: 3200,
            user_type: 'paid',
            free_user_id: null,
            paid_user_id: 'paid-user-345',
            status: 'completed',
            results_gated: true,
            results_revealed_at: '2025-12-06T10:22:00Z',
            upgrade_state: 'results_gated,upgrade_initiated,upgrade_completed,results_revealed'
          }
        ],
        total: 5
      };
      await route.fulfill({
        status: 200,
        body: JSON.stringify(mockData),
        headers: { 'content-type': 'application/json' }
      });
    });

    // Mock stats endpoint
    await page.route('/api/stats*', async route => {
      await route.fulfill({
        status: 200,
        body: JSON.stringify({
          total_validations: 100,
          completed: 95,
          failed: 5,
          avg_duration_seconds: 6.5,
          avg_citations_per_validation: 4.2
        }),
        headers: { 'content-type': 'application/json' }
      });
    });

    // Navigate to dashboard
    await page.goto('http://localhost:4646');
    await page.waitForLoadState('networkidle');
  });

  test('should display upgrade funnel column in table', async ({ page }) => {
    // Check that the Upgrade column exists
    const upgradeColumn = page.locator('th:has-text("Upgrade")');
    await expect(upgradeColumn).toBeVisible();

    // Check that column is sortable
    await expect(upgradeColumn).toHaveClass(/sortable/);
  });

  test('should display "-" for null upgrade_state', async ({ page }) => {
    // Find the row with no upgrade state
    const row = page.locator('tr:has-text("test-job-no-upgrade")');
    await expect(row).toBeVisible();

    // Check that upgrade cell shows "-"
    const upgradeCell = row.locator('td:nth-child(10)'); // 10th column is Upgrade
    await expect(upgradeCell).toHaveText('-');
  });

  test('should show all 4 icons with correct states for gated results', async ({ page }) => {
    // Find the row with gated results
    const row = page.locator('tr:has-text("test-job-gated")');
    await expect(row).toBeVisible();

    // Get the upgrade cell
    const upgradeCell = row.locator('td:nth-child(10)');

    // Check that all 4 icons are present
    const icons = upgradeCell.locator('.upgrade-icon');
    await expect(icons).toHaveCount(4);

    // Check first icon (results_gated) is active (not grayed out)
    const firstIcon = icons.first();
    await expect(firstIcon).toHaveText('🔒');
    await expect(firstIcon).toHaveClass(/upgrade-results_gated/);

    // Check other icons are grayed out
    for (let i = 1; i < 4; i++) {
      const icon = icons.nth(i);
      await expect(icon).not.toHaveClass(/upgrade-/);
    }
  });

  test('should show correct progression for each upgrade state', async ({ page }) => {
    const testCases = [
      {
        jobId: 'test-job-gated',
        state: 'results_gated',
        activeIcons: 1,
        expectedIcons: ['🔒', '🛒', '💳', '✅']
      },
      {
        jobId: 'test-job-initiated',
        state: 'results_gated,upgrade_initiated',
        activeIcons: 2,
        expectedIcons: ['🔒', '🛒', '💳', '✅']
      },
      {
        jobId: 'test-job-completed',
        state: 'results_gated,upgrade_initiated,upgrade_completed',
        activeIcons: 3,
        expectedIcons: ['🔒', '🛒', '💳', '✅']
      },
      {
        jobId: 'test-job-revealed',
        state: 'results_gated,upgrade_initiated,upgrade_completed,results_revealed',
        activeIcons: 4,
        expectedIcons: ['🔒', '🛒', '💳', '✅']
      }
    ];

    for (const testCase of testCases) {
      const row = page.locator(`tr:has-text("${testCase.jobId}")`);
      await expect(row).toBeVisible();

      const upgradeCell = row.locator('td:nth-child(10)');
      const icons = upgradeCell.locator('.upgrade-icon');

      // Check all 4 icons are present
      await expect(icons).toHaveCount(4);

      // Check icon order
      for (let i = 0; i < 4; i++) {
        await expect(icons.nth(i)).toHaveText(testCase.expectedIcons[i]);
      }

      // Check number of active icons
      let activeCount = 0;
      for (let i = 0; i < 4; i++) {
        const icon = icons.nth(i);
        const hasActiveClass = await icon.evaluate(el => {
          return el.classList.contains('upgrade-results_gated') ||
                 el.classList.contains('upgrade-upgrade_initiated') ||
                 el.classList.contains('upgrade-upgrade_completed') ||
                 el.classList.contains('upgrade-results_revealed');
        });
        if (hasActiveClass) activeCount++;
      }

      expect(activeCount).toBe(testCase.activeIcons);
    }
  });

  test('should show tooltips on hover', async ({ page }) => {
    const row = page.locator('tr:has-text("test-job-gated")');
    const upgradeCell = row.locator('td:nth-child(10)');
    const firstIcon = upgradeCell.locator('.upgrade-icon').first();

    // Hover over the first icon
    await firstIcon.hover();

    // Check tooltip (title attribute)
    await expect(firstIcon).toHaveAttribute('title', 'Results gated');
  });

  test('should highlight icons on hover', async ({ page }) => {
    const row = page.locator('tr:has-text("test-job-gated")');
    const upgradeCell = row.locator('td:nth-child(10)');
    const grayedIcon = upgradeCell.locator('.upgrade-icon').nth(1); // Second icon should be grayed

    // Get initial opacity
    const initialOpacity = await grayedIcon.evaluate(el => {
      return window.getComputedStyle(el).opacity;
    });
    expect(parseFloat(initialOpacity)).toBeLessThan(1);

    // Hover over the icon
    await grayedIcon.hover();

    // Check that opacity becomes 1 on hover
    const hoverOpacity = await grayedIcon.evaluate(el => {
      return window.getComputedStyle(el).opacity;
    });
    expect(parseFloat(hoverOpacity)).toBe(1);
  });
});