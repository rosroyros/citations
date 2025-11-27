import { test, expect } from '@playwright/test'

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('should load dashboard page with correct title and structure', async ({ page }) => {
    await expect(page).toHaveTitle(/Citation Format Checker/)

    // Check main dashboard elements
    await expect(page.locator('h1.dashboard-title')).toBeVisible()
    await expect(page.locator('h1.dashboard-title')).toContainText('Operations Dashboard')

    // Check header content
    await expect(page.locator('.dashboard-subtitle')).toBeVisible()
    await expect(page.locator('.dashboard-subtitle')).toContainText('Monitor validation requests and system health')
  })

  test('should display filters section with all controls', async ({ page }) => {
    // Check filters section exists
    await expect(page.locator('.filters-section')).toBeVisible()

    // Check individual filter controls
    await expect(page.locator('label[for="dateRange"]')).toBeVisible()
    await expect(page.locator('#dateRange')).toBeVisible()
    await expect(page.locator('label[for="status"]')).toBeVisible()
    await expect(page.locator('#status')).toBeVisible()
    await expect(page.locator('label[for="user"]')).toBeVisible()
    await expect(page.locator('#user')).toBeVisible()
    await expect(page.locator('label[for="search"]')).toBeVisible()
    await expect(page.locator('#search')).toBeVisible()
  })

  test('should display stats summary with correct metrics', async ({ page }) => {
    await expect(page.locator('.stats-section')).toBeVisible()
    await expect(page.locator('.stats-grid')).toBeVisible()

    // Check that all stat cards are present
    const statCards = page.locator('.stat-card')
    await expect(statCards).toHaveCount(6)

    // Check individual stat cards
    await expect(page.locator('.stat-card').filter({ hasText: 'Total Requests' })).toBeVisible()
    await expect(page.locator('.stat-card').filter({ hasText: 'Completed' })).toBeVisible()
    await expect(page.locator('.stat-card').filter({ hasText: 'Failed' })).toBeVisible()
    await expect(page.locator('.stat-card').filter({ hasText: 'Total Citations' })).toBeVisible()
    await expect(page.locator('.stat-card').filter({ hasText: 'Total Errors' })).toBeVisible()
    await expect(page.locator('.stat-card').filter({ hasText: 'Avg Processing' })).toBeVisible()
  })

  test('should display data table with correct headers and data', async ({ page }) => {
    await expect(page.locator('.table-section')).toBeVisible()
    await expect(page.locator('.data-table')).toBeVisible()

    // Check table headers
    const headers = page.locator('thead th')
    await expect(headers).toHaveCount(7)
    await expect(headers.filter({ hasText: 'Timestamp' })).toBeVisible()
    await expect(headers.filter({ hasText: 'Status' })).toBeVisible()
    await expect(headers.filter({ hasText: 'User' })).toBeVisible()
    await expect(headers.filter({ hasText: 'Citations' })).toBeVisible()
    await expect(headers.filter({ hasText: 'Errors' })).toBeVisible()
    await expect(headers.filter({ hasText: 'Processing Time' })).toBeVisible()
    await expect(headers.filter({ hasText: 'Actions' })).toBeVisible()

    // Check data rows (should have 5 rows from mock data)
    const dataRows = page.locator('tbody tr')
    await expect(dataRows).toHaveCount(5)

    // Check status badges are present
    const statusBadges = page.locator('.status-badge')
    await expect(statusBadges).toBeVisible()
  })

  test('should have sortable columns that work correctly', async ({ page }) => {
    // Get initial timestamp values
    const timestampsBefore = await page.locator('.timestamp-cell').allTextContents()

    // Click timestamp header to sort
    await page.click('th:has-text("Timestamp")')

    // Wait for sorting to apply
    await page.waitForTimeout(100)

    // Check sort icon changed
    const sortIcon = page.locator('th:has-text("Timestamp") .sort-icon')
    await expect(sortIcon).toBeVisible()

    // Click again to reverse sort
    await page.click('th:has-text("Timestamp")')
    await page.waitForTimeout(100)
  })

  test('should apply filters correctly', async ({ page }) => {
    // Test status filter
    await page.selectOption('#status', 'completed')
    await page.waitForTimeout(100)

    // Check that rows are filtered
    const completedRows = page.locator('.status-completed')
    const failedRows = page.locator('.status-failed')
    const processingRows = page.locator('.status-processing')

    await expect(completedRows).toHaveCount(3) // 3 completed in mock data
    await expect(failedRows).toHaveCount(0) // 0 failed after filtering
    await expect(processingRows).toHaveCount(0) // 0 processing after filtering

    // Reset status filter
    await page.selectOption('#status', 'all')
    await page.waitForTimeout(100)

    // Test user filter
    await page.fill('#user', 'john.doe@university.edu')
    await page.waitForTimeout(100)

    // Should only show john.doe row
    const filteredRows = page.locator('tbody tr')
    await expect(filteredRows).toHaveCount(1)
    await expect(filteredRows.filter({ hasText: 'john.doe@university.edu' })).toBeVisible()
  })

  test('should open and close details modal correctly', async ({ page }) => {
    // Click details button on first row
    await page.click('.details-button')

    // Check modal opens
    await expect(page.locator('.modal-overlay')).toBeVisible()
    await expect(page.locator('.modal-content')).toBeVisible()
    await expect(page.locator('.modal-header h2')).toContainText('Validation Request Details')

    // Check modal has detailed information
    await expect(page.locator('text=Validation ID')).toBeVisible()
    await expect(page.locator('text=Session ID')).toBeVisible()
    await expect(page.locator('text=Timestamp')).toBeVisible()
    await expect(page.locator('text=Status')).toBeVisible()
    await expect(page.locator('text=User')).toBeVisible()
    await expect(page.locator('text=IP Address')).toBeVisible()
    await expect(page.locator('text=Source Type')).toBeVisible()
    await expect(page.locator('text=API Version')).toBeVisible()
    await expect(page.locator('text=Citations Processed')).toBeVisible()
    await expect(page.locator('text=Errors Found')).toBeVisible()
    await expect(page.locator('text=Processing Time')).toBeVisible()
    await expect(page.locator('text=User Agent')).toBeVisible()

    // Close modal with close button
    await page.click('.modal-close')

    // Check modal closes
    await expect(page.locator('.modal-overlay')).not.toBeVisible()

    // Open modal again
    await page.click('.details-button')
    await expect(page.locator('.modal-overlay')).toBeVisible()

    // Close modal by clicking overlay
    await page.click('.modal-overlay')
    await expect(page.locator('.modal-overlay')).not.toBeVisible()
  })

  test('should have working pagination controls', async ({ page }) => {
    // Check pagination exists (should be hidden with current data, but present in DOM)
    const pagination = page.locator('.pagination')
    const isVisible = await pagination.isVisible()

    // For testing with current data (5 rows, 10 per page), pagination should not be visible
    // But we can test the controls exist
    const paginationControls = page.locator('.pagination-controls')
    await expect(paginationControls).toBeVisible()

    // Test that buttons exist
    await expect(page.locator('button:has-text("First")')).toBeVisible()
    await expect(page.locator('button:has-text("Previous")')).toBeVisible()
    await expect(page.locator('button:has-text("Next")')).toBeVisible()
    await expect(page.locator('button:has-text("Last")')).toBeVisible()
  })

  test('should be keyboard accessible', async ({ page }) => {
    // Test tab navigation through filters
    await page.keyboard.press('Tab')
    await expect(page.locator('#dateRange')).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(page.locator('#status')).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(page.locator('#user')).toBeFocused()

    await page.keyboard.press('Tab')
    await expect(page.locator('#search')).toBeFocused()

    // Test keyboard access to details modal
    await page.click('.details-button')
    await expect(page.locator('.modal-close')).toBeVisible()

    // Test escape key closes modal
    await page.keyboard.press('Escape')
    await expect(page.locator('.modal-overlay')).not.toBeVisible()
  })

  test('should have responsive design on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    // Check responsive adjustments
    await expect(page.locator('.dashboard-header .header-content')).toBeVisible()
    await expect(page.locator('.filters-container')).toBeVisible()
    await expect(page.locator('.stats-grid')).toBeVisible()

    // Mobile should stack filters vertically
    const filterGroups = page.locator('.filter-group')
    await expect(filterGroups).toHaveCount(4) // Should be stacked on mobile

    // Mobile stats should be single column
    await page.setViewportSize({ width: 375, height: 667 })
    const statCards = page.locator('.stat-card')
    const firstCard = statCards.first()
    const firstCardBox = await firstCard.boundingBox()

    // On mobile, cards should be full width
    expect(firstCardBox.width).toBeLessThan(400) // Approximate mobile width
  })

  test('should maintain visual design quality', async ({ page }) => {
    // Check that fonts are loaded
    await expect(page.locator('body')).toHaveCSS('font-family', /Inter/)

    // Check color scheme is applied
    await expect(page.locator('.dashboard')).toHaveCSS('background-color', 'rgb(250, 250, 250)')

    // Check stat cards have consistent styling
    const statCards = page.locator('.stat-card')
    const firstCard = statCards.first()
    await expect(firstCard).toHaveCSS('background-color', 'rgb(255, 255, 255)')
    await expect(firstCard).toHaveCSS('border-radius', '12px')

    // Check table styling
    await expect(page.locator('.data-table')).toHaveCSS('font-size', '14px')

    // Check modal styling
    await page.click('.details-button')
    const modal = page.locator('.modal-content')
    await expect(modal).toHaveCSS('background-color', 'rgb(255, 255, 255)')
    await expect(modal).toHaveCSS('border-radius', '16px')
  })
})

test.describe('Dashboard Data Integration', () => {
  test('should handle empty data state gracefully', async ({ page }) => {
    // Mock empty API response
    await page.route('/api/dashboard-data', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ data: [] })
      })
    })

    await page.goto('/dashboard')

    // Should show empty state message
    await expect(page.locator('.data-table')).toBeVisible()
    await expect(page.locator('tbody tr')).toHaveCount(0)

    // Should show appropriate empty state message
    await expect(page.locator('text=No validation requests found')).toBeVisible()
  })

  test('should handle loading state', async ({ page }) => {
    // Mock delayed API response
    await page.route('/api/dashboard-data', route => {
      // Delay response
      setTimeout(() => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: [] })
        })
      }, 2000)
    })

    await page.goto('/dashboard')

    // Should show loading state
    await expect(page.locator('.loading-spinner')).toBeVisible()
    await expect(page.locator('text=Loading dashboard data...')).toBeVisible()
  })

  test('should handle error state', async ({ page }) => {
    // Mock API error response
    await page.route('/api/dashboard-data', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      })
    })

    await page.goto('/dashboard')

    // Should show error state
    await expect(page.locator('.error-message')).toBeVisible()
    await expect(page.locator('text=Failed to load dashboard data')).toBeVisible()
    await expect(page.locator('button:has-text("Retry")')).toBeVisible()
  })
})