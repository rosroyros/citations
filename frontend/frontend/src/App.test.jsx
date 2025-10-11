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
