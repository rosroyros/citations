import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { vi, expect, test, describe, beforeEach } from 'vitest'
import App from '../App'

// Mock localStorage
const localStorageMock = (() => {
  let store = {}
  return {
    getItem: vi.fn((key) => store[key] || null),
    setItem: vi.fn((key, value) => {
      store[key] = value.toString()
    }),
    removeItem: vi.fn((key) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    })
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock
})

// Mock fetch globally
global.fetch = vi.fn()

// Mock timeout functions
vi.useFakeTimers()

describe('Async Polling', () => {
  beforeEach(() => {
    localStorageMock.clear()
    fetch.mockClear()
    vi.clearAllMocks()
  })

  test('should call /api/validate/async endpoint and start polling', async () => {
    // Mock the async endpoint response
    fetch.mockImplementationOnce(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ job_id: 'test-job-123', status: 'pending' })
      })
    )

    // Mock the job status endpoint for polling
    fetch.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'completed', results: { results: [], free_used_total: 1 } })
      })
    )

    render(<App />)

    // Get the editor using contenteditable attribute
    const editor = screen.getByRole('textbox') || document.querySelector('.citation-editor')
    if (editor) {
      // Clear existing content and add new content
      editor.innerHTML = 'Smith, J. (2023). Test citation.'
      fireEvent.focus(editor)
      fireEvent.input(editor, { target: { innerHTML: 'Smith, J. (2023). Test citation.' } })
    }

    // Click submit button (find the enabled one)
    const submitButton = screen.getByText('Check My Citations')
    if (submitButton && !submitButton.disabled) {
      fireEvent.click(submitButton)
    }

    // Advance timers to allow polling to complete
    vi.advanceTimersByTime(3000)

    // Should have called async endpoint
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        '/api/validate/async',
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('Smith, J. (2023)')
        })
      )
    }, { timeout: 10000 })

    // Should store job_id in localStorage
    expect(localStorageMock.setItem).toHaveBeenCalledWith(
      'current_job_id',
      'test-job-123'
    )
  }, 15000)

  test('should recover job on component mount if job_id exists in localStorage', async () => {
    // Set up existing job in localStorage
    localStorageMock.getItem.mockReturnValue('existing-job-456')

    // Mock the job status endpoint
    fetch.mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ status: 'completed', results: { results: [], free_used_total: 1 } })
      })
    )

    render(<App />)

    // Advance timers to allow polling to complete
    vi.advanceTimersByTime(3000)

    // Should poll for existing job status
    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        '/api/jobs/existing-job-456',
        expect.objectContaining({
          method: 'GET'
        })
      )
    }, { timeout: 10000 })
  }, 15000)
})