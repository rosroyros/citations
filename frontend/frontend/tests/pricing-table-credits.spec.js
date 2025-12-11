import { test, expect } from '@playwright/test'

test.describe('PricingTableCredits Component', () => {
  test.beforeEach(async ({ page }) => {
    // Create a simple test page that renders the component
    await page.goto('/test-pricing-table')
  })

  test('renders three pricing cards side by side on desktop', async ({ page }) => {
    // Check all three pricing tiers are visible
    await expect(page.getByText('100 Credits')).toBeVisible()
    await expect(page.getByText('500 Credits')).toBeVisible()
    await expect(page.getByText('2,000 Credits')).toBeVisible()

    // Check pricing is displayed
    await expect(page.getByText('$1.99')).toBeVisible()
    await expect(page.getByText('$4.99')).toBeVisible()
    await expect(page.getByText('$9.99')).toBeVisible()

    // Check price per citation
    await expect(page.getByText('$0.020 per citation')).toBeVisible()
    await expect(page.getByText('$0.010 per citation')).toBeVisible()
    await expect(page.getByText('$0.005 per citation')).toBeVisible()
  })

  test('highlights the middle tier as Best Value', async ({ page }) => {
    const bestValueBadge = page.getByText('Best Value')
    await expect(bestValueBadge).toBeVisible()

    // Verify it's on the 500 credit tier
    const middleCard = page.locator('div').filter({ hasText: '500 Credits' }).first()
    await expect(middleCard.locator('.border-primary')).toHaveClass(/border-2/)
  })

  test('shows correct benefits for each tier', async ({ page }) => {
    // 100 credits benefits
    await expect(page.getByText('100 citation validations')).toBeVisible()
    await expect(page.getByText('Use anytime at your pace')).toBeVisible()

    // 500 credits benefits
    await expect(page.getByText('500 citation validations')).toBeVisible()
    await expect(page.getByText('Best value ($0.01/citation)')).toBeVisible()
    await expect(page.getByText('Export to BibTeX / RIS')).toBeVisible()

    // 2000 credits benefits
    await expect(page.getByText('2,000 citation validations')).toBeVisible()
    await expect(page.getByText('For heavy academic writing')).toBeVisible()
    await expect(page.getByText('Priority support')).toBeVisible()
  })

  test('all buy buttons are clickable', async ({ page }) => {
    // Check all three buttons exist and are clickable
    const buy100Button = page.getByRole('button', { name: 'Buy 100 Credits' })
    const buy500Button = page.getByRole('button', { name: 'Buy 500 Credits' })
    const buy2000Button = page.getByRole('button', { name: 'Buy 2,000 Credits' })

    await expect(buy100Button).toBeVisible()
    await expect(buy500Button).toBeVisible()
    await expect(buy2000Button).toBeVisible()

    // Verify button styles - middle should be solid, others outline
    await expect(buy500Button).toHaveClass(/button-default/)
    await expect(buy100Button).toHaveClass(/button-outline/)
    await expect(buy2000Button).toHaveClass(/button-outline/)
  })

  test('is responsive - stacks cards on mobile', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    // Verify layout changes to single column
    const gridContainer = page.locator('.grid').first()
    await expect(gridContainer).toHaveClass(/grid-cols-1/)

    // All cards should still be visible
    await expect(page.getByText('100 Credits')).toBeVisible()
    await expect(page.getByText('500 Credits')).toBeVisible()
    await expect(page.getByText('2,000 Credits')).toBeVisible()
  })

  test('maintains layout on desktop', async ({ page }) => {
    // Test desktop viewport
    await page.setViewportSize({ width: 1200, height: 800 })

    // Verify three-column layout
    const gridContainer = page.locator('.grid').first()
    await expect(gridContainer).toHaveClass(/md:grid-cols-3/)
  })

  test('checkmark icons are visible', async ({ page }) => {
    // Count checkmark SVGs
    const checkmarks = page.locator('svg[aria-hidden="true"]')
    const checkmarkCount = await checkmarks.count()

    // Should have multiple checkmarks (at least 3 per tier = 9 total)
    expect(checkmarkCount).toBeGreaterThanOrEqual(9)
  })

  test('clicking buy buttons triggers correct handler', async ({ page }) => {
    // Listen for console logs to verify click handlers
    const consoleMessages = []
    page.on('console', msg => {
      consoleMessages.push(msg.text())
    })

    await page.getByRole('button', { name: 'Buy 100 Credits' }).click()

    // Check if onSelectProduct was called (console should show the alert)
    expect(consoleMessages.some(msg => msg.includes('Selected: 817c70f8-6cd1-4bdc-aa80-dd0a43e69a5e'))).toBeTruthy()
  })
})