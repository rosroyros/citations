import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'

// Mock credit storage utilities
vi.mock('./utils/creditStorage.js', () => ({
  getToken: vi.fn(),
  getFreeUsage: vi.fn(),
  incrementFreeUsage: vi.fn(),
}))

// Mock TipTap editor for testing
vi.mock('@tiptap/react', () => ({
  useEditor: (config) => {
    const editor = {
      getHTML: () => '<p>Sample citation text</p>',
      getText: () => 'Sample citation text',
      isEmpty: false,
      commands: { setContent: vi.fn() },
    };
    // Immediately trigger onFocus to clear placeholder
    if (config?.onFocus) {
      config.onFocus({ editor });
    }
    return editor;
  },
  EditorContent: ({ editor }) => <div data-testid="editor">Mock Editor</div>,
}))

beforeEach(() => {
  vi.clearAllMocks()
  localStorage.clear()
})

describe('App - Form Submission', () => {
  it('calls backend API when form is submitted', async () => {
    // Mock fetch
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ results: [] }),
      })
    )

    render(<App />)

    const submitButton = screen.getByRole('button', { name: /check my citations/i })
    await userEvent.click(submitButton)

    // Assert fetch was called with HTML content
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/validate',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: expect.stringContaining('<p>Sample citation text</p>'),
        })
      )
    })

    global.fetch.mockRestore()
  })
})

describe('App - Validation Results Display', () => {
  it('displays validation results with errors correctly', async () => {
    const mockResponse = {
      results: [
        {
          citation_number: 1,
          original: 'Smith, J. and Jones, A. (2020). Bad Citation. Journal Name, 10(2), 123-456.',
          source_type: 'journal',
          errors: [
            {
              component: 'authors',
              problem: 'Used "and" instead of "&" before last author',
              correction: 'Should be "Smith, J., & Jones, A."'
            },
          ]
        },
      ]
    }

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })
    )

    render(<App />)

    const submitButton = screen.getByRole('button', { name: /check my citations/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/validation results/i)).toBeInTheDocument()
      expect(screen.getByText(/Smith, J. and Jones, A./)).toBeInTheDocument()
      expect(screen.getByText(/Used "and" instead of "&" before last author/)).toBeInTheDocument()
    })

    global.fetch.mockRestore()
  })

  it('displays message for citations with no errors', async () => {
    const mockResponse = {
      results: [
        {
          citation_number: 1,
          original: 'Perfect, A. (2020). Good citation. Journal.',
          source_type: 'journal',
          errors: []
        }
      ]
    }

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })
    )

    render(<App />)

    const submitButton = screen.getByRole('button', { name: /check my citations/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      const successIcons = screen.getAllByText(/✅/)
      expect(successIcons.length).toBeGreaterThan(0)
      expect(screen.getByText(/no errors found/i)).toBeInTheDocument()
    })

    global.fetch.mockRestore()
  })
})

describe('App - Error Handling', () => {
  it('displays user-friendly error message when API returns error', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ error: 'Internal server error occurred' }),
      })
    )

    render(<App />)

    const submitButton = screen.getByRole('button', { name: /check my citations/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/error:/i)).toBeInTheDocument()
      expect(screen.getByText(/internal server error occurred/i)).toBeInTheDocument()
    })

    global.fetch.mockRestore()
  })

  it('displays error message when network request fails', async () => {
    global.fetch = vi.fn(() => Promise.reject(new Error('Network error')))

    render(<App />)

    const submitButton = screen.getByRole('button', { name: /check my citations/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/error:/i)).toBeInTheDocument()
      expect(screen.getByText(/network error/i)).toBeInTheDocument()
    })

    global.fetch.mockRestore()
  })

  it('clears previous error when new submission is made', async () => {
    // First request fails
    global.fetch = vi.fn(() => Promise.reject(new Error('First error')))

    render(<App />)

    const submitButton = screen.getByRole('button', { name: /check my citations/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/first error/i)).toBeInTheDocument()
    })

    // Second request succeeds
    global.fetch.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ results: [] }),
      })
    )

    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.queryByText(/first error/i)).not.toBeInTheDocument()
    })

    global.fetch.mockRestore()
  })
})

describe.skip('App - Credit System Integration', () => {
  const { getToken, getFreeUsage, incrementFreeUsage } = require('./utils/creditStorage.js')

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('sends X-User-Token header in validation requests when token exists', async () => {
    getToken.mockReturnValue('user-token-123')
    getFreeUsage.mockReturnValue(5)

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ results: [] }),
      })
    )

    render(<App />)

    const submitButton = screen.getByRole('button', { name: /check my citations/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/validate',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-User-Token': 'user-token-123',
          },
        })
      )
    })

    global.fetch.mockRestore()
  })

  it('shows UpgradeModal when free tier exhausted (>= 10)', async () => {
    getToken.mockReturnValue(null)
    getFreeUsage.mockReturnValue(10)

    render(<App />)

    const submitButton = screen.getByRole('button', { name: /check my citations/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByTestId('modal-overlay')).toBeInTheDocument()
    })
  })

  it('displays PartialResults when response.partial === true', async () => {
    getToken.mockReturnValue('user-token-123')
    getFreeUsage.mockReturnValue(5)

    const mockPartialResponse = {
      results: [
        {
          citation_number: 1,
          original: 'Smith, J. (2020). Partial citation.',
          source_type: 'journal',
          errors: []
        }
      ],
      partial: {
        total_citations: 5,
        checked_citations: 2,
        remaining_credits: 3
      },
      citations_checked: 2,
      citations_remaining: 3
    }

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockPartialResponse),
      })
    )

    render(<App />)

    const submitButton = screen.getByRole('button', { name: /check my citations/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/2 more citations checked/)).toBeInTheDocument()
      expect(screen.getByText(/Upgrade to see all results/)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Get 1,000 Citation Credits/ })).toBeInTheDocument()
    })

    global.fetch.mockRestore()
  })

  it('increments free usage counter after successful validation (free users)', async () => {
    getToken.mockReturnValue(null)
    getFreeUsage.mockReturnValue(3)

    const mockResponse = {
      results: [
        { citation_number: 1, original: 'Citation 1', source_type: 'journal', errors: [] },
        { citation_number: 2, original: 'Citation 2', source_type: 'book', errors: [] }
      ]
    }

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })
    )

    render(<App />)

    const submitButton = screen.getByRole('button', { name: /check my citations/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(incrementFreeUsage).toHaveBeenCalledWith(2)
    })

    global.fetch.mockRestore()
  })

  it('does not increment free usage when user has token (paid tier)', async () => {
    getToken.mockReturnValue('paid-user-token')
    getFreeUsage.mockReturnValue(3)

    const mockResponse = {
      results: [
        { citation_number: 1, original: 'Citation 1', source_type: 'journal', errors: [] }
      ]
    }

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      })
    )

    render(<App />)

    const submitButton = screen.getByRole('button', { name: /check my citations/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(incrementFreeUsage).not.toHaveBeenCalled()
    })

    global.fetch.mockRestore()
  })

  it('allows submission when free user has less than 10 usages', async () => {
    getToken.mockReturnValue(null)
    getFreeUsage.mockReturnValue(7)

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ results: [] }),
      })
    )

    render(<App />)

    const submitButton = screen.getByRole('button', { name: /check my citations/i })
    await userEvent.click(submitButton)

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled()
    })

    global.fetch.mockRestore()
  })
})
