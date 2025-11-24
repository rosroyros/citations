import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import App from './App.jsx'
import { CreditProvider } from './contexts/CreditContext'

// Mock TipTap editor for testing
vi.mock('@tiptap/react', () => ({
  useEditor: (config) => {
    const editor = {
      getHTML: () => '<p>Test citation content</p>',
      getText: () => 'Test citation content',
      commands: {
        setContent: vi.fn(),
      },
      on: vi.fn(),
      off: vi.fn(),
      isFocused: false,
    }

    // Call onFocus callback if provided to simulate editor interaction
    if (config.onFocus) {
      setTimeout(() => config.onFocus({ editor }), 0)
    }

    return editor
  },
  EditorContent: ({ editor }) => {
    // Mock editor content - simulate user has input content
    return (
      <div className="tiptap ProseMirror citation-editor" contentEditable="true" tabIndex="0" translate="no">
        <p>Test citation content</p>
      </div>
    )
  },
}))

// Mock credit storage utilities
vi.mock('./utils/creditStorage.js', async () => {
  const actual = await vi.importActual('./utils/creditStorage.js')
  return {
    ...actual,
    getToken: vi.fn(() => null),
    getFreeUsage: vi.fn(() => 0),
  }
})

// Mock analytics utility
vi.mock('./utils/analytics', () => ({
  trackEvent: vi.fn(),
}))

// Mock scrollIntoView method
const mockScrollIntoView = vi.fn()

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}

// Mock Element.prototype.scrollIntoView and localStorage
beforeEach(() => {
  Element.prototype.scrollIntoView = mockScrollIntoView
  Object.defineProperty(window, 'localStorage', {
    value: localStorageMock,
    writable: true
  })
  localStorageMock.getItem.mockReturnValue(null) // No existing job by default
})

afterEach(() => {
  vi.clearAllMocks()
})

// Helper function to render App with provider
const renderApp = () => {
  return render(
    <CreditProvider>
      <App />
    </CreditProvider>
  )
}

describe('Auto-scroll to validation results', () => {
  beforeEach(() => {
    // Mock fetch API
    global.fetch = vi.fn()

    // Mock console methods to reduce noise in tests
    vi.spyOn(console, 'log').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should auto-scroll to validation loading state when citations are submitted', async () => {
    // Mock successful async job creation
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ job_id: 'test-job-123' })
      })
      // Mock job polling (processing state first)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: 'pending',
          results: null
        })
      })

    const { container } = renderApp()

    // Wait a moment for editor to initialize and simulate removing placeholder
    await waitFor(() => {
      const submitButton = screen.getByRole('button', { name: /check my citations/i })
      expect(submitButton).not.toBeDisabled()
    }, { timeout: 1000 })

    // Clear mock calls before action
    mockScrollIntoView.mockClear()

    // Submit the form
    const submitButton = screen.getByRole('button', { name: /check my citations/i })
    fireEvent.click(submitButton)

    // Wait for the validation loading state to appear
    await waitFor(() => {
      expect(screen.getByText('Validation Results')).toBeTruthy()
    }, { timeout: 3000 })

    // Add a small delay to ensure useEffect has time to run
    await new Promise(resolve => setTimeout(resolve, 200))

    // Verify that scrollIntoView was called with smooth behavior
    expect(mockScrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'start'
    })

    // Verify it was called on the validation results section
    const validationSection = container.querySelector('.validation-results-section')
    expect(validationSection).toBeTruthy()
  })

  it('should use smooth scrolling behavior with proper positioning', async () => {
    // Mock successful async job creation
    fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ job_id: 'test-job-456' })
      })
      // Mock job polling (processing state)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: 'processing',
          results: null
        })
      })

    const { container } = renderApp()

    // Wait for button to be enabled
    await waitFor(() => {
      const submitButton = screen.getByRole('button', { name: /check my citations/i })
      expect(submitButton).not.toBeDisabled()
    }, { timeout: 1000 })

    const submitButton = screen.getByRole('button', { name: /check my citations/i })
    mockScrollIntoView.mockClear()

    fireEvent.click(submitButton)

    // Wait for validation results to appear
    await waitFor(() => {
      expect(screen.getByText('Validation Results')).toBeTruthy()
    }, { timeout: 3000 })

    // Add a small delay to ensure useEffect has time to run
    await new Promise(resolve => setTimeout(resolve, 200))

    // Verify scrollIntoView was called with correct options for mobile compatibility
    expect(mockScrollIntoView).toHaveBeenCalledTimes(1)
    expect(mockScrollIntoView).toHaveBeenCalledWith({
      behavior: 'smooth',
      block: 'start'
    })
  })
})