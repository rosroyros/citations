import React, { useEffect } from 'react';
import './PartialResults.css';
import { useAnalyticsTracking } from '../hooks/useAnalyticsTracking';
import ValidationTable from './ValidationTable';

export function PartialResults({ results, partial, citations_checked, citations_remaining, onUpgrade }) {
  const { trackSourceTypeView, trackCTAClick } = useAnalyticsTracking();

  // Track source type views when results are displayed
  useEffect(() => {
    results.forEach((result) => {
      if (result.source_type && result.citation_number) {
        trackSourceTypeView(result.source_type, result.citation_number);
      }
    });
  }, [results, trackSourceTypeView]);

  return (
    <div className="partial-results-container">
      <ValidationTable results={results} />

      <div className="upgrade-banner">
        <div className="upgrade-content">
          <h3>🔒 {citations_remaining} more citation{citations_remaining > 1 ? 's' : ''} available</h3>
          <p>Upgrade to see validation results for all your citations</p>
          <button
            onClick={() => {
              trackCTAClick('Upgrade Now', 'partial_results_upsell');
              onUpgrade();
            }}
            className="upgrade-button"
          >
            Upgrade Now
          </button>
        </div>
      </div>
    </div>
  );
}