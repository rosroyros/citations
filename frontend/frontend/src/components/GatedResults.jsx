import { useState } from 'react'
import './GatedResults.css'

function GatedResults({ results = [], onReveal, trackingData = {} }) {
  const [isRevealing, setIsRevealing] = useState(false)

  // Calculate statistics
  const perfectCount = results.filter(r => (r.errors?.length || 0) === 0).length
  const errorCount = results.filter(r => (r.errors?.length || 0) > 0).length
  const citationCount = results.length

  const handleReveal = async (e) => {
    // Prevent form submission if triggered from form
    if (e) {
      e.preventDefault()
      if (e.key === ' ' && e.target) {
        e.preventDefault() // Prevent page scroll on space
      }
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
    <div className="gated-results-container" data-testid="gated-results">
      {/* Table Header with Statistics */}
      <div className="table-header">
        <h2>Validation Results</h2>
        <div className="table-stats">
          <span className="stat-item">
            <strong>{citationCount}</strong> citations
          </span>
          <span className="stat-separator">•</span>
          <span className="stat-item">
            <span className="stat-badge success">{perfectCount}</span>
            perfect
          </span>
          <span className="stat-separator">•</span>
          <span className="stat-item">
            <span className="stat-badge error">{errorCount}</span>
            need fixes
          </span>
        </div>
      </div>

      {/* Gated Content Area */}
      <div className="gated-content">
        {/* Completion Indicator */}
        <div className="completion-indicator">
          <div className="completion-icon">✓</div>
          <div className="completion-text">
            <h3 className="completion-title">Your citation validation is complete</h3>
            <div className="completion-summary">
              <span className="results-ready">Results Ready</span>
              <span className="results-summary">
                {perfectCount} valid • {errorCount} {errorCount === 1 ? 'error' : 'errors'} found
              </span>
            </div>
          </div>
        </div>

        {/* Reveal Button */}
        <div className="reveal-button-container">
          <button
            className={`reveal-button ${isRevealing ? 'loading' : ''}`}
            onClick={handleReveal}
            onKeyDown={handleKeyDown}
            disabled={isRevealing}
            tabIndex="0"
            aria-label={`View Results (${citationCount} citations)`}
          >
            {isRevealing ? (
              <>
                <span className="loading-spinner"></span>
                Loading...
              </>
            ) : (
              `View Results (${citationCount} ${citationCount === 1 ? 'citation' : 'citations'})`
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default GatedResults