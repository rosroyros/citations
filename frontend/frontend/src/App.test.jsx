import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'

// Mock TipTap editor for testing
vi.mock('@tiptap/react', () => ({
  useEditor: () => ({
    getHTML: () => '<p>Sample citation text</p>',
    getText: () => 'Sample citation text',
    isEmpty: false,
    commands: {},
  }),
  EditorContent: ({ editor }) => <div data-testid="editor">Mock Editor</div>,
}))

beforeEach(() => {
  vi.clearAllMocks()
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

    const submitButton = screen.getByRole('button', { name: /validate/i })
    await userEvent.click(submitButton)

    // Assert fetch was called with HTML content
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/validate',
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

    const submitButton = screen.getByRole('button', { name: /validate/i })
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

    const submitButton = screen.getByRole('button', { name: /validate/i })
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

    const submitButton = screen.getByRole('button', { name: /validate/i })
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

    const submitButton = screen.getByRole('button', { name: /validate/i })
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

    const submitButton = screen.getByRole('button', { name: /validate/i })
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
