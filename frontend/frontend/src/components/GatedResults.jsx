import { useState } from 'react';
import './GatedResults-landscape1.css';

function GatedResults({ results = [], onReveal, trackingData = {}, variant = 'landscape1' }) {
  const [isRevealing, setIsRevealing] = useState(false)

  // Calculate statistics
  const perfectCount = results.filter(r => (r.errors?.length || 0) === 0).length
  const errorCount = results.filter(r => (r.errors?.length || 0) > 0).length
  const citationCount = results.length

  const handleReveal = async (e) => {
    // Prevent form submission if triggered from form
    if (e) {
      e.preventDefault()
    }

    setIsRevealing(true)

    try {
      await onReveal?.()
    } finally {
      setIsRevealing(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleReveal(e)
    }
  }

  return (
    <div className="gated-results-overlay gated-variant-landscape1" data-testid="gated-results">
      <div className="gated-overlay-backdrop" />
      <div className="gated-overlay-content">
        <div className="completion-indicator">
          <div className="completion-icon">✓</div>
          <div className="completion-text">
            <h3 className="completion-title">Your citation validation is complete</h3>
            <p className="completion-summary">
              {perfectCount} valid • {errorCount} {errorCount === 1 ? 'error' : 'errors'} found
            </p>
          </div>
        </div>
        <div className="reveal-button-container">
          <button
            className={`reveal-button ${isRevealing ? 'loading' : ''}`}
            onClick={handleReveal}
            onKeyDown={handleKeyDown}
            disabled={isRevealing}
            tabIndex="0"
            aria-label={`View Results (${citationCount} citations)`}
          >
            {isRevealing ? 'Loading...' : `View Results (${citationCount} ${citationCount === 1 ? 'citation' : 'citations'})`}
          </button>
        </div>
      </div>
    </div>
  )
}

export default GatedResults
