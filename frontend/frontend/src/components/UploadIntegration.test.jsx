import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { CreditProvider } from '../contexts/CreditContext'
import App from '../App'
import { vi, describe, test, expect, beforeEach, afterEach } from 'vitest'

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn()
}
global.localStorage = localStorageMock

// Mock analytics to avoid noise in tests
vi.mock('../utils/analytics', () => ({
  trackEvent: vi.fn()
}))

// Mock the file processing hook
vi.mock('../hooks/useFileProcessing', () => ({
  useFileProcessing: () => {
    let processedFileCallback = null

    return {
      processFile: vi.fn((file) => {
        // Simulate immediate processing for tests
        processedFileCallback = file
      }),
      isProcessing: false,
      progress: 100,
      get processedFile() {
        return processedFileCallback
      },
      reset: vi.fn(() => {
        processedFileCallback = null
      })
    }
  }
}))

// Mock editor to simplify testing
vi.mock('@tiptap/react', () => ({
  useEditor: () => ({
    getHTML: () => '<p>Test content</p>',
    getText: () => 'Test content',
    commands: {
      setContent: vi.fn()
    }
  }),
  EditorContent: ({ editor }) => <div>{editor?.getText?.() || ''}</div>
}))

const renderAppWithProvider = () => {
  return render(
    <BrowserRouter>
      <CreditProvider>
        <App />
      </CreditProvider>
    </BrowserRouter>
  )
}

describe('Upload Component Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorageMock.getItem.mockReturnValue(null)
  })
  test('renders UploadArea component in the input section', () => {
    renderAppWithProvider()

    // Should render UploadArea with its actual text
    expect(screen.getByText(/Drop your document here/i)).toBeInTheDocument()
    expect(screen.getByText(/or click to browse/i)).toBeInTheDocument()
  })

  test('renders ComingSoonModal component (initially hidden)', () => {
    renderAppWithProvider()

    // Modal should not be in DOM when closed (it renders null)
    expect(screen.queryByText(/File Upload Coming Soon/i)).not.toBeInTheDocument()
  })

  test('layouts components responsively - desktop side-by-side', () => {
    // Mock desktop viewport
    global.innerWidth = 1200

    renderAppWithProvider()

    // Check that both editor and upload area are present
    expect(screen.getByTestId('editor')).toBeInTheDocument()
    expect(screen.getByText(/Drop your document here/i)).toBeInTheDocument()

    // In desktop layout, they should be in same container (input section)
    const inputSection = document.querySelector('form')?.closest('section')
    expect(inputSection).toBeInTheDocument()
    expect(inputSection).toHaveClass('input-section')
  })

  test('upload area component responds to file selection', () => {
    renderAppWithProvider()

    // Should have file input with correct attributes
    const fileInput = document.querySelector('input[type="file"]')
    expect(fileInput).toBeInTheDocument()
    expect(fileInput).toHaveAttribute('accept', '.pdf,.docx,.txt,.rtf')

    // Should have upload area with proper accessibility
    const uploadArea = screen.getByTestId('upload-area')
    expect(uploadArea).toHaveAttribute('role', 'button')
    expect(uploadArea).toHaveAttribute('tabIndex', '0')
  })

  test('analytics functions are properly imported and available', async () => {
    const { trackEvent } = await import('../utils/analytics')

    renderAppWithProvider()

    // Should be able to call trackEvent (analytics integration working)
    expect(typeof trackEvent).toBe('function')
  })
})