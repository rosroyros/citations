import { useState, useEffect, useRef } from 'react'
import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'
import { CreditDisplay } from './components/CreditDisplay'
import { UpgradeModal } from './components/UpgradeModal'
import { PartialResults } from './components/PartialResults'
import Footer from './components/Footer'
import { getToken, getFreeUsage, incrementFreeUsage } from './utils/creditStorage'
import { CreditProvider, useCredits } from './contexts/CreditContext'
import { trackEvent } from './utils/analytics'
import { useAnalyticsTracking } from './hooks/useAnalyticsTracking'
import Success from './pages/Success'
import PrivacyPolicy from './pages/PrivacyPolicy'
import TermsOfService from './pages/TermsOfService'
import ContactUs from './pages/ContactUs'
import './App.css'

function AppContent() {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [hasPlaceholder, setHasPlaceholder] = useState(true)
  const [showUpgradeModal, setShowUpgradeModal] = useState(false)
  const editorFocusedRef = useRef(false)
  const abandonmentTimerRef = useRef(null)
  const { refreshCredits } = useCredits()
  const { trackCTAClick, trackNavigationClick } = useAnalyticsTracking()

  // Cleanup timer on component unmount
  useEffect(() => {
    return () => {
      if (abandonmentTimerRef.current) {
        clearTimeout(abandonmentTimerRef.current)
      }
    }
  }, [])

  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        // Disable underline from StarterKit to avoid duplicate
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
    onBlur: ({ editor }) => {
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

    if (!editor) return

    // Clear abandonment timer on form submission
    if (abandonmentTimerRef.current) {
      clearTimeout(abandonmentTimerRef.current)
      abandonmentTimerRef.current = null
    }

    const token = getToken()
    const freeUsed = getFreeUsage()

    // Check free tier limit
    if (!token && freeUsed >= 10) {
      trackEvent('upgrade_modal_shown', { trigger: 'free_limit' })
      setShowUpgradeModal(true)
      return
    }

    const htmlContent = editor.getHTML()
    const textContent = editor.getText()

    console.log('Form submitted with citations:', textContent)
    console.log('HTML content:', htmlContent)

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      console.log('Calling API: /api/validate')

      // Build headers
      const headers = { 'Content-Type': 'application/json' }
      if (token) {
        headers['X-User-Token'] = token
      }

      const response = await fetch('/api/validate', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          citations: htmlContent,
          style: 'apa7',
        }),
      })

      console.log('API response status:', response.status)

      if (!response.ok) {
        const errorData = await response.json()
        // FastAPI uses 'detail', but support both 'detail' and 'error' keys
        throw new Error(errorData.detail || errorData.error || 'Validation failed')
      }

      const data = await response.json()
      console.log('API response data:', data)

      // Handle response
      if (data.partial) {
        // Partial results (insufficient credits)
        setResults({ ...data, isPartial: true })
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
          user_type: userType
        })

        // Increment free counter if no token
        if (!token) {
          incrementFreeUsage(data.results.length)
        }
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
      setError(userMessage)
    } finally {
      setLoading(false)
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
              Stop wasting 5 minutes on every citation
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
          <div>
            <label>Paste your citations below (APA 7th edition)</label>
            <EditorContent editor={editor} />
            <p className="input-helper">
              Paste one or multiple citations. We'll check each one.
            </p>
          </div>

          <button
            type="submit"
            disabled={loading || !editor || hasPlaceholder}
            onClick={() => {
              if (!loading && editor && !hasPlaceholder) {
                trackCTAClick('Check My Citations', 'main_form')
              }
            }}
          >
            {loading ? 'Validating...' : 'Check My Citations'}
          </button>

          <p className="cta-micro-text">
            No login required • Get results in seconds
          </p>

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
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {results && (
        results.isPartial ? (
          <PartialResults
            results={results.results}
            partial={results.partial}
            citations_checked={results.citations_checked}
            citations_remaining={results.citations_remaining}
            onUpgrade={() => {
              trackEvent('upgrade_modal_shown', { trigger: 'partial_results' })
              setShowUpgradeModal(true)
            }}
          />
        ) : (
          <div className="results">
            <div className="results-summary">
              <h2>Validation Results</h2>
              <div className="summary-stats">
                <div className="summary-stat">
                  <span className="stat-number">{results.results.length}</span>
                  <span className="stat-label">Citations Checked</span>
                </div>
                <div className="summary-stat">
                  <span className="stat-number">
                    {results.results.filter(r => r.errors.length === 0).length}
                  </span>
                  <span className="stat-label">Perfect</span>
                </div>
                <div className="summary-stat">
                  <span className="stat-number">
                    {results.results.filter(r => r.errors.length > 0).length}
                  </span>
                  <span className="stat-label">Need Fixes</span>
                </div>
              </div>
            </div>

            {results.results.map((result) => (
              <div key={result.citation_number} className="citation-result">
                <h3>
                  Citation #{result.citation_number}
                  {result.errors.length === 0 ? ' ✅' : ' ❌'}
                </h3>

                <div className="original-citation">
                  <strong>Original:</strong>
                  <div
                    className="citation-html"
                    dangerouslySetInnerHTML={{ __html: result.original }}
                  />
                </div>

                <div className="source-type">
                  <em>Source type: {result.source_type}</em>
                </div>

                {result.errors.length === 0 ? (
                  <div className="no-errors">
                    <p>✅ No errors found - this citation follows APA 7th edition guidelines!</p>
                  </div>
                ) : (
                  <div className="errors-list">
                    <strong>Errors found:</strong>
                    {result.errors.map((error, index) => (
                      <div key={index} className="error-item">
                        <div className="error-component">
                          <strong>❌ {error.component}:</strong>
                        </div>
                        <div className="error-problem">
                          <em>Problem:</em> {error.problem}
                        </div>
                        <div className="error-correction">
                          <em>Correction:</em> {error.correction}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )
      )}

      {/* Benefits Section */}
      <section className="benefits">
        <div className="benefits-content">
          <h3 className="benefits-title">Why researchers choose Citation Format Checker</h3>
          <div className="benefits-grid">
            <div className="benefit-card">
              <div className="benefit-icon">🎯</div>
              <h4 className="benefit-title">Catches 99% of errors</h4>
              <p className="benefit-text">
                Our AI validates against official APA 7th Edition rules — more accurate than any generator or LLM.
              </p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">🎯</div>
              <h4 className="benefit-title">Catch generator errors</h4>
              <p className="benefit-text">
                Zotero, EasyBib, and ChatGPT make formatting mistakes. We find them before your professor does.
              </p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">✅</div>
              <h4 className="benefit-title">Never lose points</h4>
              <p className="benefit-text">
                Submit with confidence. No more losing grades on formatting mistakes.
              </p>
            </div>
            <div className="benefit-card">
              <div className="benefit-icon">💜</div>
              <h4 className="benefit-title">Trusted by researchers worldwide</h4>
              <p className="benefit-text">
                Join thousands of students and academics who rely on us to perfect their citations.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Why We're Different Section */}
      <section className="why-different">
        <div className="why-different-content">
          <h3 className="why-different-title">Why Citation Format Checker is Different</h3>
          <div className="why-grid">
            <div className="why-card">
              <h4>Custom AI Models</h4>
              <p>Trained on thousands of expert-verified citations for each source type</p>
            </div>
            <div className="why-card">
              <h4>APA Expert Verified</h4>
              <p>Every error type validated against official APA 7th Edition manual</p>
            </div>
            <div className="why-card">
              <h4>99% Accuracy</h4>
              <p>Significantly more accurate than ChatGPT, Zotero, and EasyBib</p>
            </div>
          </div>
          <p className="why-footnote">
            Unlike general AI tools, our models specialize exclusively in citation formatting
          </p>
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
    </div>
    </>
  )
}

function App() {
  const pathname = window.location.pathname

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
