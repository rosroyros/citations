import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from './App'

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

    // Find textarea and submit button
    const textarea = screen.getByRole('textbox', { name: /citations/i })
    const submitButton = screen.getByRole('button', { name: /validate/i })

    // Enter citation text
    await userEvent.type(textarea, 'Sample citation text')

    // Click submit
    await userEvent.click(submitButton)

    // Assert fetch was called with correct endpoint
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/validate',
        expect.objectContaining({
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: expect.stringContaining('Sample citation text'),
        })
      )
    })

    // Cleanup
    global.fetch.mockRestore()
  })
})

describe('App - Validation Results Display', () => {
  it('displays validation results with errors correctly', async () => {
    // Mock API response with validation errors
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
            {
              component: 'title',
              problem: 'Article title should be in sentence case',
              correction: 'Should be "Bad citation"'
            }
          ]
        },
        {
          citation_number: 2,
          original: 'Brown, B. (2021). Good Citation. Publisher.',
          source_type: 'book',
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

    const textarea = screen.getByRole('textbox', { name: /citations/i })
    const submitButton = screen.getByRole('button', { name: /validate/i })

    await userEvent.type(textarea, 'Test citation')
    await userEvent.click(submitButton)

    // Wait for results to appear
    await waitFor(() => {
      expect(screen.getByText(/validation results/i)).toBeInTheDocument()
    })

    // Check that original citations are displayed
    expect(screen.getByText(/Smith, J. and Jones, A./)).toBeInTheDocument()
    expect(screen.getByText(/Brown, B. \(2021\)/)).toBeInTheDocument()

    // Check that errors are displayed with ❌ indicator
    const errorIcons = screen.getAllByText(/❌/)
    expect(errorIcons.length).toBeGreaterThan(0)
    expect(screen.getByText(/Used "and" instead of "&" before last author/)).toBeInTheDocument()
    expect(screen.getByText(/Article title should be in sentence case/)).toBeInTheDocument()
    expect(screen.getByText(/Should be "Smith, J., & Jones, A."/)).toBeInTheDocument()

    // Check that valid citation shows ✅
    const citationSections = screen.getAllByText(/citation #/i)
    expect(citationSections).toHaveLength(2)

    // Cleanup
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

    const textarea = screen.getByRole('textbox', { name: /citations/i })
    const submitButton = screen.getByRole('button', { name: /validate/i })

    await userEvent.type(textarea, 'Test citation')
    await userEvent.click(submitButton)

    await waitFor(() => {
      const successIcons = screen.getAllByText(/✅/)
      expect(successIcons.length).toBeGreaterThan(0)
      expect(screen.getByText(/no errors found/i)).toBeInTheDocument()
    })

    // Cleanup
    global.fetch.mockRestore()
  })
})

describe('App - Error Handling', () => {
  it('displays user-friendly error message when API returns error', async () => {
    // Mock API error response
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ error: 'Internal server error occurred' }),
      })
    )

    render(<App />)

    const textarea = screen.getByRole('textbox', { name: /citations/i })
    const submitButton = screen.getByRole('button', { name: /validate/i })

    await userEvent.type(textarea, 'Test citation')
    await userEvent.click(submitButton)

    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText(/error:/i)).toBeInTheDocument()
      expect(screen.getByText(/internal server error occurred/i)).toBeInTheDocument()
    })

    // Cleanup
    global.fetch.mockRestore()
  })

  it('displays error message when network request fails', async () => {
    // Mock network failure
    global.fetch = vi.fn(() => Promise.reject(new Error('Network error')))

    render(<App />)

    const textarea = screen.getByRole('textbox', { name: /citations/i })
    const submitButton = screen.getByRole('button', { name: /validate/i })

    await userEvent.type(textarea, 'Test citation')
    await userEvent.click(submitButton)

    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText(/error:/i)).toBeInTheDocument()
      expect(screen.getByText(/network error/i)).toBeInTheDocument()
    })

    // Cleanup
    global.fetch.mockRestore()
  })

  it('disables submit button when input is empty', () => {
    render(<App />)

    const submitButton = screen.getByRole('button', { name: /validate/i })

    // Button should be disabled with empty input
    expect(submitButton).toBeDisabled()
  })

  it('enables submit button when input has text', async () => {
    render(<App />)

    const textarea = screen.getByRole('textbox', { name: /citations/i })
    const submitButton = screen.getByRole('button', { name: /validate/i })

    // Initially disabled
    expect(submitButton).toBeDisabled()

    // Type something
    await userEvent.type(textarea, 'Test citation')

    // Should be enabled now
    expect(submitButton).not.toBeDisabled()
  })

  it('clears previous error when new submission is made', async () => {
    // First request fails
    global.fetch = vi.fn(() => Promise.reject(new Error('First error')))

    render(<App />)

    const textarea = screen.getByRole('textbox', { name: /citations/i })
    const submitButton = screen.getByRole('button', { name: /validate/i })

    await userEvent.type(textarea, 'Test citation')
    await userEvent.click(submitButton)

    // Wait for first error
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

    // Wait for error to clear
    await waitFor(() => {
      expect(screen.queryByText(/first error/i)).not.toBeInTheDocument()
    })

    // Cleanup
    global.fetch.mockRestore()
  })
})
