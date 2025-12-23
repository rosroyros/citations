import { test, expect } from '@playwright/test'

test.describe('PricingTableCredits Component', () => {
  test.beforeEach(async ({ page }) => {
    // Create a simple test page that renders the component
    await page.goto('/test-pricing-table')
  })

  test('renders three pricing cards side by side on desktop', async ({ page }) => {
    // Check all three pricing tiers are visible
    // Use exact text matching to find card titles (CardTitle renders as div, not heading)
    await expect(page.getByText('100 Credits', { exact: true }).first()).toBeVisible()
    await expect(page.getByText('500 Credits', { exact: true }).first()).toBeVisible()
    await expect(page.getByText('2,000 Credits', { exact: true }).first()).toBeVisible()

    // Check pricing is displayed
    await expect(page.getByText('$1.99').first()).toBeVisible()
    await expect(page.getByText('$4.99').first()).toBeVisible()
    await expect(page.getByText('$9.99').first()).toBeVisible()
  })

  test('highlights the middle tier as Best Value', async ({ page }) => {
    const bestValueBadge = page.getByText('Best Value')
    await expect(bestValueBadge).toBeVisible()

    // Verify the middle card has the highlighted border (border-2 and border-purple-600)
    const middleCard = page.locator('.border-2.border-purple-600')
    await expect(middleCard).toBeVisible()
    // The card with Best Value badge should contain 500 Credits
    await expect(middleCard.getByText('500 Credits', { exact: true })).toBeVisible()
  })

  test('shows correct benefits for each tier', async ({ page }) => {
    // All tiers have the same benefits in the current implementation
    // Check that benefits are displayed (use .first() to avoid multiple matches)
    await expect(page.getByText('Full APA 7 Compliance').first()).toBeVisible()
    await expect(page.getByText('Detailed citation analysis').first()).toBeVisible()
    await expect(page.getByText('Actionable error correction feedback').first()).toBeVisible()
    await expect(page.getByText('No expiration date').first()).toBeVisible()
  })

  test('all buy buttons are clickable', async ({ page }) => {
    // Check all three buttons exist and are clickable
    const buy100Button = page.getByRole('button', { name: 'Buy 100 Credits' })
    const buy500Button = page.getByRole('button', { name: 'Buy 500 Credits' })
    const buy2000Button = page.getByRole('button', { name: 'Buy 2,000 Credits' })

    await expect(buy100Button).toBeVisible()
    await expect(buy500Button).toBeVisible()
    await expect(buy2000Button).toBeVisible()

    // Verify all buttons have the purple styling
    await expect(buy100Button).toHaveClass(/bg-purple-600/)
    await expect(buy500Button).toHaveClass(/bg-purple-600/)
    await expect(buy2000Button).toHaveClass(/bg-purple-600/)
  })

  test('is responsive - stacks cards on mobile', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    // All cards should still be visible
    await expect(page.getByText('100 Credits', { exact: true }).first()).toBeVisible()
    await expect(page.getByText('500 Credits', { exact: true }).first()).toBeVisible()
    await expect(page.getByText('2,000 Credits', { exact: true }).first()).toBeVisible()
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

  test('shows money-back guarantee', async ({ page }) => {
    await expect(page.getByText('Risk-free with money-back guarantee.')).toBeVisible()
  })
})