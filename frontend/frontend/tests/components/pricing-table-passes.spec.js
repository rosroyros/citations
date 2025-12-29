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

    // Check pricing is displayed (discounted prices)
    await expect(page.getByText('$1.99').first()).toBeVisible()
    await expect(page.getByText('$4.99').first()).toBeVisible()
    await expect(page.getByText('$9.99').first()).toBeVisible()
  })

  test('highlights the middle tier as Most Popular', async ({ page }) => {
    // The badge says "Most Popular" (promo feature update)
    const mostPopularBadge = page.getByText('Most Popular', { exact: true })
    await expect(mostPopularBadge).toBeVisible()

    // Verify it's on the 7-day pass tier by checking the highlighted card (border-2 and border-purple-600)
    const middleCard = page.locator('.border-2.border-purple-600')
    await expect(middleCard).toBeVisible()
    await expect(middleCard.getByText('7-Day Pass', { exact: true })).toBeVisible()
  })

  test('shows correct subtitles for each tier', async ({ page }) => {
    // Updated subtitles from promo feature
    await expect(page.getByText('Finish a paper tonight')).toBeVisible()
    await expect(page.getByText('Best for assignment week')).toBeVisible()
    await expect(page.getByText('For the whole semester')).toBeVisible()
  })

  test('shows correct benefits for each tier', async ({ page }) => {
    // All tiers have the same benefits in the current implementation
    // Updated for MLA 9 support (citations-568p)
    await expect(page.getByText('Full APA 7 & MLA 9 Compliance').first()).toBeVisible()
    await expect(page.getByText('Detailed citation analysis').first()).toBeVisible()
    await expect(page.getByText('Actionable error correction feedback').first()).toBeVisible()
    await expect(page.getByText('Risk-free with money-back guarantee').first()).toBeVisible()
  })

  test('shows fair use disclaimer below cards', async ({ page }) => {
    await expect(page.getByText('Fair use: 1,000 citations per day. Passes can be extended anytime.')).toBeVisible()
  })

  test('all buy buttons show promo text and are clickable', async ({ page }) => {
    // With promo enabled, all buttons say "Get 50% Off"
    const promoButtons = page.getByRole('button', { name: /Get 50% Off/i })

    // Should have exactly 3 buttons (one per tier)
    await expect(promoButtons).toHaveCount(3)

    // All buttons should be visible
    const count = await promoButtons.count()
    for (let i = 0; i < count; i++) {
      await expect(promoButtons.nth(i)).toBeVisible()
    }
  })

  test('shows promo pill with promotional text', async ({ page }) => {
    // Promo pill should be visible above the pricing cards
    const promoPill = page.locator('.bg-gradient-to-r.from-amber-200')
    await expect(promoPill).toBeVisible()

    // Check promo text is displayed
    await expect(page.getByText("New Year's Deal — 50% Off")).toBeVisible()
  })

  test('shows strikethrough original prices', async ({ page }) => {
    // Strikethrough prices should be visible (original prices before discount)
    const strikethroughPrices = page.locator('.line-through')
    await expect(strikethroughPrices.first()).toBeVisible()

    // Original prices should be shown: $3.99, $9.99, $19.99 (calculated from 50% off)
    await expect(page.getByText('$3.99').first()).toBeVisible()
    await expect(page.getByText('$9.99').first()).toBeVisible() // Note: 7-day also shows $9.99 strikethrough
    await expect(page.getByText('$19.99').first()).toBeVisible()
  })

  test('shows per-unit costs for 7-day and 30-day passes', async ({ page }) => {
    // Per-unit costs shown at bottom of cards
    await expect(page.getByText('Just $0.71/day')).toBeVisible()
    await expect(page.getByText('Only $0.33/day')).toBeVisible()

    // 1-day pass shows dash placeholder (no per-unit breakdown)
    await expect(page.locator('.text-gray-400:has-text("—")')).toBeVisible()
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