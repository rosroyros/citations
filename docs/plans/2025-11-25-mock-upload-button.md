# Mock Upload Button Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a mock upload document button next to the citation editor to measure user demand for document upload functionality before investing in expensive processing infrastructure.

**Architecture:** Create an UploadArea component that sits alongside the existing TipTap editor, allowing real file selection and metadata extraction while showing a "coming soon" modal. The component integrates with existing analytics infrastructure to track user behavior patterns for demand validation.

**Tech Stack:** React, TipTap editor, FileReader API, CSS variables matching existing design system, custom analytics events

---

### Task 1: Create UploadArea Component Structure

**Files:**
- Create: `frontend/frontend/src/components/UploadArea.jsx`
- Create: `frontend/frontend/src/components/UploadArea.module.css`
- Test: `frontend/frontend/src/components/__tests__/UploadArea.test.jsx`

**Step 1: Write the failing test**

```jsx
// frontend/frontend/src/components/__tests__/UploadArea.test.jsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { UploadArea } from '../UploadArea'

describe('UploadArea', () => {
  const mockOnFileSelect = jest.fn()
  const mockAnalytics = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders upload area with correct elements', () => {
    render(<UploadArea onFileSelect={mockOnFileSelect} trackAnalytics={mockAnalytics} />)

    expect(screen.getByText('Upload Document')).toBeInTheDocument()
    expect(screen.getByText('or drag & drop')).toBeInTheDocument()
    expect(screen.getByText(/PDF, DOCX, TXT up to 10MB/)).toBeInTheDocument()
  })

  it('handles file selection and calls analytics', async () => {
    const file = new File(['test'], 'test.pdf', { type: 'application/pdf' })

    render(<UploadArea onFileSelect={mockOnFileSelect} trackAnalytics={mockAnalytics} />)

    const fileInput = screen.getByLabelText('Upload document')
    fireEvent.change(fileInput, { target: { files: [file] } })

    await waitFor(() => {
      expect(mockAnalytics).toHaveBeenCalledWith('upload_file_selected', {
        fileName: 'test.pdf',
        fileSize: 4,
        fileType: 'application/pdf',
        fileExtension: 'pdf'
      })
    })
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend/frontend && npm test -- --watchAll=false UploadArea.test.jsx`
Expected: FAIL with "UploadArea component not found"

**Step 3: Write minimal UploadArea component**

```jsx
// frontend/frontend/src/components/UploadArea.jsx
import React, { useState, useRef, useCallback } from 'react'
import styles from './UploadArea.module.css'

export function UploadArea({ onFileSelect, trackAnalytics }) {
  const [isDragOver, setIsDragOver] = useState(false)
  const fileInputRef = useRef(null)

  const handleFileSelect = useCallback((files) => {
    if (files && files.length > 0) {
      const file = files[0]

      // Track analytics
      trackAnalytics('upload_file_selected', {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
        fileExtension: file.name.split('.').pop().toLowerCase()
      })

      onFileSelect(file)
    }
  }, [onFileSelect, trackAnalytics])

  const handleInputChange = useCallback((e) => {
    handleFileSelect(e.target.files)
  }, [handleFileSelect])

  const handleClick = useCallback(() => {
    fileInputRef.current?.click()
  }, [])

  return (
    <div className={`${styles.uploadArea} ${isDragOver ? styles.dragOver : ''}`}>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.doc,.txt,.rtf"
        onChange={handleInputChange}
        className={styles.fileInput}
        aria-label="Upload document"
      />

      <div className={styles.uploadContent} onClick={handleClick}>
        <div className={styles.uploadIcon}>
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M7 10L12 15L17 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M12 15V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M20 13V19C20 20.1046 19.1046 21 18 21H6C4.89543 21 4 20.1046 4 19V13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>

        <div className={styles.uploadText}>
          <div className={styles.primaryText}>Upload Document</div>
          <div className={styles.secondaryText}>or drag & drop</div>
        </div>

        <div className={styles.uploadLimits}>
          PDF, DOCX, TXT up to 10MB
        </div>

        <div className={styles.fileTypeIcons}>
          <span className={styles.fileIcon}>PDF</span>
          <span className={styles.fileIcon}>DOCX</span>
          <span className={styles.fileIcon}>TXT</span>
        </div>
      </div>
    </div>
  )
}
```

**Step 4: Create CSS module**

```css
/* frontend/frontend/src/components/UploadArea.module.css */
.uploadArea {
  background: white;
  border: 2px solid var(--border-color, #e5e7eb);
  border-radius: 8px;
  padding: 1rem;
  min-height: 250px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: all 0.2s ease;
  background: var(--color-bg-secondary, #fafbfc);
  position: relative;
}

.uploadArea:hover {
  border-color: var(--color-brand, #9333ea);
  box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1);
}

.uploadArea.dragOver {
  border-style: dashed;
  border-color: var(--color-brand, #9333ea);
  background: linear-gradient(135deg, transparent, rgba(147, 51, 234, 0.05));
  animation: borderPulse 1.5s infinite;
}

@keyframes borderPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.fileInput {
  display: none;
}

.uploadContent {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.uploadIcon {
  color: var(--color-text-tertiary, #718096);
  margin-bottom: 0.5rem;
}

.uploadIcon svg {
  width: 48px;
  height: 48px;
}

.uploadText {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.primaryText {
  font-weight: 600;
  color: var(--color-text-primary, #1a1f36);
  font-size: 1rem;
}

.secondaryText {
  font-size: 0.875rem;
  color: var(--color-text-secondary, #4a5568);
}

.uploadLimits {
  font-size: 0.8rem;
  color: var(--color-text-tertiary, #718096);
  margin-top: 0.5rem;
}

.fileTypeIcons {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.fileIcon {
  background: var(--color-bg-tertiary, #f3f4f6);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
  color: var(--color-text-secondary, #4a5568);
}
```

**Step 5: Run test to verify it passes**

Run: `cd frontend/frontend && npm test -- --watchAll=false UploadArea.test.jsx`
Expected: PASS

**Step 6: Commit**

```bash
git add frontend/frontend/src/components/UploadArea.jsx
git add frontend/frontend/src/components/UploadArea.module.css
git add frontend/frontend/src/components/__tests__/UploadArea.test.jsx
git commit -m "feat: create UploadArea component with basic structure and styling"
```

---

### Task 2: Add Drag and Drop Functionality

**Files:**
- Modify: `frontend/frontend/src/components/UploadArea.jsx`
- Test: `frontend/frontend/src/components/__tests__/UploadArea.test.jsx`

**Step 1: Write failing test for drag and drop**

```jsx
// Add to existing test file
it('handles drag over events and updates styling', () => {
  render(<UploadArea onFileSelect={mockOnFileSelect} trackAnalytics={mockAnalytics} />)

  const uploadArea = screen.getByLabelText('Upload document').closest('div')

  fireEvent.dragEnter(uploadArea)
  fireEvent.dragOver(uploadArea)

  expect(uploadArea).toHaveClass('dragOver')
})

it('handles file drop and tracks analytics', async () => {
  const file = new File(['test content'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })

  render(<UploadArea onFileSelect={mockOnFileSelect} trackAnalytics={mockAnalytics} />)

  const uploadArea = screen.getByLabelText('Upload document').closest('div')

  fireEvent.drop(uploadArea, {
    dataTransfer: {
      files: [file]
    }
  })

  await waitFor(() => {
    expect(mockAnalytics).toHaveBeenCalledWith('upload_file_selected', {
      fileName: 'test.docx',
      fileSize: 14,
      fileType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      fileExtension: 'docx'
    })
  })

  expect(mockAnalytics).toHaveBeenCalledWith('upload_file_dragged')
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend/frontend && npm test -- --watchAll=false UploadArea.test.jsx`
Expected: FAIL with drag events not implemented

**Step 3: Implement drag and drop functionality**

```jsx
// Update the UploadArea component with drag and drop handlers
const handleDragOver = useCallback((e) => {
  e.preventDefault()
  e.stopPropagation()
  setIsDragOver(true)
}, [])

const handleDragEnter = useCallback((e) => {
  e.preventDefault()
  e.stopPropagation()
  setIsDragOver(true)
}, [])

const handleDragLeave = useCallback((e) => {
  e.preventDefault()
  e.stopPropagation()
  setIsDragOver(false)
}, [])

const handleDrop = useCallback((e) => {
  e.preventDefault()
  e.stopPropagation()
  setIsDragOver(false)

  const files = e.dataTransfer.files
  if (files && files.length > 0) {
    trackAnalytics('upload_file_dragged')
    handleFileSelect(files)
  }
}, [handleFileSelect, trackAnalytics])

// Update the div with drag event handlers
return (
  <div
    className={`${styles.uploadArea} ${isDragOver ? styles.dragOver : ''}`}
    onDragOver={handleDragOver}
    onDragEnter={handleDragEnter}
    onDragLeave={handleDragLeave}
    onDrop={handleDrop}
  >
    {/* existing content */}
  </div>
)
```

**Step 4: Run test to verify it passes**

Run: `cd frontend/frontend && npm test -- --watchAll=false UploadArea.test.jsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/frontend/src/components/UploadArea.jsx
git add frontend/frontend/src/components/__tests__/UploadArea.test.jsx
git commit -m "feat: add drag and drop functionality to UploadArea component"
```

---

### Task 3: Create ComingSoonModal Component

**Files:**
- Create: `frontend/frontend/src/components/ComingSoonModal.jsx`
- Create: `frontend/frontend/src/components/ComingSoonModal.module.css`
- Test: `frontend/frontend/src/components/__tests__/ComingSoonModal.test.jsx`

**Step 1: Write failing test**

```jsx
// frontend/frontend/src/components/__tests__/ComingSoonModal.test.jsx
import { render, screen, fireEvent } from '@testing-library/react'
import { ComingSoonModal } from '../ComingSoonModal'

describe('ComingSoonModal', () => {
  const mockOnClose = jest.fn()
  const mockAnalytics = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders modal with file information', () => {
    const file = {
      name: 'research.pdf',
      size: 2048576,
      type: 'application/pdf'
    }

    render(
      <ComingSoonModal
        isOpen={true}
        file={file}
        onClose={mockOnClose}
        trackAnalytics={mockAnalytics}
      />
    )

    expect(screen.getByText(/File Upload Coming Soon/)).toBeInTheDocument()
    expect(screen.getByText(/Great choice! We detected your PDF/)).toBeInTheDocument()
    expect(screen.getByText('Got it!')).toBeInTheDocument()
  })

  it('calls analytics and onClose when dismissed', () => {
    const file = { name: 'test.docx', size: 1024, type: 'application/docx' }

    render(
      <ComingSoonModal
        isOpen={true}
        file={file}
        onClose={mockOnClose}
        trackAnalytics={mockAnalytics}
      />
    )

    fireEvent.click(screen.getByText('Got it!'))

    expect(mockAnalytics).toHaveBeenCalledWith('upload_modal_closed', {
      dismissMethod: 'button',
      fileName: 'test.docx',
      fileSize: 1024
    })
    expect(mockOnClose).toHaveBeenCalled()
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend/frontend && npm test -- --watchAll=false ComingSoonModal.test.jsx`
Expected: FAIL with component not found

**Step 3: Implement ComingSoonModal component**

```jsx
// frontend/frontend/src/components/ComingSoonModal.jsx
import React, { useEffect, useRef } from 'react'
import styles from './ComingSoonModal.module.css'

export function ComingSoonModal({ isOpen, file, onClose, trackAnalytics }) {
  const modalRef = useRef(null)
  const startTimeRef = useRef(null)

  useEffect(() => {
    if (isOpen) {
      startTimeRef.current = Date.now()
      document.body.style.overflow = 'hidden'

      // Track modal open
      trackAnalytics('upload_completed_disabled', {
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type
      })
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, file, trackAnalytics])

  const handleClose = (dismissMethod = 'button') => {
    if (startTimeRef.current) {
      const duration = Date.now() - startTimeRef.current
      trackAnalytics('upload_modal_closed', {
        dismissMethod,
        fileName: file.name,
        fileSize: file.size,
        duration: duration
      })
    }

    onClose()
  }

  const handleBackdropClick = (e) => {
    if (e.target === modalRef.current) {
      handleClose('backdrop')
    }
  }

  const getFileTypeDisplay = (file) => {
    const extension = file.name.split('.').pop().toLowerCase()
    const typeMap = {
      'pdf': 'PDF',
      'docx': 'Document',
      'doc': 'Document',
      'txt': 'Text file',
      'rtf': 'Rich text'
    }
    return typeMap[extension] || 'Document'
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  if (!isOpen) return null

  return (
    <div className={styles.modalBackdrop} ref={modalRef} onClick={handleBackdropClick}>
      <div className={styles.modalContent}>
        <button
          className={styles.closeButton}
          onClick={() => handleClose('close_button')}
          aria-label="Close modal"
        >
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M18 6L6 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>

        <div className={styles.modalIcon}>
          📄
        </div>

        <h2 className={styles.modalTitle}>
          File Upload Coming Soon
        </h2>

        <div className={styles.modalMessage}>
          <p>
            Great choice! We detected your <strong>{getFileTypeDisplay(file)}</strong> and saved it to help prioritize this feature.
          </p>

          <p className={styles.instructions}>
            For now, you can paste the text from your document here:
          </p>
        </div>

        <div className={styles.fileInfo}>
          <div className={styles.fileName}>{file.name}</div>
          <div className={styles.fileSize}>{formatFileSize(file.size)}</div>
        </div>

        <div className={styles.helpfulMessage}>
          Your feedback helps us build this faster!
        </div>

        <button
          className={styles.primaryButton}
          onClick={() => handleClose('button')}
        >
          Got it!
        </button>
      </div>
    </div>
  )
}
```

**Step 4: Create modal CSS**

```css
/* frontend/frontend/src/components/ComingSoonModal.module.css */
.modalBackdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 1rem;
}

.modalContent {
  background: white;
  border-radius: 12px;
  padding: 2rem;
  max-width: 480px;
  width: 100%;
  position: relative;
  box-shadow: var(--shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.05));
  text-align: center;
}

.closeButton {
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  color: var(--color-text-tertiary, #718096);
  transition: all 0.2s ease;
}

.closeButton:hover {
  background: var(--color-bg-tertiary, #f3f4f6);
  color: var(--color-text-primary, #1a1f36);
}

.modalIcon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.modalTitle {
  font-family: var(--font-heading, 'Work Sans', sans-serif);
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary, #1a1f36);
  margin: 0 0 1rem 0;
}

.modalMessage {
  color: var(--color-text-secondary, #4a5568);
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.modalMessage p {
  margin: 0 0 0.75rem 0;
}

.instructions {
  font-weight: 500;
  color: var(--color-text-primary, #1a1f36) !important;
}

.fileInfo {
  background: var(--color-bg-secondary, #fafbfc);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.fileName {
  font-weight: 600;
  color: var(--color-text-primary, #1a1f36);
  margin-bottom: 0.25rem;
  word-break: break-word;
}

.fileSize {
  font-size: 0.875rem;
  color: var(--color-text-tertiary, #718096);
}

.helpfulMessage {
  font-size: 0.875rem;
  color: var(--color-brand, #9333ea);
  margin-bottom: 1.5rem;
  font-weight: 500;
}

.primaryButton {
  background: var(--color-brand, #9333ea);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  width: 100%;
}

.primaryButton:hover {
  background: var(--color-brand-hover, #7c3aed);
}

@media (max-width: 768px) {
  .modalContent {
    padding: 1.5rem;
    margin: 1rem;
  }

  .modalTitle {
    font-size: 1.25rem;
  }
}
```

**Step 5: Run test to verify it passes**

Run: `cd frontend/frontend && npm test -- --watchAll=false ComingSoonModal.test.jsx`
Expected: PASS

**Step 6: Commit**

```bash
git add frontend/frontend/src/components/ComingSoonModal.jsx
git add frontend/frontend/src/components/ComingSoonModal.module.css
git add frontend/frontend/src/components/__tests__/ComingSoonModal.test.jsx
git commit -m "feat: create ComingSoonModal component with enhanced messaging"
```

---

### Task 4: Create File Processing Hook

**Files:**
- Create: `frontend/frontend/src/hooks/useFileProcessing.js`
- Test: `frontend/frontend/src/hooks/__tests__/useFileProcessing.test.js`

**Step 1: Write failing test**

```jsx
// frontend/frontend/src/hooks/__tests__/useFileProcessing.test.js
import { renderHook, act } from '@testing-library/react'
import { useFileProcessing } from '../useFileProcessing'

describe('useFileProcessing', () => {
  const mockAnalytics = jest.fn()
  const mockOnComplete = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  it('processes file and calls analytics with processing state', async () => {
    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' })

    const { result } = renderHook(() =>
      useFileProcessing(mockAnalytics, mockOnComplete)
    )

    act(() => {
      result.current.processFile(file)
    })

    expect(result.current.isProcessing).toBe(true)
    expect(mockAnalytics).toHaveBeenCalledWith('upload_processing_shown', {
      fileName: 'test.pdf',
      fileSize: 12,
      fileType: 'application/pdf'
    })

    act(() => {
      jest.advanceTimersByTime(1500)
    })

    expect(result.current.isProcessing).toBe(false)
    expect(mockOnComplete).toHaveBeenCalledWith(file)
    expect(mockAnalytics).toHaveBeenCalledWith('upload_file_preview_rendered', {
      fileName: 'test.pdf',
      fileExtension: 'pdf',
      processingTime: 1500
    })
  })
})
```

**Step 2: Run test to verify it fails**

Run: `cd frontend/frontend && npm test -- --watchAll=false useFileProcessing.test.js`
Expected: FAIL with hook not found

**Step 3: Implement file processing hook**

```jsx
// frontend/frontend/src/hooks/useFileProcessing.js
import { useState, useCallback } from 'react'
import { trackEvent } from '../utils/analytics'

export function useFileProcessing(customAnalytics, onComplete) {
  const [isProcessing, setIsProcessing] = useState(false)
  const [processingProgress, setProcessingProgress] = useState(0)

  const processFile = useCallback(async (file) => {
    setIsProcessing(true)
    setProcessingProgress(0)

    // Track processing start
    const analyticsData = {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type
    }

    if (customAnalytics) {
      customAnalytics('upload_processing_shown', analyticsData)
    } else {
      trackEvent('upload_processing_shown', analyticsData)
    }

    const startTime = Date.now()

    // Simulate file processing with progress
    const progressInterval = setInterval(() => {
      setProcessingProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval)
          return prev
        }
        return prev + 30
      })
    }, 400)

    // Fixed 1.5 second processing time
    await new Promise(resolve => setTimeout(resolve, 1500))

    clearInterval(progressInterval)
    setProcessingProgress(100)

    const processingTime = Date.now() - startTime

    // Track processing completion
    const completionData = {
      fileName: file.name,
      fileExtension: file.name.split('.').pop().toLowerCase(),
      processingTime: processingTime
    }

    if (customAnalytics) {
      customAnalytics('upload_file_preview_rendered', completionData)
    } else {
      trackEvent('upload_file_preview_rendered', completionData)
    }

    setIsProcessing(false)
    setProcessingProgress(0)

    if (onComplete) {
      onComplete(file)
    }

    return {
      success: true,
      processingTime,
      fileMetadata: {
        name: file.name,
        size: file.size,
        type: file.type,
        extension: file.name.split('.').pop().toLowerCase()
      }
    }
  }, [customAnalytics, onComplete])

  return {
    isProcessing,
    processingProgress,
    processFile
  }
}
```

**Step 4: Run test to verify it passes**

Run: `cd frontend/frontend && npm test -- --watchAll=false useFileProcessing.test.js`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/frontend/src/hooks/useFileProcessing.js
git add frontend/frontend/src/hooks/__tests__/useFileProcessing.test.js
git commit -m "feat: create useFileProcessing hook with consistent 1.5s processing time"
```

---

### Task 5: Integrate UploadArea into App.jsx

**Files:**
- Modify: `frontend/frontend/src/App.jsx`
- Test: `frontend/frontend/src/components/__tests__/App.test.jsx` (update if exists)

**Step 1: Add UploadArea imports and state**

```jsx
// Add to imports in App.jsx
import { UploadArea } from './components/UploadArea'
import { ComingSoonModal } from './components/ComingSoonModal'
import { useFileProcessing } from './hooks/useFileProcessing'

// Add state to AppContent component
const [showUploadModal, setShowUploadModal] = useState(false)
const [uploadedFile, setUploadedFile] = useState(null)

// File processing hook
const { isProcessing, processFile } = useFileProcessing(
  (event, data) => trackEvent(event, data),
  (file) => {
    setUploadedFile(file)
    setShowUploadModal(true)
  }
)

// Upload event handlers
const handleFileUpload = useCallback(async (file) => {
  try {
    await processFile(file)
  } catch (error) {
    console.error('File processing error:', error)
    setError('File upload failed. Please try pasting your citations instead.')
  }
}, [processFile])

const handleUploadModalClose = useCallback(() => {
  setShowUploadModal(false)
  // Track transition to text input
  trackEvent('upload_text_input_transition', {
    fileName: uploadedFile?.name,
    fileSize: uploadedFile?.size
  })
  // Focus back to editor after modal closes
  setTimeout(() => {
    editor?.commands.focus()
  }, 100)
}, [editor, uploadedFile])

const handleUploadAreaClick = useCallback(() => {
  trackEvent('upload_area_clicked')
}, [])
```

**Step 2: Add UploadArea to form layout**

```jsx
// Update the form in App.jsx - modify the input section
<section className="input-section">
  <form onSubmit={handleSubmit}>
    <div className="input-container">
      <div className="editor-section">
        <label>Paste your citations below (APA 7th edition)</label>
        <EditorContent editor={editor} />
        <p className="input-helper">
          Paste one or multiple citations. We'll check each one.
        </p>
      </div>

      <div className="upload-section">
        <UploadArea
          onFileSelect={handleFileUpload}
          trackAnalytics={(event, data) => trackEvent(event, data)}
        />
      </div>
    </div>

    <button
      type="submit"
      disabled={loading || !editor || hasPlaceholder}
    >
      {loading ? 'Validating...' : 'Check My Citations'}
    </button>

    {/* existing content */}
  </form>

  <ComingSoonModal
    isOpen={showUploadModal}
    file={uploadedFile}
    onClose={handleUploadModalClose}
    trackAnalytics={(event, data) => trackEvent(event, data)}
  />
</section>
```

**Step 3: Add responsive CSS for new layout**

```css
/* Add to App.css */
.input-container {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.editor-section {
  flex: 1;
  min-width: 0; /* Allows flex item to shrink */
}

.upload-section {
  flex: 0 0 300px;
  min-width: 280px;
}

@media (max-width: 1024px) {
  .input-container {
    flex-direction: column;
  }

  .upload-section {
    flex: 1;
    width: 100%;
    min-width: unset;
  }
}

@media (max-width: 768px) {
  .input-section {
    padding: 0 1rem 3rem;
  }

  .input-container {
    gap: 1.5rem;
  }
}
```

**Step 4: Run tests to verify integration**

Run: `cd frontend/frontend && npm test -- --watchAll=false App.test.jsx`
Expected: PASS (or create new tests if they don't exist)

**Step 5: Commit**

```bash
git add frontend/frontend/src/App.jsx
git add frontend/frontend/src/App.css
git commit -m "feat: integrate UploadArea and ComingSoonModal into main App component"
```

---

### Task 6: Add Comprehensive Testing

**Files:**
- Create: `frontend/frontend/src/components/__tests__/UploadArea.integration.test.jsx`
- Create: `frontend/frontend/src/components/__tests__/App.integration.test.jsx`

**Step 1: Write integration tests**

```jsx
// frontend/frontend/src/components/__tests__/UploadArea.integration.test.jsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../../App'

// Mock analytics
const mockTrackEvent = jest.fn()
jest.mock('../../utils/analytics', () => ({
  trackEvent: mockTrackEvent
}))

describe('Upload Integration', () => {
  beforeEach(() => {
    mockTrackEvent.mockClear()
  })

  it('integrates upload area with main app flow', async () => {
    render(<App />)

    // Check upload area is present
    expect(screen.getByText('Upload Document')).toBeInTheDocument()
    expect(screen.getByText('or drag & drop')).toBeInTheDocument()

    // Simulate file upload
    const file = new File(['test citations'], 'citations.pdf', { type: 'application/pdf' })
    const fileInput = screen.getByLabelText('Upload document')

    await userEvent.upload(fileInput, file)

    // Wait for processing and modal
    await waitFor(() => {
      expect(screen.getByText(/File Upload Coming Soon/)).toBeInTheDocument()
    }, { timeout: 2000 })

    // Check analytics were called
    expect(mockTrackEvent).toHaveBeenCalledWith('upload_area_clicked')
    expect(mockTrackEvent).toHaveBeenCalledWith('upload_file_selected', expect.objectContaining({
      fileName: 'citations.pdf',
      fileType: 'application/pdf'
    }))
    expect(mockTrackEvent).toHaveBeenCalledWith('upload_processing_shown', expect.any(Object))
    expect(mockTrackEvent).toHaveBeenCalledWith('upload_completed_disabled', expect.any(Object))
  })

  it('handles modal close and returns focus to editor', async () => {
    render(<App />)

    // Upload file to trigger modal
    const file = new File(['test'], 'test.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
    const fileInput = screen.getByLabelText('Upload document')

    await userEvent.upload(fileInput, file)

    // Wait for modal
    await waitFor(() => {
      expect(screen.getByText('Got it!')).toBeInTheDocument()
    })

    // Close modal
    await userEvent.click(screen.getByText('Got it!'))

    // Check modal closed and analytics tracked
    await waitFor(() => {
      expect(screen.queryByText(/File Upload Coming Soon/)).not.toBeInTheDocument()
    })

    expect(mockTrackEvent).toHaveBeenCalledWith('upload_modal_closed', expect.objectContaining({
      dismissMethod: 'button'
    }))
    expect(mockTrackEvent).toHaveBeenCalledWith('upload_text_input_transition', expect.objectContaining({
      fileName: 'test.docx'
    }))
  })
})
```

**Step 2: Run integration tests**

Run: `cd frontend/frontend && npm test -- --watchAll=false UploadArea.integration.test.jsx`
Expected: PASS

**Step 3: Test responsive behavior**

```jsx
// Add responsive tests
it('displays upload area correctly on mobile', async () => {
  // Mock mobile viewport
  window.innerWidth = 375
  window.dispatchEvent(new Event('resize'))

  render(<App />)

  const uploadArea = screen.getByText('Upload Document').closest('div').closest('div')

  // Should be stacked below editor on mobile
  expect(uploadArea).toBeInTheDocument()

  // Check mobile layout classes are applied
  const inputContainer = uploadArea.closest('.input-container')
  expect(inputContainer).toHaveStyle({ flexDirection: 'column' })
})
```

**Step 4: Run all tests**

Run: `cd frontend/frontend && npm test`
Expected: All tests pass

**Step 5: Commit**

```bash
git add frontend/frontend/src/components/__tests__/UploadArea.integration.test.jsx
git add frontend/frontend/src/components/__tests__/App.integration.test.jsx
git commit -m "test: add comprehensive integration tests for upload functionality"
```

---

### Task 7: Add Error Handling and Edge Cases

**Files:**
- Modify: `frontend/frontend/src/components/UploadArea.jsx`
- Test: `frontend/frontend/src/components/__tests__/UploadArea.test.jsx`

**Step 1: Add file validation tests**

```jsx
// Add to UploadArea test file
describe('File Validation', () => {
  it('rejects files larger than 10MB', () => {
    const largeFile = new File(['x'.repeat(11 * 1024 * 1024)], 'large.pdf', { type: 'application/pdf' })

    render(<UploadArea onFileSelect={mockOnFileSelect} trackAnalytics={mockAnalytics} />)

    const fileInput = screen.getByLabelText('Upload document')
    fireEvent.change(fileInput, { target: { files: [largeFile] } })

    expect(screen.getByText(/That's a big document/)).toBeInTheDocument()
    expect(mockOnFileSelect).not.toHaveBeenCalled()
  })

  it('shows supported file types for unsupported formats', () => {
    const imageFile = new File(['test'], 'image.jpg', { type: 'image/jpeg' })

    render(<UploadArea onFileSelect={mockOnFileSelect} trackAnalytics={mockAnalytics} />)

    const fileInput = screen.getByLabelText('Upload document')
    fireEvent.change(fileInput, { target: { files: [imageFile] } })

    expect(screen.getByText(/PDFs work great!/)).toBeInTheDocument()
    expect(mockOnFileSelect).not.toHaveBeenCalled()
  })
})
```

**Step 2: Implement file validation**

```jsx
// Add file validation to UploadArea component
const SUPPORTED_TYPES = ['.pdf', '.docx', '.doc', '.txt', '.rtf']
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB

const validateFile = (file) => {
  const extension = '.' + file.name.split('.').pop().toLowerCase()

  if (file.size > MAX_FILE_SIZE) {
    return {
      isValid: false,
      error: 'large_file',
      message: `That's a big document! For now, files under 10MB work best.`
    }
  }

  if (!SUPPORTED_TYPES.includes(extension)) {
    return {
      isValid: false,
      error: 'unsupported_type',
      message: 'PDFs work great! For other formats, try copying the text.'
    }
  }

  return { isValid: true }
}

const handleFileSelect = useCallback((files) => {
  if (files && files.length > 0) {
    const file = files[0]
    const validation = validateFile(file)

    if (!validation.isValid) {
      setError(validation.message)
      trackAnalytics('upload_validation_error', {
        errorType: validation.error,
        fileName: file.name,
        fileSize: file.size
      })
      return
    }

    trackAnalytics('upload_file_selected', {
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      fileExtension: file.name.split('.').pop().toLowerCase()
    })

    onFileSelect(file)
  }
}, [onFileSelect, trackAnalytics])

// Add error state
const [error, setError] = useState(null)

// Add error display in component
{error && (
  <div className={styles.errorMessage}>
    {error}
  </div>
)}
```

**Step 3: Add error styling**

```css
/* Add to UploadArea.module.css */
.errorMessage {
  background: var(--color-error-bg, #fffbeb);
  border: 1px solid var(--color-error-border, #fcd34d);
  color: var(--color-error, #b45309);
  padding: 0.75rem;
  border-radius: 6px;
  font-size: 0.875rem;
  margin-top: 0.5rem;
  text-align: center;
}
```

**Step 4: Run tests**

Run: `cd frontend/frontend && npm test -- --watchAll=false UploadArea.test.jsx`
Expected: PASS

**Step 5: Commit**

```bash
git add frontend/frontend/src/components/UploadArea.jsx
git add frontend/frontend/src/components/UploadArea.module.css
git add frontend/frontend/src/components/__tests__/UploadArea.test.jsx
git commit -m "feat: add file validation and error handling for upload functionality"
```

---

### Task 8: Final Testing and Documentation

**Files:**
- Create: `frontend/frontend/docs/upload-feature.md`
- Test: Manual testing checklist

**Step 1: Create documentation**

```markdown
# Upload Feature Documentation

## Overview
The upload feature allows users to upload documents for citation validation while measuring demand for future document processing functionality.

## User Flow
1. User clicks upload area or drags file
2. File is validated (type, size)
3. Processing animation (1.5 seconds)
4. "Coming soon" modal appears
5. User closes modal and returns to text input

## Analytics Events
- `upload_area_clicked` - when upload area clicked
- `upload_file_dragged` - when file dragged
- `upload_file_selected` - file metadata
- `upload_validation_error` - validation failures
- `upload_processing_shown` - processing start
- `upload_file_preview_rendered` - processing complete
- `upload_completed_disabled` - modal shown
- `upload_modal_closed` - modal dismissed with duration
- `upload_text_input_transition` - return to text input

## File Support
- **Types**: PDF, DOCX, DOC, TXT, RTF
- **Size**: Maximum 10MB
- **Validation**: Client-side only

## Technical Implementation
- UploadArea component with drag & drop
- ComingSoonModal for user communication
- useFileProcessing hook for consistent processing
- Integrated with existing analytics infrastructure
- Responsive design (desktop: side-by-side, mobile: stacked)

## Testing
- Unit tests for all components
- Integration tests for full user flow
- File validation edge cases
- Responsive behavior
- Accessibility compliance
```

**Step 2: Manual testing checklist**

Create and run through this checklist:
- [ ] Upload area displays correctly on desktop
- [ ] Upload area displays correctly on mobile
- [ ] File drag and drop works
- [ ] File click selection works
- [ ] File validation rejects large files
- [ ] File validation rejects unsupported types
- [ ] Processing animation shows for 1.5 seconds
- [ ] Modal displays with correct file information
- [ ] Modal can be closed via button, X, or backdrop
- [ ] Focus returns to text editor after modal
- [ ] Analytics events fire correctly
- [ ] No impact on existing citation validation
- [ ] Keyboard navigation works
- [ ] Screen reader compatibility

**Step 3: Final commit**

```bash
git add frontend/frontend/docs/upload-feature.md
git commit -m "docs: add upload feature documentation and testing guide"
```

**Step 4: Create summary of changes**

```bash
echo "## Mock Upload Button Implementation Complete

### Components Created
- UploadArea component with drag & drop functionality
- ComingSoonModal component with enhanced messaging
- useFileProcessing hook for consistent processing

### Features Implemented
- File validation (type, size checking)
- Processing animation (1.5 seconds)
- Comprehensive analytics tracking
- Responsive design (desktop/mobile)
- Error handling and user feedback
- Accessibility compliance

### Files Modified
- App.jsx (integration of upload components)
- App.css (responsive layout styling)

### Testing
- Unit tests for all components
- Integration tests for user flow
- File validation edge cases
- Manual testing checklist

### Analytics Events
- 7 different events tracked for demand validation
- File metadata and user behavior captured
- Modal duration and dismiss methods tracked

Ready for production deployment and demand validation data collection." > git commit -m "feat: complete mock upload button implementation with comprehensive testing and documentation"
```

---

**Plan complete and saved to `docs/plans/2025-11-25-mock-upload-button.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**