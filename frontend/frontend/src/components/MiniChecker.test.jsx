import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import MiniChecker from './MiniChecker'

// ═══════════════════════════════════════════════════════════════════
// Test Helper: Mock async polling flow (job creation → status poll)
// ═══════════════════════════════════════════════════════════════════

/**
 * Creates mock for the async validation flow:
 * 1. POST /api/validate/async → returns job_id
 * 2. GET /api/jobs/{id} → returns job status (can be called multiple times)
 * 
 * @param {Object} options
 * @param {Object} options.citationResult - The citation result to return
 * @param {string[]} options.pollSequence - Sequence of statuses ['pending', 'completed']
 * @param {string} options.errorMessage - Error message for failed status
 */
function mockAsyncPolling({ citationResult, pollSequence = ['completed'], errorMessage = null }) {
  const mock = vi.fn()
    // First call: POST /api/validate/async
    .mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ job_id: 'test-job-123' })
    })

  // Subsequent calls: GET /api/jobs/{id}
  pollSequence.forEach((status, index) => {
    const isLast = index === pollSequence.length - 1
    mock.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({
        status,
        results: status === 'completed' ? { results: [citationResult] } : null,
        error: status === 'failed' ? (errorMessage || 'Validation failed') : null
      })
    })
  })

  return global.fetch = mock
}

// Standard citation result for tests
const validCitationResult = {
  citation_number: 1,
  original: 'Test citation',
  source_type: 'journal',
  errors: []
}

beforeEach(() => {
  vi.clearAllMocks()
})

// ═══════════════════════════════════════════════════════════════════
// Rendering Tests (no fetch mocking needed)
// ═══════════════════════════════════════════════════════════════════

describe('MiniChecker - Rendering', () => {
  it('renders with default props', () => {
    render(<MiniChecker />)

    expect(screen.getByText(/quick check your citation/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/paste your citation here/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /check citation/i })).toBeInTheDocument()
  })

  it('renders with custom placeholder', () => {
    render(<MiniChecker placeholder="Enter journal article citation..." />)

    expect(screen.getByPlaceholderText(/enter journal article citation/i)).toBeInTheDocument()
  })

  it('renders with prefilled example', () => {
    const example = 'Smith, J. (2020). Test article. Journal, 10(2), 123-145.'
    render(<MiniChecker prefillExample={example} />)

    expect(screen.getByDisplayValue(example)).toBeInTheDocument()
  })

  it('displays keyboard shortcut tip', () => {
    render(<MiniChecker />)

    expect(screen.getByText(/ctrl\+enter/i)).toBeInTheDocument()
  })
})

// ═══════════════════════════════════════════════════════════════════
// Validation Tests
// ═══════════════════════════════════════════════════════════════════

describe('MiniChecker - Validation', () => {
  it('validates citation when button clicked', async () => {
    mockAsyncPolling({ citationResult: validCitationResult })

    render(<MiniChecker />)

    const textarea = screen.getByPlaceholderText(/paste your citation here/i)
    const button = screen.getByRole('button', { name: /check citation/i })

    await userEvent.type(textarea, 'Smith, J. (2020). Test. Journal.')
    await userEvent.click(button)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/validate/async',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
    })

    global.fetch.mockRestore()
  })

  it('shows loading state during validation', async () => {
    global.fetch = vi.fn(() => new Promise(() => { })) // Never resolves

    render(<MiniChecker />)

    const textarea = screen.getByPlaceholderText(/paste your citation here/i)
    const button = screen.getByRole('button', { name: /check citation/i })

    await userEvent.type(textarea, 'Test citation')
    await userEvent.click(button)

    expect(screen.getByRole('button', { name: /checking/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /checking/i })).toBeDisabled()

    global.fetch.mockRestore()
  })

  it('disables button when textarea is empty', () => {
    render(<MiniChecker />)

    const button = screen.getByRole('button', { name: /check citation/i })
    expect(button).toBeDisabled()
  })

  it('validates on Ctrl+Enter keyboard shortcut', async () => {
    mockAsyncPolling({ citationResult: validCitationResult })

    render(<MiniChecker />)

    const textarea = screen.getByPlaceholderText(/paste your citation here/i)
    await userEvent.type(textarea, 'Test citation')
    await userEvent.keyboard('{Control>}{Enter}{/Control}')

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
    })

    global.fetch.mockRestore()
  })
})

// ═══════════════════════════════════════════════════════════════════
// Results Display Tests
// ═══════════════════════════════════════════════════════════════════

describe('MiniChecker - Results Display', () => {
  it('displays valid citation result', async () => {
    const citationResult = {
      citation_number: 1,
      original: 'Smith, J. (2020). Perfect citation. Journal, 10(2), 123-145.',
      source_type: 'journal',
      errors: []
    }
    mockAsyncPolling({ citationResult })

    render(<MiniChecker />)

    const textarea = screen.getByPlaceholderText(/paste your citation here/i)
    const button = screen.getByRole('button', { name: /check citation/i })

    await userEvent.type(textarea, 'Test citation')
    await userEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/no formatting errors found/i)).toBeInTheDocument()
      expect(screen.getByText(/✅/)).toBeInTheDocument()
    })

    global.fetch.mockRestore()
  })

  it('displays invalid citation with errors', async () => {
    const citationResult = {
      citation_number: 1,
      original: 'Bad citation',
      source_type: 'journal',
      errors: [
        {
          component: 'title',
          problem: 'Title should be in sentence case',
          correction: 'Use sentence case for article titles'
        },
        {
          component: 'authors',
          problem: 'Use & instead of "and"',
          correction: 'Replace "and" with &'
        }
      ]
    }
    mockAsyncPolling({ citationResult })

    render(<MiniChecker />)

    const textarea = screen.getByPlaceholderText(/paste your citation here/i)
    const button = screen.getByRole('button', { name: /check citation/i })

    await userEvent.type(textarea, 'Bad citation')
    await userEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/found 2 formatting issue/i)).toBeInTheDocument()
      expect(screen.getByText(/title should be in sentence case/i)).toBeInTheDocument()
      expect(screen.getByText(/use & instead of "and"/i)).toBeInTheDocument()
    })

    global.fetch.mockRestore()
  })

  it('displays CTA after results', async () => {
    mockAsyncPolling({ citationResult: validCitationResult })

    render(<MiniChecker />)

    const textarea = screen.getByPlaceholderText(/paste your citation here/i)
    const button = screen.getByRole('button', { name: /check citation/i })

    await userEvent.type(textarea, 'Test')
    await userEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/check your entire reference list/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /open citation checker/i })).toBeInTheDocument()
    })

    global.fetch.mockRestore()
  })

  it('calls onFullChecker callback when CTA clicked', async () => {
    mockAsyncPolling({ citationResult: validCitationResult })

    const onFullChecker = vi.fn()
    render(<MiniChecker onFullChecker={onFullChecker} />)

    const textarea = screen.getByPlaceholderText(/paste your citation here/i)
    const button = screen.getByRole('button', { name: /check citation/i })

    await userEvent.type(textarea, 'Test')
    await userEvent.click(button)

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /open citation checker/i })).toBeInTheDocument()
    })

    const ctaButton = screen.getByRole('button', { name: /open citation checker/i })
    await userEvent.click(ctaButton)

    expect(onFullChecker).toHaveBeenCalledTimes(1)

    global.fetch.mockRestore()
  })
})

// ═══════════════════════════════════════════════════════════════════
// Error Handling Tests
// ═══════════════════════════════════════════════════════════════════

describe('MiniChecker - Error Handling', () => {
  it('displays error message when validation fails', async () => {
    // Mock job creation failure (async endpoint returns error)
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        headers: { get: () => 'application/json' },
        json: () => Promise.resolve({ detail: 'Validation failed' }),
      })
    )

    render(<MiniChecker />)

    const textarea = screen.getByPlaceholderText(/paste your citation here/i)
    const button = screen.getByRole('button', { name: /check citation/i })

    await userEvent.type(textarea, 'Test')
    await userEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/⚠️/)).toBeInTheDocument()
      expect(screen.getByText(/validation failed/i)).toBeInTheDocument()
    })

    global.fetch.mockRestore()
  })

  it('displays error message when network request fails', async () => {
    global.fetch = vi.fn(() => Promise.reject(new Error('Network error')))

    render(<MiniChecker />)

    const textarea = screen.getByPlaceholderText(/paste your citation here/i)
    const button = screen.getByRole('button', { name: /check citation/i })

    await userEvent.type(textarea, 'Test')
    await userEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/validation failed/i)).toBeInTheDocument()
    })

    global.fetch.mockRestore()
  })
})

// ═══════════════════════════════════════════════════════════════════
// Input Constraints Tests (no fetch mocking needed)
// ═══════════════════════════════════════════════════════════════════

describe('MiniChecker - Input Constraints', () => {
  it('enforces maximum character limit', () => {
    render(<MiniChecker />)

    const textarea = screen.getByPlaceholderText(/paste your citation here/i)
    expect(textarea).toHaveAttribute('maxLength', '600')
  })

  it('allows only 3 rows in textarea', () => {
    render(<MiniChecker />)

    const textarea = screen.getByPlaceholderText(/paste your citation here/i)
    expect(textarea).toHaveAttribute('rows', '3')
  })
})

// ═══════════════════════════════════════════════════════════════════
// Async Polling Edge Cases
// ═══════════════════════════════════════════════════════════════════

describe('MiniChecker - Async Polling', () => {
  it('polls until job completes', async () => {
    // Mock: pending → pending → completed
    // Mocks resolve immediately, so polling happens without real delays
    mockAsyncPolling({
      citationResult: validCitationResult,
      pollSequence: ['pending', 'pending', 'completed']
    })

    render(<MiniChecker />)

    const textarea = screen.getByPlaceholderText(/paste your citation here/i)
    const button = screen.getByRole('button', { name: /check citation/i })

    await userEvent.type(textarea, 'Test citation')
    await userEvent.click(button)

    // Wait for polling to complete and results to appear
    await waitFor(() => {
      expect(screen.getByText(/no formatting errors found/i)).toBeInTheDocument()
    }, { timeout: 10000 })

    // Verify fetch calls made (1 create + 3 polls)
    expect(global.fetch).toHaveBeenCalledTimes(4)

    global.fetch.mockRestore()
  })

  it('displays job failure error', async () => {
    // Mock: job status returns failed
    mockAsyncPolling({
      citationResult: validCitationResult,
      pollSequence: ['failed'],
      errorMessage: 'Processing error occurred'
    })

    render(<MiniChecker />)

    const textarea = screen.getByPlaceholderText(/paste your citation here/i)
    const button = screen.getByRole('button', { name: /check citation/i })

    await userEvent.type(textarea, 'Test citation')
    await userEvent.click(button)

    await waitFor(() => {
      expect(screen.getByText(/⚠️/)).toBeInTheDocument()
      expect(screen.getByText(/validation failed/i)).toBeInTheDocument()
    })

    global.fetch.mockRestore()
  })
})

