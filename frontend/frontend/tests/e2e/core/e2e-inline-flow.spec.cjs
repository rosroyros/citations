// @ts-check
const { test, expect } = require('@playwright/test')
const path = require('path')

/**
 * E2E Tests for Inline Citation Validation Flow
 *
 * Uses Playwright Network Mocking (page.route) to ensure deterministic results.
 * This bypasses the backend MockProvider, allowing us to test specific scenarios
 * (orphans, valid matches, gating) reliably without complex backend logic.
 */

// ==========================================
// Mock Data Definitions
// ==========================================

const MOCK_JOB_ID = 'mock-job-123'

// 1. Valid Response (No orphans, perfect matches)
// NOTE: structure flattened to match useInlineCitations hook expectation
const MOCK_VALID_RESPONSE = {
  status: 'completed',
  results: {
    job_id: MOCK_JOB_ID,
    status: 'completed',
    validation_type: 'full_doc',
    citations_checked: 2,
    citations_remaining: 0,
    user_status: { type: 'paid', plan: 'unlimited' },
    results: [
      {
        id: 'ref-1',
        citation_text: 'Smith, J. (2019). Title of article. Journal of Academic Studies, 1(2), 10-20.',
        status: 'valid',
        errors: [],
        citation_number: 1
      },
      {
        id: 'ref-2',
        citation_text: 'Johnson, K. (2020). Another article. Academic Publishers.',
        status: 'valid',
        errors: [],
        citation_number: 2
      }
    ],
    inline_citations: [
      { id: 'ic-1', citation_text: '(Smith, 2019)', match_probability: 0.95, matched_ref_index: 0, match_status: 'matched' },
      { id: 'ic-2', citation_text: 'Johnson (2020)', match_probability: 0.95, matched_ref_index: 1, match_status: 'matched' }
    ],
    orphan_citations: []
  }
}

// 2. Orphan Response (Has orphans)
const MOCK_ORPHAN_RESPONSE = {
  status: 'completed',
  results: {
    job_id: MOCK_JOB_ID,
    status: 'completed',
    validation_type: 'full_doc',
    citations_checked: 1,
    citations_remaining: 0,
    user_status: { type: 'paid', plan: 'unlimited' },
    results: [
      {
        id: 'ref-1',
        citation_text: 'Smith, J. (2019). Title of article. Journal of Academic Studies, 1(2), 10-20.',
        status: 'valid',
        errors: [],
        citation_number: 1
      }
    ],
    inline_citations: [
      { id: 'ic-1', citation_text: '(Smith, 2019)', match_probability: 0.95, matched_ref_index: 0, match_status: 'matched' }
    ],
    orphan_citations: [
      {
        id: 'orphan-1',
        citation_text: '(Doe, 2021)',
        citation_count: 1
      }
    ]
  }
}

// 3. Large/Gated Response (Partial results)
const MOCK_GATED_RESPONSE = {
  status: 'completed',
  results: {
    job_id: MOCK_JOB_ID,
    status: 'completed',
    validation_type: 'full_doc',
    partial: true, // Triggers gating UI
    limit_type: 'free_tier_limit',
    citations_checked: 5,
    citations_remaining: 3,
    user_status: { type: 'free', daily_limit: 5, daily_used: 5 },
    results: Array(5).fill(null).map((_, i) => ({
      id: `ref-${i}`,
      citation_text: `Author, ${i}. (202${i}). Generated citation ${i}. Publisher.`,
      status: 'valid',
      errors: [],
      citation_number: i + 1
    })),
    inline_citations: Array(5).fill(null).map((_, i) => ({
      id: `ic-${i}`,
      citation_text: `(Author, 202${i})`,
      match_probability: 0.9,
      matched_ref_index: i,
      match_status: 'matched'
    })),
    orphan_citations: []
  }
}

// 4. Complex Response (Mismatches and Ambiguous)
const MOCK_COMPLEX_RESPONSE = {
  status: 'completed',
  results: {
    job_id: MOCK_JOB_ID,
    status: 'completed',
    validation_type: 'full_doc',
    citations_checked: 1,
    citations_remaining: 0,
    user_status: { type: 'paid', plan: 'unlimited' },
    results: [
      {
        id: 'ref-1',
        citation_number: 1,
        citation_text: 'Smith, J. (2019). Title of article. Journal of Academic Studies, 1(2), 10-20.',
        status: 'valid',
        errors: [],
        citation_number: 1
      }
    ],
    inline_citations: [
      {
        id: 'ic-1',
        citation_text: '(Smith, 2019)',
        match_probability: 0.99,
        matched_ref_index: 0,
        match_status: 'matched'
      },
      {
        id: 'ic-2',
        citation_text: '(Smith, 2020)',
        match_probability: 0.6,
        matched_ref_index: 0,
        match_status: 'mismatch',
        mismatch_reason: 'Year mismatch',
        suggested_correction: '(Smith, 2019)'
      },
      {
        id: 'ic-3',
        citation_text: '(Smith, 2019a)',
        match_probability: 0.5,
        matched_ref_index: 0,
        match_status: 'ambiguous',
        suggested_correction: 'Check reference'
      }
    ],
    orphan_citations: []
  }
}

test.describe('Inline Citation Validation Flow', () => {

  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies()
    await page.addInitScript(() => {
      localStorage.clear()
      // Force 'Credits + Button' variant (1.1) to ensure consistent UI for tests
      localStorage.setItem('experiment_v1', '1.1')
      // Simulate Paid User by default to bypass Gated Results overlay
      localStorage.setItem('citation_checker_token', 'mock-paid-token')
      window.gtag = function () { } // Mock gtag
    })

    // Default Mock: Valid Response
    // We override this in specific tests using page.route again if needed
    await setupNetworkMocks(page, MOCK_VALID_RESPONSE)

    await page.goto('/')
  })

  // Helper to setup mocks
  async function setupNetworkMocks(page, mockResponse) {
    // 1. Mock the file upload / validation start
    await page.route('/api/validate/async', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ job_id: MOCK_JOB_ID })
      })
    })

    // 2. Mock the polling result
    await page.route(/\/api\/jobs\/.*/, async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockResponse)
      })
    })
  }

  // ============================================
  // DOCX Upload Tests
  // ============================================
  test.describe('DOCX Upload', () => {
    test('upload valid DOCX shows inline citations', async ({ page }) => {
      // Ensure we use the valid response mock
      await setupNetworkMocks(page, MOCK_VALID_RESPONSE)

      const fileInput = page.locator('input[type="file"]')
      const testDocPath = path.join(__dirname, '../../fixtures/test_doc_valid.docx')

      await fileInput.setInputFiles(testDocPath)

      // Wait for results
      await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 10000 })

      // Verify inline citations displayed in stats
      // Note: The UI logic checks for validation_type or presence of inline_citations
      const expandButton = page.getByLabel('Expand').first()
      await expect(expandButton).toBeVisible()
      await expandButton.click()

      // Verify inline citations nested under ref
      const inlineList = page.locator('[data-testid^="inline-list-"]').first()
      await expect(inlineList).toBeVisible()
      await expect(page.getByText('(Smith, 2019)')).toBeVisible()
    })

    test('upload document with orphans shows warning', async ({ page }) => {
      // OVERRIDE: Use Orphan Response Mock
      await setupNetworkMocks(page, MOCK_ORPHAN_RESPONSE)

      const fileInput = page.locator('input[type="file"]')
      const testDocPath = path.join(__dirname, '../../fixtures/test_doc_orphans.docx')

      await fileInput.setInputFiles(testDocPath)

      // Wait for results
      await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 10000 })

      // Verify orphan warning box
      const warningBox = page.locator('[data-testid="orphan-warning"]')
      await expect(warningBox).toBeVisible()
      await expect(warningBox).toContainText('Citation Missing from References')
      await expect(warningBox).toContainText('(Doe, 2021)')
    })

    test('complex inline statuses (mismatch, ambiguous) display correctly', async ({ page }) => {
      // OVERRIDE: Use Complex Response Mock
      await setupNetworkMocks(page, MOCK_COMPLEX_RESPONSE)

      const fileInput = page.locator('input[type="file"]')
      // Using valid doc as input, mock response determines output
      const testDocPath = path.join(__dirname, '../../fixtures/test_doc_valid.docx')

      await fileInput.setInputFiles(testDocPath)

      // Wait for results
      await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 10000 })

      // Expand to see inline citations
      const expandButton = page.getByLabel('Expand').first()
      await expandButton.click()

      // Verify Mismatch
      const mismatchItem = page.locator('.inline-item.status-mismatch')
      await expect(mismatchItem).toBeVisible()
      await expect(mismatchItem).toContainText('(Smith, 2020)')
      await expect(mismatchItem).toContainText('Year mismatch')
      await expect(mismatchItem).toContainText('Should be: (Smith, 2019)')

      // Verify Ambiguous
      const ambiguousItem = page.locator('.inline-item.status-ambiguous')
      await expect(ambiguousItem).toBeVisible()
      await expect(ambiguousItem).toContainText('(Smith, 2019a)')
      await expect(ambiguousItem).toContainText('Matches multiple references')
    })
  })

  // ============================================
  // Paste-based Tests
  // ============================================
  test.describe('Paste Full Document', () => {
    test('paste full document triggers inline validation', async ({ page }) => {
      // Use valid response mock
      await setupNetworkMocks(page, MOCK_VALID_RESPONSE)

      const fullDocContent = `
According to Smith (2019), the results were significant. Another study by Johnson (2020) confirmed these findings.

References

Smith, J. (2019). Title of article. Journal of Academic Studies, 1(2), 10-20.
Johnson, K. (2020). Another article. Academic Publishers.
      `.trim()

      // Paste content into editor
      const editor = page.locator('.ProseMirror')
      await editor.fill(fullDocContent)

      // Submit
      const submitButton = page.getByRole('button', { name: 'Check My Citations' })
      await expect(submitButton).toBeEnabled()
      await submitButton.click()

      // Wait for results
      await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 10000 })

      // Verify first result has inline citations
      const expandButton = page.getByLabel('Expand').first()
      await expandButton.click()
      await expect(page.getByText('(Smith, 2019)')).toBeVisible()
    })
  })

  // ============================================
  // Free Tier Gating Tests
  // ============================================
  test.describe('Free Tier Gating', () => {
    test('free tier shows limited refs with inline', async ({ page }) => {
      // CLEAR TOKEN to simulate free user
      await page.evaluate(() => localStorage.removeItem('citation_checker_token'))
      await page.reload()

      // OVERRIDE: Use Gated Response Mock
      await setupNetworkMocks(page, MOCK_GATED_RESPONSE)

      const fileInput = page.locator('input[type="file"]')
      // We can upload any file, the mock determines the response
      const testDocPath = path.join(__dirname, '../../fixtures/test_doc_large.docx')

      await fileInput.setInputFiles(testDocPath)

      await expect(page.locator('.validation-results-section')).toBeVisible({ timeout: 10000 })

      // Should show partial indicator - looking for "Partial" which is in the span
      await expect(page.getByText('Partial', { exact: false })).toBeVisible()

      // Should show upgrade prompt
      await expect(page.getByRole('button', { name: /Upgrade/i })).toBeVisible()

      // Verify we have results shown
      const resultRows = page.locator('tbody tr.result-row')
      await expect(resultRows).toHaveCount(5)
    })
  })

  // ============================================
  // Validation Tests
  // ============================================
  test.describe('Validation', () => {
    test('upload non-DOCX shows error for inline validation', async ({ page }) => {
      // This is a client-side check, so mocks don't matter as much,
      // but we shouldn't trigger the API call

      const fileInput = page.locator('input[type="file"]')

      // Try to upload a text file
      await fileInput.setInputFiles({
        name: 'test.txt',
        mimeType: 'text/plain',
        buffer: Buffer.from('This is not a DOCX file')
      })

      // Should show error
      await expect(page.getByText(/Only .docx files/)).toBeVisible()
    })
  })
})
