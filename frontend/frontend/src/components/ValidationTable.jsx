import { useState } from 'react'
import './ValidationTable.css'

function ValidationTable({ results, isPartial = false, totalSubmitted = null, citationsRemaining = 0 }) {
  const [expandedRows, setExpandedRows] = useState(() => {
    // Initialize with error rows expanded
    const initial = {}
    results.forEach(result => {
      initial[result.citation_number] = (result.errors?.length || 0) > 0
    })
    return initial
  })

  const toggleRow = (citationNumber) => {
    setExpandedRows(prev => ({
      ...prev,
      [citationNumber]: !prev[citationNumber]
    }))
  }

  const perfectCount = results.filter(r => (r.errors?.length || 0) === 0).length
  const errorCount = results.filter(r => (r.errors?.length || 0) > 0).length

  // Calculate display counts
  const citationCount = results.length

  const handlePartialClick = () => {
    if (isPartial) {
      const upgradeBanner = document.querySelector('.upgrade-banner')
      if (upgradeBanner) {
        upgradeBanner.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
      }
    }
  }

  return (
    <div className="validation-table-container" data-testid="results">
      <div className="table-header">
        <h2>
          Validation Results {isPartial && (
            <span
              className="partial-indicator clickable"
              onClick={handlePartialClick}
              role="button"
              tabIndex={0}
              onKeyPress={(e) => e.key === 'Enter' && handlePartialClick()}
              title="Click to see upgrade options"
            >
              ⚠️ Partial
            </span>
          )}
        </h2>
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
          {isPartial && citationsRemaining > 0 && (
            <>
              <span className="stat-separator">•</span>
              <span className="stat-item stat-remaining">
                <span className="stat-badge remaining">{citationsRemaining}</span>
                remaining
              </span>
            </>
          )}
        </div>
      </div>

      <table className="validation-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Citation</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {results.map((result) => {
            const isExpanded = expandedRows[result.citation_number]
            const hasErrors = (result.errors?.length || 0) > 0

            return (
              <tr
                key={result.citation_number}
                className={`${isExpanded ? 'expanded' : ''} ${hasErrors ? 'has-errors' : ''}`}
              >
                <td>
                  <span className="citation-num">{result.citation_number}</span>
                </td>
                <td>
                  <div
                    className={`citation-text ${!isExpanded ? 'truncated' : ''}`}
                    dangerouslySetInnerHTML={{ __html: result.original }}
                  />
                  <div className="source-type">
                    {result.source_type}
                  </div>

                  {hasErrors && isExpanded && (
                    <div className="error-details">
                      <ul className="error-list">
                        {result.errors.map((error, index) => (
                          <li key={index} className="error-item">
                            <div className="error-component">
                              {error.component}
                            </div>
                            <div className="error-problem">
                              {error.problem}
                            </div>
                            {error.correction && (
                              <div className="error-correction">
                                <strong>Should be:</strong> {error.correction}
                              </div>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </td>
                <td>
                  <div className="status-cell">
                    <div className={`status-icon ${hasErrors ? 'error' : 'success'}`}>
                      {hasErrors ? '✗' : '✓'}
                    </div>
                    <span className="status-text">
                      {hasErrors ? `${result.errors?.length || 0} issue${(result.errors?.length || 0) > 1 ? 's' : ''}` : 'Perfect'}
                    </span>
                  </div>
                </td>
                <td>
                  <button
                    className="action-btn"
                    onClick={() => toggleRow(result.citation_number)}
                    aria-label={isExpanded ? 'Collapse' : 'Expand'}
                  >
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth="2"
                        d={isExpanded ? "M5 15l7-7 7 7" : "M19 9l-7 7-7-7"}
                      />
                    </svg>
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default ValidationTable
