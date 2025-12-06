import { useState, useEffect, useRef } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import { CreditDisplay } from './components/CreditDisplay'
import { UpgradeModal } from './components/UpgradeModal'
import { PartialResults } from './components/PartialResults'
import ValidationTable from './components/ValidationTable'
import ValidationLoadingState from './components/ValidationLoadingState'
import GatedResults from './components/GatedResults'
import Footer from './components/Footer'
import { UploadArea } from './components/UploadArea'
import { ComingSoonModal } from './components/ComingSoonModal'
import { getToken, getFreeUsage, ensureFreeUserId } from './utils/creditStorage'
import { CreditProvider, useCredits } from './contexts/CreditContext'
import { trackEvent, trackResultsRevealedSafe } from './utils/analytics'
import { useAnalyticsTracking } from './hooks/useAnalyticsTracking'
import Success from './pages/Success'
import PrivacyPolicy from './pages/PrivacyPolicy'
import TermsOfService from './pages/TermsOfService'
import ContactUs from './pages/ContactUs'
import Dashboard from './pages/Dashboard'
import DebugHTMLTest from './components/DebugHTMLTest'
import { mockValidationAPI } from './utils/mockData'
import './App.css'

// Set to true to test frontend without backend
const MOCK_MODE = import.meta.env.VITE_MOCK_MODE === 'true'

// Gated results feature flag with runtime validation
const validateGatedResultsEnv = () => {
  const envValue = import.meta.env.VITE_GATED_RESULTS_ENABLED
  const validValues = ['true', 'false']

  if (envValue === undefined) {
    console.warn('VITE_GATED_RESULTS_ENABLED not set, defaulting to false')
    return false
  }

  if (!validValues.includes(envValue)) {
    console.warn(`Invalid VITE_GATED_RESULTS_ENABLED value: "${envValue}". Expected "true" or "false", defaulting to false`)
    return false
  }

  return envValue === 'true'
}

// Gated results design variant with runtime validation
const getGatedResultsVariant = () => {
  const envValue = import.meta.env.VITE_GATED_RESULTS_VARIANT
  const validVariants = ['original', 'glassmorphism', 'gradient', 'card']

  if (envValue === undefined) {
    return 'original'
  }

  if (!validVariants.includes(envValue)) {
    console.warn(`Invalid VITE_GATED_RESULTS_VARIANT value: "${envValue}". Expected one of ${validVariants.join(', ')}, defaulting to 'original'`)
    return 'original'
  }

  return envValue
}

const GATED_RESULTS_ENABLED = validateGatedResultsEnv()
const GATED_RESULTS_VARIANT = getGatedResultsVariant()

// Polling configuration constants
const POLLING_CONFIG = {
  MAX_ATTEMPTS: 90, // 3 minutes at 2s intervals
  POLL_INTERVAL: 2000, // 2 seconds
  LOCAL_STORAGE_KEY: 'current_job_id'
}

// Scroll configuration constants
const SCROLL_CONFIG = {
  DELAY_MS: 100 // Delay to ensure DOM is updated before scrolling
}

function AppContent() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [hasPlaceholder, setHasPlaceholder] = useState(true)
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const [submittedText, setSubmittedText] = useState('')
  const [fadingOut, setFadingOut] = useState(false)

  // Gated results state management
  const [resultsReady, setResultsReady] = useState(false)
  const [resultsRevealed, setResultsRevealed] = useState(false)
  const [resultsReadyTimestamp, setResultsReadyTimestamp] = useState(null)
  const [isGated, setIsGated] = useState(false)
  const [trackingData, setTrackingData] = useState({
    jobStartedAt: null,
    resultsReadyAt: null,
    resultsRevealedAt: null,
    isGated: false
  })
  // Upload state
  const [showComingSoonModal, setShowComingSoonModal] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const editorFocusedRef = useRef(false)
  const abandonmentTimerRef = useRef(null)
  const validationSectionRef = useRef(null)
  const { refreshCredits } = useCredits()
  // Analytics tracking hook - provides trackNavigationClick (used in Footer component)
  useAnalyticsTracking()

  // User type detection
  const getUserType = () => {
    // Check for paid user token
    if (localStorage.getItem('citation_checker_token')) {
      return 'paid'
    } else {
      return 'free'
    }
  }

  const isFreeUser = getUserType() === 'free'

  // State flow logic
  const determineDisplayState = () => {
    if (loading) {
      return 'loading'
    } else if (results && !error) {
      if (isGated && !resultsRevealed) {
        return 'gated'
      } else {
        return 'results'
      }
    } else if (error) {
      return 'error'
    } else {
      return 'idle'
    }
  }

  // Gating logic
  const shouldGateResults = (userIsFree, validationResults) => {
    if (!userIsFree || !GATED_RESULTS_ENABLED) {
      return false
    }

    // Gate all results for free users (simple policy for now)
    return true
  }

  // Cleanup timer on component unmount
  useEffect(() => {
    return () => {
      if (abandonmentTimerRef.current) {
        clearTimeout(abandonmentTimerRef.current)
      }
    }
  }, [])

  // Auto-scroll to validation results when loading starts
  useEffect(() => {
    if (loading && submittedText) {
      // Use requestAnimationFrame to wait for React to complete rendering
      const performScroll = () => {
        // Try both React ref and DOM query to find validation section
        const validationElement = validationSectionRef.current || document.querySelector('.validation-results-section')

        if (validationElement) {
          // Check for user's motion preference (accessibility)
          const prefersReducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false

          // Use manual scroll calculation instead of scrollIntoView (avoids CSS overflow conflicts)
          try {
            const elementRect = validationElement.getBoundingClientRect()
            const elementTop = elementRect.top + window.scrollY

            // Account for fixed header/nav elements
            const headerOffset = 80
            const scrollToPosition = Math.max(0, elementTop - headerOffset)

            window.scrollTo({
              top: scrollToPosition,
              behavior: prefersReducedMotion ? 'auto' : 'smooth'
            })
          } catch (error) {
            console.error('Auto-scroll error:', error)
          }
        } else {
          // Retry if element not found yet
          setTimeout(performScroll, 50)
        }
      }

      // Use multiple attempts with requestAnimationFrame to ensure the DOM is ready
      let attempts = 0
      const maxAttempts = 6 // ~300ms total

      const tryScroll = () => {
        if (validationSectionRef.current || document.querySelector('.validation-results-section')) {
          performScroll()
        } else if (attempts < maxAttempts) {
          attempts++
          requestAnimationFrame(tryScroll)
        }
      }

      // Start the retry process
      requestAnimationFrame(tryScroll)
    }
  }, [loading, submittedText])

  
  // Recover existing job on component mount
  useEffect(() => {
    const existingJobId = localStorage.getItem(POLLING_CONFIG.LOCAL_STORAGE_KEY)
    if (existingJobId) {
      console.log('Found existing job ID:', existingJobId)

      const token = getToken()

      // Start loading state
      setLoading(true)
      setError(null)
      setResults(null)
      setSubmittedText('Recovering validation...') // Enable auto-scroll during recovery

      // Start polling for existing job
      pollForResults(existingJobId, token)
    }
  }, [])

  // Handle reveal results action
  const handleRevealResults = async () => {
    // Validate timestamp before calculation
    if (!resultsReadyTimestamp || typeof resultsReadyTimestamp !== 'number' || resultsReadyTimestamp <= 0) {
      console.warn('Invalid resultsReadyTimestamp, skipping tracking')
      setResultsRevealed(true)
      return
    }

    const timeToReveal = Math.floor((Date.now() - resultsReadyTimestamp) / 1000)

    // Immediate state update for better UX
    setResultsRevealed(true)
    setTrackingData(prev => ({
      ...prev,
      resultsRevealedAt: new Date().toISOString(),
      timeToRevealSeconds: timeToReveal
    }))

    // Get job_id and user tier for tracking
    const jobId = results?.job_id || localStorage.getItem(POLLING_CONFIG.LOCAL_STORAGE_KEY)
    const token = getToken()
    const userTier = token ? 'paid' : 'free'

    // Track analytics event
    if (jobId) {
      trackResultsRevealedSafe(jobId, timeToReveal, userTier)

      // Fire-and-forget API call
      fetch('/api/reveal-results', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          job_id: jobId,
          outcome: 'revealed'
        })
      }).catch(error => {
        // Log error but don't break user experience
        console.warn('Error tracking reveal results:', error)
      })
    }
  }

  // Poll for job results
  const pollForResults = async (jobId, token) => {

    for (let attempt = 0; attempt < POLLING_CONFIG.MAX_ATTEMPTS; attempt++) {
      try {
        console.log(`Polling attempt ${attempt + 1}/${POLLING_CONFIG.MAX_ATTEMPTS} for job ${jobId}`)

        const response = await fetch(`/api/jobs/${jobId}`)

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Job not found - please try again')
          }
          throw new Error(`Server error (${response.status}): Please try again`)
        }

        const jobData = await response.json()
        console.log('Job status:', jobData.status, jobData)

        if (jobData.status === 'completed') {
          console.log('Job completed successfully')
          localStorage.removeItem(POLLING_CONFIG.LOCAL_STORAGE_KEY)

          // Handle successful completion
          const data = jobData.results

          // Sync localStorage with backend's authoritative count
          if (data.free_used_total !== undefined) {
            localStorage.setItem('citation_checker_free_used', String(data.free_used_total))
            console.log(`Updated free usage to: ${data.free_used_total}`)
          }

          // Handle gated results logic
          const userIsFree = !token
          const shouldGate = shouldGateResults(userIsFree, data)

          // Set results and gated state
          setResults(data)
          setIsGated(shouldGate)
          setResultsReady(true)
          setResultsReadyTimestamp(Date.now())

          setTrackingData(prev => ({
            ...prev,
            resultsReadyAt: new Date().toISOString(),
            isGated: shouldGate
          }))

          // Track partial results vs full results
          if (data.partial) {
            setResults({ ...data, isPartial: true })

            // Track free limit reached
            const freeUsed = data.free_used_total || getFreeUsage()
            const citationsCount = data.citations_checked + data.citations_remaining
            trackEvent('free_limit_reached', {
              current_usage: freeUsed,
              limit: 10,
              attempted_citations: citationsCount
            })
          } else {
            // Track citation validation event
            const citationsCount = data.results.length
            const errorsFound = data.results.reduce((sum, result) => sum + (result.errors?.length || 0), 0)
            const perfectCount = data.results.filter(result => !result.errors || result.errors.length === 0).length
            const userType = token ? 'paid' : 'free'

            trackEvent('citation_validated', {
              citations_count: citationsCount,
              errors_found: errorsFound,
              perfect_count: perfectCount,
              user_type: userType,
              interface_source: 'main_page'
            })
          }

          // Refresh credits for paid users
          if (token) {
            setTimeout(() => {
              refreshCredits().catch(err =>
                console.error('Failed to refresh credits:', err)
              )
            }, 100)
          }

          setLoading(false)
          return

        } else if (jobData.status === 'failed') {
          console.log('Job failed:', jobData.error)
          localStorage.removeItem(POLLING_CONFIG.LOCAL_STORAGE_KEY)

          const errorMessage = jobData.error || 'Validation failed'

          // Track validation error
          let errorType = 'job_failed'
          if (errorMessage.includes('credits') || errorMessage.includes('402')) {
            errorType = 'out_of_credits'
          }

          trackEvent('validation_error', {
            error_type: errorType,
            error_message: errorMessage.substring(0, 100)
          })

          setFadingOut(true)
          setTimeout(() => {
            setLoading(false)
            setFadingOut(false)
            setError(errorMessage)
          }, 400)

          return

        } else {
          // Job still pending or processing, continue polling
          if (attempt < POLLING_CONFIG.MAX_ATTEMPTS - 1) {
            await new Promise(resolve => setTimeout(resolve, POLLING_CONFIG.POLL_INTERVAL))
          }
        }

      } catch (err) {
        console.error('Polling error:', err)

        // Track polling error
        let errorType = 'polling_error'
        if (err.message.includes('Job not found')) {
          errorType = 'job_not_found'
        } else if (err.message.includes('402')) {
          errorType = 'out_of_credits'
        }

        trackEvent('validation_error', {
          error_type: errorType,
          error_message: err.message.substring(0, 100)
        })

        localStorage.removeItem(POLLING_CONFIG.LOCAL_STORAGE_KEY)
        setFadingOut(true)
        setTimeout(() => {
          setLoading(false)
          setFadingOut(false)
          setError(err.message)
        }, 400)

        return
      }
    }

    // Max attempts reached
    console.log('Job timed out after maximum attempts')
    localStorage.removeItem(POLLING_CONFIG.LOCAL_STORAGE_KEY)

    trackEvent('validation_error', {
      error_type: 'timeout',
      error_message: 'Validation timed out after 3 minutes'
    })

    setFadingOut(true)
    setTimeout(() => {
      setLoading(false)
      setFadingOut(false)
      setError('Validation timed out. Please try again.')
    }, 400)
  }

  // Handle file selection from UploadArea
  const handleFileSelected = (file) => {
    // Track upload file selection
    trackEvent('upload_file_selected', {
      file_type: file.type,
      file_size: file.size,
      file_name: file.name
    })

    // Show coming soon modal
    setSelectedFile(file)
    setShowComingSoonModal(true)
  }

  // Handle upload area click
  const handleUploadAreaClick = () => {
    trackEvent('upload_area_clicked', {
      interface_source: 'main_page'
    })
  }

  // Handle coming soon modal close
  const handleComingSoonClose = ({ dismissMethod, duration }) => {
    setShowComingSoonModal(false)
    setSelectedFile(null)

    // Track analytics for modal close
    trackEvent('upload_modal_closed', {
      dismiss_method: dismissMethod,
      duration: duration,
      file_type: selectedFile?.type,
      file_size: selectedFile?.size
    })
  }

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        // StarterKit doesn't include underline, so we add it separately
      }),
      Underline,
    ],
    content: `<p style="color: #9ca3af;">Example:</p>
<p style="color: #9ca3af;"></p>
<p style="color: #9ca3af;">Smith, J., & Jones, M. (2023). Understanding research methods. Journal of Academic Studies, 45(2), 123-145. https://doi.org/10.1234/example</p>
<p style="color: #9ca3af;"></p>
<p style="color: #9ca3af;">Brown, A. (2022). Writing in APA style. Academic Press.</p>`,
    editorProps: {
      attributes: {
        class: 'citation-editor',
      },
    },
    onFocus: ({ editor }) => {
      if (hasPlaceholder) {
        editor.commands.setContent('')
        setHasPlaceholder(false)
      }

      // Track editor focus event
      trackEvent('editor_focused', {
        editor_content_length: editor.getText().length,
        has_placeholder: hasPlaceholder
      })

      // Track form abandonment - start timer when editor is focused
      editorFocusedRef.current = true

      // Clear any existing timer
      if (abandonmentTimerRef.current) {
        clearTimeout(abandonmentTimerRef.current)
      }

      // Set new timer for 30 seconds
      const timer = setTimeout(() => {
        // Track form abandonment if editor was focused but no submission occurred
        trackEvent('form_abandoned', {
          time_to_abandon: 30,
          editor_content_length: editor.getText().length
        })
      }, 30000)

      abandonmentTimerRef.current = timer
    },
    onBlur: () => {
      // Clear the abandonment timer when editor loses focus
      if (abandonmentTimerRef.current) {
        clearTimeout(abandonmentTimerRef.current)
        abandonmentTimerRef.current = null
      }
      editorFocusedRef.current = false
    },
    onUpdate: ({ editor, transaction }) => {
      // Track editor content changes for paste and clear events
      if (transaction.docChanged) {
        const currentText = editor.getText()
        const currentLength = currentText.length
        const prevLength = transaction.before?.textContent?.length || 0

        // Track paste events (significant content addition)
        if (transaction.steps.some(step => step.json?.type === 'replace' || step.json?.type === 'insert')) {
          // Check if this is likely a paste event (content length increased significantly)
          if (currentLength > prevLength + 50) { // Threshold for paste vs typing
            trackEvent('editor_paste', {
              content_length_before: prevLength,
              content_length_after: currentLength,
              content_added: currentLength - prevLength
            })
          }
        }

        // Track clear events (content becomes empty or nearly empty)
        // Only fire if previous content was substantial (>50 chars) then became small
        if (prevLength > 50 && (currentLength === 0 || currentLength < 10)) {
          trackEvent('editor_cleared', {
            content_length_before: prevLength,
            content_length_after: currentLength
          })
        }
      }
    },
  })

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (!editor) {
      return
    }

    // Clear abandonment timer on form submission
    if (abandonmentTimerRef.current) {
      clearTimeout(abandonmentTimerRef.current)
      abandonmentTimerRef.current = null
    }

    const token = getToken()
    // Free tier pre-check removed - allows users at limit to see locked results teaser

    const htmlContent = editor.getHTML()
    const textContent = editor.getText()

    
    // Track validation attempt
    trackEvent('validation_attempted', {
      form_content_length: textContent.length,
      interface_source: 'main_page'
    })

    // Capture submitted text for loading state
    setSubmittedText(htmlContent)
    setLoading(true)
    setError(null)
    setResults(null)

    // Reset gated state and initialize tracking data
    setResultsReady(false)
    setResultsRevealed(false)
    setResultsReadyTimestamp(null)
    setIsGated(false)
    setTrackingData({
      jobStartedAt: new Date().toISOString(),
      resultsReadyAt: null,
      resultsRevealedAt: null,
      isGated: false
    })

    try {
      let data

      if (MOCK_MODE) {
        console.log('🎭 MOCK MODE: Simulating API call (10s delay)')
        data = await mockValidationAPI(10000)
      } else {
        console.log('Calling API: /api/validate/async')

        // Build headers
        const headers = { 'Content-Type': 'application/json' }
        if (token) {
          headers['X-User-Token'] = token
        } else {
          // Free tier - send user ID and usage count
          const freeUserId = ensureFreeUserId()
          const freeUsed = getFreeUsage()

          // Add free user ID header if UUID generation succeeded
          if (freeUserId) {
            try {
              headers['X-Free-User-ID'] = btoa(freeUserId)
            } catch (encodingError) {
              console.error('Failed to encode user ID:', encodingError)
              // Send raw UUID as fallback
              headers['X-Free-User-ID'] = freeUserId
            }
          }

          try {
            headers['X-Free-Used'] = btoa(String(freeUsed))
          } catch (encodingError) {
            console.error('Failed to encode usage count:', encodingError)
            headers['X-Free-Used'] = String(freeUsed)
          }
        }

        const response = await fetch('/api/validate/async', {
          method: 'POST',
          headers,
          body: JSON.stringify({
            citations: htmlContent,
            style: 'apa7',
          }),
        })

        console.log('API response status:', response.status)

        if (!response.ok) {
          // Check content-type before calling .json() to avoid "string did not match" errors
          const contentType = response.headers.get('content-type')
          if (contentType?.includes('application/json')) {
            const errorData = await response.json()
            // FastAPI uses 'detail', but support both 'detail' and 'error' keys
            throw new Error(errorData.detail || errorData.error || 'Validation failed')
          } else {
            // Handle non-JSON error responses (502, 504, timeout errors, etc.)
            const text = await response.text()
            throw new Error(`Server error (${response.status}): ${text || 'Request failed'}`)
          }
        }

        const asyncData = await response.json()
        console.log('Async job created:', asyncData)

        // Store job_id in localStorage for recovery
        localStorage.setItem(POLLING_CONFIG.LOCAL_STORAGE_KEY, asyncData.job_id)

        // Start polling for results
        await pollForResults(asyncData.job_id, token)
        return // Exit early, polling will handle results
      }

      console.log('API response data:', data)

      // Sync localStorage with backend's authoritative count
      if (data.free_used_total !== undefined) {
        localStorage.setItem('citation_checker_free_used', String(data.free_used_total))
        console.log(`Updated free usage to: ${data.free_used_total}`)
      }

      // Handle response
      if (data.partial) {
        // Partial results (insufficient credits)
        setResults({ ...data, isPartial: true })

        // Track free limit reached
        const freeUsed = data.free_used_total || getFreeUsage()
        const citationsCount = data.citations_checked + data.citations_remaining
        trackEvent('free_limit_reached', {
          current_usage: freeUsed,
          limit: 10,
          attempted_citations: citationsCount
        })
      } else {
        // Full results
        setResults(data)

        // Track citation validation event
        const citationsCount = data.results.length
        const errorsFound = data.results.reduce((sum, result) => sum + (result.errors?.length || 0), 0)
        const perfectCount = data.results.filter(result => !result.errors || result.errors.length === 0).length
        const userType = token ? 'paid' : 'free'

        trackEvent('citation_validated', {
          citations_count: citationsCount,
          errors_found: errorsFound,
          perfect_count: perfectCount,
          user_type: userType,
          interface_source: 'main_page'
        })

        // Free counter increment removed - now handled by free_used_total sync
      }

      // Refresh credits for paid users (with small delay to ensure state updates)
      if (token) {
        setTimeout(() => {
          refreshCredits().catch(err =>
            console.error('Failed to refresh credits:', err)
          )
        }, 100)
      }
    } catch (err) {
      console.error('API call error:', err)

      // Track validation error
      let errorType = 'unknown'
      if (err.message.includes('fetch')) {
        errorType = 'connection'
      } else if (err.message.includes('Network')) {
        errorType = 'network'
      } else if (err.message.includes('429')) {
        errorType = 'rate_limit'
      } else if (err.message.includes('400')) {
        errorType = 'bad_request'
      } else if (err.message.includes('500')) {
        errorType = 'server_error'
      }

      trackEvent('validation_error', {
        error_type: errorType,
        error_message: err.message.substring(0, 100) // Truncate for privacy
      })

      // User-friendly error messages
      let userMessage = err.message
      if (err.message.includes('fetch')) {
        userMessage = 'Unable to connect to the validation service. Please check if the backend is running.'
      } else if (err.message.includes('Network')) {
        userMessage = 'Network error occurred. Please check your connection and try again.'
      }

      console.log('Displaying user-facing error:', userMessage)

      // Fade out loading state before showing error
      setFadingOut(true)
      setTimeout(() => {
        setLoading(false)
        setFadingOut(false)
        setError(userMessage)
      }, 400) // Match fadeOut animation duration
    } finally {
      // For success case only, disable loading immediately
      // Error case handles loading state in setTimeout above
      if (!error && !fadingOut) {
        setLoading(false)
      }
    }
  }

  return (
    <>
      <div className="app">
        {/* Header */}
        <header className="header">
        <div className="header-content">
          <div className="logo">
            <svg className="logo-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="12" cy="12" r="10" fill="currentColor"/>
              <path d="M7 12L10.5 15.5L17 9" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <h1 className="logo-text">Citation Format Checker</h1>
          </div>
          <CreditDisplay />
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero">
        <div className="hero-content">
          <div className="hero-text">
            <h2 className="hero-title">
              Stop wasting 5 minutes on every{'\u00A0'}citation
            </h2>
            <p className="hero-subtitle">
              The fastest, most accurate APA citation checker.
            </p>
            <div className="hero-stat">
              <span className="stat-text">
                ⚡ Instant validation • Catches citation generator errors • No sign up required
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* Input Section */}
      <section className="input-section">
        <form onSubmit={handleSubmit}>
          <div className="input-layout">
            <div className="editor-column">
              <label>Paste your citations below (APA 7th edition)</label>
              <div data-testid="editor">
                <EditorContent editor={editor} />
              </div>
              <p className="input-helper">
                Paste one or multiple citations. We'll check each one.
              </p>
            </div>

            <div className="upload-column">
              <label>Or upload a document</label>
              <UploadArea onFileSelected={handleFileSelected} onUploadAreaClick={handleUploadAreaClick} />
              <p className="input-helper">
                We'll automatically find & validate citations.
              </p>
            </div>
          </div>

          <div className="button-container">
            <button
              type="submit"
              disabled={loading || !editor || hasPlaceholder}
            >
              {loading ? 'Validating...' : 'Check My Citations'}
            </button>

            <p className="cta-micro-text">
              No login required • Get results in seconds
            </p>
          </div>

          {/* Feature Pills */}
          <div className="feature-pills">
            <span className="feature-pill">✓ Capitalization check</span>
            <span className="feature-pill">✓ Italics validation</span>
            <span className="feature-pill">✓ DOI formatting</span>
            <span className="feature-pill">✓ Punctuation rules</span>
          </div>
        </form>
      </section>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading && submittedText && (
        <div ref={validationSectionRef} className={`validation-results-section ${fadingOut ? 'fade-out' : ''}`}>
          <ValidationLoadingState submittedHtml={submittedText} />
        </div>
      )}

      {results && !loading && (
        <div className="validation-results-section">
          {results.isPartial ? (
            <PartialResults
              results={results.results}
              partial={results.partial}
              citations_checked={results.citations_checked}
              citations_remaining={results.citations_remaining}
              job_id={results.job_id || localStorage.getItem(POLLING_CONFIG.LOCAL_STORAGE_KEY)}
              onUpgrade={() => {
                trackEvent('upgrade_modal_shown', { trigger: 'partial_results' })
                setShowUpgradeModal(true)
              }}
            />
          ) : (
            <div style={{ position: 'relative' }}>
              {/* Always render the validation table */}
              <ValidationTable
                results={results.results}
                style={{
                  filter: isGated && !resultsRevealed && GATED_RESULTS_ENABLED ? 'blur(8px)' : 'none',
                  transition: 'filter 0.3s ease-out',
                  opacity: isGated && !resultsRevealed && GATED_RESULTS_ENABLED ? 0.3 : 1
                }}
              />

              {/* Gated overlay for free users */}
              {isGated && !resultsRevealed && GATED_RESULTS_ENABLED && (
                <GatedResults
                  results={results.results}
                  onReveal={handleRevealResults}
                  trackingData={trackingData}
                  variant={GATED_RESULTS_VARIANT}
                />
              )}
            </div>
          )}
        </div>
      )}

      {/* Why It Works Section */}
      <section className="why-it-works">
        <div className="why-it-works-content">
          <h3 className="why-it-works-title">Why Citation Format Checker Works</h3>
          <div className="featured-bento-refined">
            <div className="featured-hero-refined">
              <h4>Catches 99% of citation errors</h4>
              <p>Our custom AI models are trained exclusively on citation formatting and validate against official APA 7th Edition rules. Significantly more accurate than ChatGPT, Zotero, or EasyBib.</p>
            </div>

            <div className="secondary-gradient secondary-teal">
              <h5>Never lose points</h5>
              <p>Submit with confidence. No more losing grades on formatting mistakes.</p>
            </div>

            <div className="secondary-gradient secondary-emerald">
              <h5>Finds generator mistakes</h5>
              <p>Zotero, EasyBib, and ChatGPT make formatting errors. We catch them before your professor does.</p>
            </div>

            <div className="bottom-card">
              <h6>Custom AI Models</h6>
              <p>Trained on thousands of expert-verified citations for each source type</p>
            </div>

            <div className="bottom-card">
              <h6>APA Expert Verified</h6>
              <p>Every error type validated against official APA 7th Edition manual</p>
            </div>

            <div className="bottom-card">
              <h6>Trusted Worldwide</h6>
              <p>Join thousands of students and academics who rely on us</p>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="faq">
        <div className="faq-content">
          <h3 className="faq-title">Frequently Asked Questions</h3>
          <div className="faq-items">
            <div className="faq-item">
              <h4 className="faq-question">How do I check my APA citations?</h4>
              <p className="faq-answer">
                Simply paste your citations into the text box and click "Check My Citations". Our tool will instantly validate your APA 7th edition citations and highlight any formatting errors.
              </p>
            </div>
            <div className="faq-item">
              <h4 className="faq-question">Is this citation checker free?</h4>
              <p className="faq-answer">
                Yes! You get 10 free citation checks to try the tool. For unlimited checking,
                you can purchase 1,000 Citation Credits for $8.99. Credits never expire.
              </p>
            </div>
            <div className="faq-item">
              <h4 className="faq-question">What citation style does this tool support?</h4>
              <p className="faq-answer">
                Currently, we support APA 7th edition citation style. This is the most current version of APA formatting used by most academic institutions.
              </p>
            </div>
            <div className="faq-item">
              <h4 className="faq-question">What types of errors does this tool catch?</h4>
              <p className="faq-answer">
                Our tool checks for capitalization errors, italics validation, DOI formatting, punctuation rules, author name formatting, and overall APA 7th edition compliance.
              </p>
            </div>
            <div className="faq-item">
              <h4 className="faq-question">Can I check multiple citations at once?</h4>
              <p className="faq-answer">
                Yes! You can paste multiple citations at once, and our tool will check each one individually and provide detailed feedback for each citation.
              </p>
            </div>

            <div className="faq-item">
              <h4 className="faq-question">What are Citation Credits and how do they work?</h4>
              <p className="faq-answer">
                Each citation you check uses 1 credit. When you purchase 1,000 credits for $8.99,
                you can check 1,000 citations. Credits never expire and can be used anytime.
              </p>
            </div>

            <div className="faq-item">
              <h4 className="faq-question">Do Citation Credits expire?</h4>
              <p className="faq-answer">
                No! Your credits never expire. Use them at your own pace — whether that's all at
                once or over several years.
              </p>
            </div>

            <div className="faq-item">
              <h4 className="faq-question">Can I get a refund?</h4>
              <p className="faq-answer">
                Absolutely! We offer a no-questions-asked refund policy. If you're not completely
                satisfied with your Citation Credits purchase, just contact us anytime for a full refund.
              </p>
            </div>

            <div className="faq-item">
              <h4 className="faq-question">How is this different from ChatGPT or citation generators?</h4>
              <p className="faq-answer">
                ChatGPT and tools like Zotero or EasyBib make formatting errors because they're not
                specialized for citation validation. Our AI models are custom-trained exclusively on
                APA 7th Edition rules with expert verification, achieving 99% accuracy.
              </p>
            </div>
          </div>
        </div>
      </section>

      <Footer />

      <UpgradeModal isOpen={showUpgradeModal} onClose={() => setShowUpgradeModal(false)} />
      <ComingSoonModal
        isOpen={showComingSoonModal}
        file={selectedFile}
        onClose={handleComingSoonClose}
      />
    </div>
    </>
  )
}

function App() {
  const pathname = window.location.pathname

  if (pathname === '/debug-html') {
    return <DebugHTMLTest />
  }
  if (pathname === '/dashboard') {
    return (
      <>
        <link rel="stylesheet" href="/src/pages/Dashboard.css" />
        <CreditProvider><Dashboard /></CreditProvider>
      </>
    )
  }
  if (pathname === '/success') {
    return <CreditProvider><Success /></CreditProvider>
  }
  if (pathname === '/privacy') {
    return <CreditProvider><PrivacyPolicy /></CreditProvider>
  }
  if (pathname === '/terms') {
    return <CreditProvider><TermsOfService /></CreditProvider>
  }
  if (pathname === '/contact') {
    return <CreditProvider><ContactUs /></CreditProvider>
  }

  // Default: main app (lets nginx handle PSEO pages)
  return <CreditProvider><AppContent /></CreditProvider>
}

export default App
