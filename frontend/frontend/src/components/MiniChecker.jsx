import { useState } from 'react'
import { trackEvent } from '../utils/analytics'
import { getExperimentVariant } from '../utils/experimentVariant'
import './MiniChecker.css'

/**
 * MiniChecker - Embedded citation validation component
 *
 * A lightweight version of the main citation checker designed to be embedded
 * in static content pages. Validates a single citation and provides a CTA
 * to the main checker for bulk validation.
 */
function MiniChecker({
  placeholder = "Paste your citation here...",
  prefillExample = "",
  onFullChecker = () => window.location.href = '/'
}) {
  const [citation, setCitation] = useState(prefillExample)
  const [isValidating, setIsValidating] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleValidate = async () => {
    if (!citation.trim()) return

    setIsValidating(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch('/api/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Experiment-Variant': getExperimentVariant()
        },
        body: JSON.stringify({
          citations: citation,
          style: 'apa7',
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

      const data = await response.json()

      // Extract first result (single citation)
      if (data.results && data.results.length > 0) {
        setResult(data.results[0])

        // Track mini checker validation
        trackEvent('mini_checker_validated', {
          citation_length: citation.length,
          validation_successful: true
        })
      }
    } catch (err) {
      console.error('Validation error:', err)
      setError('Validation failed. Please try again.')

      // Track failed validation
      trackEvent('mini_checker_validated', {
        citation_length: citation.length,
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
        <p>Instantly validate APA formatting</p>
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
              <p>Your citation follows APA 7th edition guidelines.</p>
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
