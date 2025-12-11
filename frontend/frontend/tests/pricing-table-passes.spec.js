import { test, expect } from '@playwright/test'

test.describe('PricingTablePasses Component', () => {
  test.beforeEach(async ({ page }) => {
    // Create a simple test page that renders the component
    await page.goto('/test-pricing-table-passes')
  })

  test('renders three pass tiers side by side on desktop', async ({ page }) => {
    // Check all three pass tiers are visible as headings
    await expect(page.getByRole('heading', { name: '1-Day Pass' })).toBeVisible()
    await expect(page.getByRole('heading', { name: '7-Day Pass' })).toBeVisible()
    await expect(page.getByRole('heading', { name: '30-Day Pass' })).toBeVisible()

    // Check pricing is displayed
    await expect(page.getByText('$1.99')).toBeVisible()
    await expect(page.getByText('$4.99')).toBeVisible()
    await expect(page.getByText('$9.99')).toBeVisible()

    // Check price per day
    await expect(page.getByText('$1.99 per day')).toBeVisible()
    await expect(page.getByText('$0.71 per day')).toBeVisible()
    await expect(page.getByText('$0.33 per day')).toBeVisible()
  })

  test('highlights the middle tier as Recommended', async ({ page }) => {
    const recommendedBadge = page.getByText('Recommended')
    await expect(recommendedBadge).toBeVisible()

    // Verify it's on the 7-day pass tier
    const middleCard = page.locator('div').filter({ hasText: '7-Day Pass' }).first()
    await expect(middleCard.locator('.border-primary')).toHaveClass(/border-2/)
  })

  test('shows correct benefits for each tier', async ({ page }) => {
    // 1-day pass benefits
    const oneDayCard = page.locator('.border').filter({ hasText: '1-Day Pass' }).first()
    await expect(oneDayCard.getByText('Unlimited validations for 24 hours')).toBeVisible()
    await expect(oneDayCard.getByText('Up to 1,000 citations per day')).toBeVisible()
    await expect(oneDayCard.getByText('Perfect for finishing a paper')).toBeVisible()

    // 7-day pass benefits
    const sevenDayCard = page.locator('.border').filter({ hasText: '7-Day Pass' }).first()
    await expect(sevenDayCard.getByText('7 days of unlimited access')).toBeVisible()
    await expect(sevenDayCard.getByText('Best value ($0.71/day)')).toBeVisible()
    await expect(sevenDayCard.getByText('Export to BibTeX / RIS')).toBeVisible()

    // 30-day pass benefits
    const thirtyDayCard = page.locator('.border').filter({ hasText: '30-Day Pass' }).first()
    await expect(thirtyDayCard.getByText('30 days of unlimited access')).toBeVisible()
    await expect(thirtyDayCard.getByText('Lowest daily cost ($0.33/day)')).toBeVisible()
    await expect(thirtyDayCard.getByText('Perfect for ongoing research')).toBeVisible()
  })

  test('shows fair use disclaimer below cards', async ({ page }) => {
    await expect(page.getByText('Fair use: 1,000 citations per day. Passes can be extended anytime.')).toBeVisible()
  })

  test('all buy buttons are clickable', async ({ page }) => {
    // Check all three buttons exist and are clickable
    const buy1DayButton = page.getByRole('button', { name: 'Buy 1-Day Pass' })
    const buy7DayButton = page.getByRole('button', { name: 'Buy 7-Day Pass' })
    const buy30DayButton = page.getByRole('button', { name: 'Buy 30-Day Pass' })

    await expect(buy1DayButton).toBeVisible()
    await expect(buy7DayButton).toBeVisible()
    await expect(buy30DayButton).toBeVisible()

    // Verify button styles - middle should be solid (bg-primary), others outline (border)
    await expect(buy7DayButton).toHaveClass(/bg-primary/)
    await expect(buy1DayButton).toHaveClass(/border/)
    await expect(buy30DayButton).toHaveClass(/border/)
  })

  test('is responsive - stacks cards on mobile', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    // Verify layout changes to single column
    const gridContainer = page.locator('.grid').first()
    await expect(gridContainer).toHaveClass(/grid-cols-1/)

    // All cards should still be visible
    await expect(page.getByRole('heading', { name: '1-Day Pass' })).toBeVisible()
    await expect(page.getByRole('heading', { name: '7-Day Pass' })).toBeVisible()
    await expect(page.getByRole('heading', { name: '30-Day Pass' })).toBeVisible()
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

    // Should have multiple checkmarks (at least 4 per tier = 12 total)
    expect(checkmarkCount).toBeGreaterThanOrEqual(12)
  })

  test('clicking buy buttons triggers correct handler', async ({ page }) => {
    // Listen for console logs to verify click handlers
    const consoleMessages = []
    page.on('console', msg => {
      consoleMessages.push(msg.text())
    })

    // Listen for dialogs (alerts)
    let alertText = ''
    page.on('dialog', dialog => {
      alertText = dialog.message()
      dialog.accept()
    })

    await page.getByRole('button', { name: 'Buy 1-Day Pass' }).click()

    // Check if onSelectProduct was called (either via alert or console)
    const hasAlert = alertText.includes('Selected: prod_pass_1day (Variant: 2)')
    const hasConsole = consoleMessages.some(msg => msg.includes('Selected: prod_pass_1day'))
    expect(hasAlert || hasConsole).toBeTruthy()
  })

  test('all cards mention 1000 citations per day limit', async ({ page }) => {
    // Get the specific card elements
    const oneDayCard = page.locator('.border').filter({ hasText: '1-Day Pass' }).first()
    const sevenDayCard = page.locator('.border').filter({ hasText: '7-Day Pass' }).first()
    const thirtyDayCard = page.locator('.border').filter({ hasText: '30-Day Pass' }).first()

    // Each card should mention "1,000 citations per day"
    await expect(oneDayCard.getByText('Up to 1,000 citations per day')).toBeVisible()
    await expect(sevenDayCard.getByText('Up to 1,000 citations per day')).toBeVisible()
    await expect(thirtyDayCard.getByText('Up to 1,000 citations per day')).toBeVisible()
  })
})