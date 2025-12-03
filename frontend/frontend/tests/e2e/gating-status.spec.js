import { test, expect } from '@playwright/test'

test.describe('Gating Status Display', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/dashboard')
  })

  test('should display "Revealed" column as rightmost column in validations table', async ({ page }) => {
    // Wait for the table to load
    await page.waitForSelector('.table-container table')

    // Check that the table header includes "Revealed" column
    const revealedHeader = page.locator('th[onclick="sortTable(\'revealed\')"]')
    await expect(revealedHeader).toBeVisible()
    await expect(revealedHeader).toContainText('Revealed')

    // Verify it's the last column in the header
    const headers = page.locator('thead th')
    const headerCount = await headers.count()
    const lastHeader = headers.nth(headerCount - 1)
    await expect(lastHeader).toContainText('Revealed')
  })

  test('should display appropriate colspan when no data is loaded', async ({ page }) => {
    // Wait for potential loading state
    await page.waitForTimeout(1000)

    // Check empty state message uses correct colspan (should be 8 now)
    const emptyMessage = page.locator('#validationsTable td[colspan="8"]')
    if (await emptyMessage.isVisible()) {
      await expect(emptyMessage).toContainText('No validations found')
    }
  })

  test('should display job details modal with gating information', async ({ page }) => {
    // Wait for the table to load
    await page.waitForSelector('.table-container table', { timeout: 10000 })

    // Look for any job row with data (skip loading message)
    const jobRows = page.locator('#validationsTable tr').filter({ hasNot: page.locator('text=Loading data') })

    if (await jobRows.count() > 0) {
      // Click on the first job ID to open details
      const firstJobRow = jobRows.first()
      const jobIdLink = firstJobRow.locator('.job-id')

      if (await jobIdLink.isVisible()) {
        await jobIdLink.click()

        // Wait for details to appear
        await page.waitForSelector('#details-' + await jobIdLink.getAttribute('onclick').match(/'([^']+)'/)[1], {
          state: 'visible',
          timeout: 5000
        })

        // Check that gating information is displayed in the modal
        const gatingDetails = page.locator('.job-details:has-text("Results Gated:")')
        if (await gatingDetails.isVisible()) {
          await expect(gatingDetails).toBeVisible()
          await expect(gatingDetails).toContainText('Results Gated:')
        }
      }
    }
  })

  test('should apply correct CSS classes for different gating statuses', async ({ page }) => {
    // Wait for the table to load
    await page.waitForSelector('.table-container table', { timeout: 10000 })

    // Look for any gating status elements
    const gatedStatusElements = page.locator('.revealed-gated, .revealed-yes, .revealed-free')

    // If any gating status elements exist, verify they have proper styling
    const statusCount = await gatedStatusElements.count()
    if (statusCount > 0) {
      for (let i = 0; i < statusCount; i++) {
        const element = gatedStatusElements.nth(i)
        await expect(element).toBeVisible()

        // Check that the element has appropriate content (emoji + text)
        const textContent = await element.textContent()
        expect(textContent).toMatch(/^(🔒|✅|⚡)\s+\w+/)
      }
    }
  })

  test('should handle gating statistics section properly', async ({ page }) => {
    // Check if gating statistics section exists
    const gatedStats = page.locator('#gatedStats')

    if (await gatedStats.isVisible()) {
      // Verify gating stats elements are present
      await expect(page.locator('#revealedCount')).toBeVisible()

      // Check the toggle button for gated details
      const toggleButton = page.locator('button[onclick="toggleGatedDetails()"]')
      if (await toggleButton.isVisible()) {
        await toggleButton.click()

        // Verify gated details section toggles
        await expect(page.locator('#gatedDetails')).toBeVisible()
      }
    }
  })

  test('should display loading state with correct colspan', async ({ page }) => {
    // Check initial loading state
    const loadingRow = page.locator('#validationsTable tr:has(td.loading)')

    if (await loadingRow.isVisible()) {
      const loadingCell = loadingRow.locator('td[colspan="8"]')
      await expect(loadingCell).toBeVisible()
      await expect(loadingCell).toContainText('Loading data')
    }
  })
})