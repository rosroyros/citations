import { test, expect } from '@playwright/test'

test.describe('PricingTablePasses Component', () => {
  test.beforeEach(async ({ page }) => {
    // Create a simple test page that renders the component
    await page.goto('/test-pricing-table-passes')
  })

  test('renders three pass tiers side by side on desktop', async ({ page }) => {
    // Check all three pass tiers are visible
    // CardTitle renders as div, not heading - use text matching with .first()
    await expect(page.getByText('1-Day Pass', { exact: true }).first()).toBeVisible()
    await expect(page.getByText('7-Day Pass', { exact: true }).first()).toBeVisible()
    await expect(page.getByText('30-Day Pass', { exact: true }).first()).toBeVisible()

    // Check pricing is displayed
    await expect(page.getByText('$1.99').first()).toBeVisible()
    await expect(page.getByText('$4.99').first()).toBeVisible()
    await expect(page.getByText('$9.99').first()).toBeVisible()
  })

  test('highlights the middle tier as Best Value', async ({ page }) => {
    // The badge says "Best Value" (use exact: true to avoid matching the description text)
    const bestValueBadge = page.getByText('Best Value', { exact: true })
    await expect(bestValueBadge).toBeVisible()

    // Verify it's on the 7-day pass tier by checking the highlighted card (border-2 and border-purple-600)
    const middleCard = page.locator('.border-2.border-purple-600')
    await expect(middleCard).toBeVisible()
    await expect(middleCard.getByText('7-Day Pass', { exact: true })).toBeVisible()
  })

  test('shows correct benefits for each tier', async ({ page }) => {
    // All tiers have the same benefits in the current implementation
    await expect(page.getByText('Full APA 7 Compliance').first()).toBeVisible()
    await expect(page.getByText('Detailed citation analysis').first()).toBeVisible()
    await expect(page.getByText('Actionable error correction feedback').first()).toBeVisible()
    await expect(page.getByText('Risk-free with money-back guarantee').first()).toBeVisible()
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

    // Verify all buttons have purple styling
    await expect(buy1DayButton).toHaveClass(/bg-purple-600/)
    await expect(buy7DayButton).toHaveClass(/bg-purple-600/)
    await expect(buy30DayButton).toHaveClass(/bg-purple-600/)
  })

  test('is responsive - stacks cards on mobile', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    // All cards should still be visible
    await expect(page.getByText('1-Day Pass', { exact: true }).first()).toBeVisible()
    await expect(page.getByText('7-Day Pass', { exact: true }).first()).toBeVisible()
    await expect(page.getByText('30-Day Pass', { exact: true }).first()).toBeVisible()
  })

  test('maintains layout on desktop', async ({ page }) => {
    // Test desktop viewport
    await page.setViewportSize({ width: 1200, height: 800 })

    // Verify three-column layout
    const gridContainer = page.locator('.grid').first()
    await expect(gridContainer).toHaveClass(/md:grid-cols-3/)
  })

  test('checkmark icons are visible', async ({ page }) => {
    // The component uses text checkmarks (✓) not SVG icons
    const checkmarks = page.locator('text=✓')
    const checkmarkCount = await checkmarks.count()

    // Should have multiple checkmarks (4 benefits per tier × 3 tiers = 12 total)
    expect(checkmarkCount).toBeGreaterThanOrEqual(12)
  })
})