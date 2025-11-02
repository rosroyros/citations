import React from 'react';
import './PartialResults.css';

export function PartialResults({ results, partial, citations_checked, citations_remaining, onUpgrade }) {
  const perfectCount = results.filter(r => r.errors.length === 0).length;
  const needFixesCount = results.filter(r => r.errors.length > 0).length;

  return (
    <div className="results">
      <div className="results-summary">
        <h2>Validation Results</h2>
        <div className="summary-stats">
          <div className="summary-stat">
            <span className="stat-number">{citations_checked}</span>
            <span className="stat-label">Citations Checked</span>
          </div>
          <div className="summary-stat">
            <span className="stat-number">{perfectCount}</span>
            <span className="stat-label">Perfect</span>
          </div>
          <div className="summary-stat">
            <span className="stat-number">{needFixesCount}</span>
            <span className="stat-label">Need Fixes</span>
          </div>
        </div>
      </div>

      {/* Render validated citation results */}
      {results.map((result) => (
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

      {/* Locked results section */}
      {partial && (
        <div className="locked-results">
          <div className="lock-icon">🔒</div>
          <p className="lock-message">
            {citations_remaining} more citation{citations_remaining > 1 ? 's' : ''} checked
          </p>
          <p className="lock-subtitle">Upgrade to see all results</p>
          <button className="upgrade-button" onClick={onUpgrade}>
            Get 1,000 Citation Credits for $8.99
          </button>
        </div>
      )}
    </div>
  );
}