import { useState, useEffect } from 'react'
import { trackEvent } from '../utils/analytics'
import { getExperimentVariant } from '../utils/experimentVariant'
import './MiniChecker.css'

/**
 * Get the citation style from various sources (priority order):
 * 1. URL parameter (?style=mla9)
 * 2. data-style attribute on container element
 * 3. Default to 'apa7'
 */
function getStyleFromContext(containerId) {
  // Check URL parameter first
  const urlParams = new URLSearchParams(window.location.search);
  const urlStyle = urlParams.get('style');
  if (urlStyle && (urlStyle === 'apa7' || urlStyle === 'mla9')) {
    return urlStyle;
  }

  // Check data-style attribute on container
  if (containerId) {
    const container = document.getElementById(containerId);
    if (container) {
      const dataStyle = container.getAttribute('data-style');
      if (dataStyle && (dataStyle === 'apa7' || dataStyle === 'mla9')) {
        return dataStyle;
      }
    }
  }

  // Also check for any parent with data-style (for static pages)
  const miniCheckerEl = document.querySelector('.mini-checker[data-style]');
  if (miniCheckerEl) {
    const dataStyle = miniCheckerEl.getAttribute('data-style');
    if (dataStyle && (dataStyle === 'apa7' || dataStyle === 'mla9')) {
      return dataStyle;
    }
  }

  // Default to APA 7
  return 'apa7';
}

/**
 * Get display name for citation style
 */
function getStyleDisplayName(style) {
  return style === 'mla9' ? 'MLA 9th Edition' : 'APA 7th Edition';
}

/**
 * MiniChecker - Embedded citation validation component
 *
 * A lightweight version of the main citation checker designed to be embedded
 * in static content pages. Validates a single citation and provides a CTA
 * to the main checker for bulk validation.
 * 
 * Supports style selection via:
 * - URL parameter: ?style=mla9 or ?style=apa7
 * - data-style attribute on container element
 * - Default: apa7
 */
function MiniChecker({
  placeholder = "Paste your citation here...",
  prefillExample = "",
  onFullChecker = () => window.location.href = '/',
  containerId = null,
  style: propStyle = null
}) {
  const [citation, setCitation] = useState(prefillExample)
  const [isValidating, setIsValidating] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [citationStyle, setCitationStyle] = useState(propStyle || 'apa7')

  // Determine style on mount
  useEffect(() => {
    if (!propStyle) {
      const detectedStyle = getStyleFromContext(containerId);
      setCitationStyle(detectedStyle);
    }
  }, [containerId, propStyle]);

  const handleValidate = async () => {
    if (!citation.trim()) return

    setIsValidating(true)
    setError(null)
    setResult(null)

    // Polling config optimized for single citations (fast validation)
    const POLL_INTERVAL = 500  // 500ms for snappy UX
    const MAX_ATTEMPTS = 60    // 30s timeout (500ms × 60)

    try {
      // Step 1: Create async validation job
      const response = await fetch('/api/validate/async', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Experiment-Variant': getExperimentVariant()
        },
        body: JSON.stringify({
          citations: citation,
          style: citationStyle,
        }),
      })

      if (!response.ok) {
        // Check content-type before calling .json() to avoid "string did not match" errors
        const contentType = response.headers.get('content-type')
        if (contentType?.includes('application/json')) {
          const errorData = await response.json()
          throw new Error(errorData.detail || errorData.error || 'Validation failed')
        } else {
          // Handle non-JSON error responses (502, 504, timeout errors, etc.)
          const text = await response.text()
          throw new Error(`Server error (${response.status}): ${text || 'Request failed'}`)
        }
      }

      const { job_id } = await response.json()

      // Step 2: Poll for completion
      let data = null
      for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
        const statusResponse = await fetch(`/api/jobs/${job_id}`)
        if (!statusResponse.ok) {
          throw new Error('Failed to check validation status')
        }

        const jobData = await statusResponse.json()

        if (jobData.status === 'completed') {
          data = jobData.results
          break
        }
        if (jobData.status === 'failed') {
          throw new Error(jobData.error || 'Validation failed')
        }

        // Wait AFTER check (not before) for faster first response
        if (attempt < MAX_ATTEMPTS - 1) {
          await new Promise(r => setTimeout(r, POLL_INTERVAL))
        }
      }

      if (data === null) {
        throw new Error('Validation timed out. Please try again.')
      }

      // Extract first result (single citation)
      if (data.results && data.results.length > 0) {
        setResult(data.results[0])

        // Track mini checker validation
        trackEvent('mini_checker_validated', {
          citation_length: citation.length,
          citation_style: citationStyle,
          validation_successful: true
        })
      }
    } catch (err) {
      console.error('Validation error:', err)
      setError('Validation failed. Please try again.')

      // Track failed validation
      trackEvent('mini_checker_validated', {
        citation_length: citation.length,
        citation_style: citationStyle,
        validation_successful: false
      })
    } finally {
      setIsValidating(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && e.ctrlKey) {
      handleValidate()
    }
  }

  return (
    <div className="mini-checker">
      <div className="mini-checker-header">
        <h4>Quick Check Your Citation</h4>
        <p>Instantly validate {getStyleDisplayName(citationStyle)} formatting</p>
      </div>

      <div className="mini-checker-form">
        <textarea
          value={citation}
          onChange={(e) => setCitation(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder={placeholder}
          className="mini-checker-input"
          rows={3}
          maxLength={600}
        />

        <div className="mini-checker-actions">
          <button
            onClick={handleValidate}
            disabled={!citation.trim() || isValidating}
            className="mini-checker-button"
          >
            {isValidating ? 'Checking...' : 'Check Citation'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mini-checker-error">
          <p>⚠️ {error}</p>
        </div>
      )}

      {result && (
        <div className={`mini-checker-result ${result.errors.length === 0 ? 'valid' : 'invalid'}`}>
          {result.errors.length === 0 ? (
            <div className="result-valid">
              <p>✅ <strong>No formatting errors found!</strong></p>
              <p>Your citation follows the correct formatting guidelines.</p>
            </div>
          ) : (
            <div className="result-invalid">
              <p>❌ <strong>Found {result.errors.length} formatting issue{result.errors.length > 1 ? 's' : ''}:</strong></p>
              <ul className="error-list">
                {result.errors.map((error, index) => (
                  <li key={index} className="error-item">
                    <strong>{error.component}:</strong> {error.problem}
                    {error.correction && (
                      <div className="error-suggestion">
                        💡 <em>Suggestion: <span dangerouslySetInnerHTML={{ __html: error.correction }} /></em>
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="mini-checker-upsell">
            <p>
              <strong>Check your entire reference list →</strong>
            </p>
            <button
              onClick={() => {
                trackEvent('mini_checker_to_main_clicked', {})
                onFullChecker()
              }}
              className="full-checker-button"
            >
              Open Citation Checker
            </button>
          </div>
        </div>
      )}

      <div className="mini-checker-tips">
        <p>💡 <em>Tip: Press Ctrl+Enter to validate quickly</em></p>
      </div>
    </div>
  )
}

export default MiniChecker
