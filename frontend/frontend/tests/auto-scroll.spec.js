import { test, expect } from '@playwright/test'

test.describe('Auto-scroll E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5174/')
    // Wait for the page to load completely
    await page.waitForSelector('.citation-editor')
  })

  test('should auto-scroll to validation results when citations are submitted', async ({ page }) => {
    // Get initial scroll position
    const initialScrollY = await page.evaluate(() => window.scrollY)
    console.log('Initial scroll position:', initialScrollY)

    // Type citation text in the editor
    const editor = page.locator('.citation-editor')
    await editor.click() // This should remove the placeholder
    await editor.fill('Smith, J. (2023). Understanding research methods. Journal of Academic Studies, 45(2), 123-145. https://doi.org/10.1234/example')

    // Find the validation results section (it should exist but not be visible yet)
    const validationSection = page.locator('.validation-results-section')
    await expect(validationSection).toHaveCount(0)

    // Get the button and ensure it's enabled
    const submitButton = page.locator('button[type="submit"]')
    await expect(submitButton).toBeEnabled()

    // Click the submit button
    await submitButton.click()

    // Wait for validation results section to appear
    await expect(validationSection).toHaveCount(1)

    // Get the position of the validation section
    const validationSectionY = await validationSection.evaluate(el => el.getBoundingClientRect().top + window.scrollY)
    console.log('Validation section Y position:', validationSectionY)

    // Wait a moment for the auto-scroll to trigger (100ms delay + rendering time)
    await page.waitForTimeout(300)

    // Get final scroll position
    const finalScrollY = await page.evaluate(() => window.scrollY)
    console.log('Final scroll position:', finalScrollY)

    // Verify that we scrolled down (final position should be greater than initial)
    expect(finalScrollY).toBeGreaterThan(initialScrollY)

    // Verify that the validation section is now visible in viewport
    const validationSectionBounds = await validationSection.boundingBox()
    expect(validationSectionBounds).toBeTruthy()
    expect(validationSectionBounds.y).toBeGreaterThanOrEqual(-200) // Should be visible or just above viewport
    expect(validationSectionBounds.y).toBeLessThan(800) // Should be reasonably close to top (allowing for header/navigation)

    // Verify "Validation Results" text is visible
    await expect(page.locator('text=Validation Results')).toBeVisible()
  })

  test('should handle page refresh recovery and still auto-scroll', async ({ page }) => {
    // Mock localStorage to simulate an existing job
    await page.addInitScript(() => {
      localStorage.setItem('current_job_id', 'test-job-recovery')
    })

    // Mock the API responses for job recovery
    await page.route('/api/jobs/test-job-recovery', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'pending',
          results: null
        })
      })
    })

    // Reload the page (simulating refresh)
    await page.reload()
    await page.waitForSelector('.citation-editor')

    // Get initial scroll position
    const initialScrollY = await page.evaluate(() => window.scrollY)

    // Wait for validation results section to appear due to recovery
    const validationSection = page.locator('.validation-results-section')
    await expect(validationSection).toHaveCount(1)

    // Wait for auto-scroll to trigger
    await page.waitForTimeout(300)

    // Get final scroll position
    const finalScrollY = await page.evaluate(() => window.scrollY)

    // Verify that auto-scroll happened during recovery
    expect(finalScrollY).toBeGreaterThan(initialScrollY)

    // Verify validation results are visible
    await expect(page.locator('text=Validation Results')).toBeVisible()
  })
})