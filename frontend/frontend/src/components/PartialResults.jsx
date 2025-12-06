import React, { useEffect } from 'react';
import './PartialResults.css';
import { useAnalyticsTracking } from '../hooks/useAnalyticsTracking';
import { trackEvent } from '../utils/analytics';
import { getToken } from '../utils/creditStorage';
import ValidationTable from './ValidationTable';

export function PartialResults({ results, partial, citations_checked, citations_remaining, onUpgrade, job_id }) {
  const { trackSourceTypeView } = useAnalyticsTracking();

  // Track partial results viewed (only on component mount)
  useEffect(() => {
    const token = getToken();
    trackEvent('partial_results_viewed', {
      citations_shown: citations_checked,
      citations_locked: citations_remaining,
      user_type: token ? 'paid' : 'free'
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Track source type views when results are displayed
  useEffect(() => {
    results.forEach((result) => {
      if (result.source_type && result.citation_number) {
        trackSourceTypeView(result.source_type, result.citation_number);
      }
    });
  }, [results, trackSourceTypeView]);

  return (
    <div className="partial-results-container" data-testid="partial-results">
      <ValidationTable
        results={results}
        isPartial={true}
        totalSubmitted={citations_checked + citations_remaining}
        citationsRemaining={citations_remaining}
      />

      <div className="upgrade-banner">
        <div className="upgrade-content">
          <h3>🔒 {citations_remaining} more citation{citations_remaining > 1 ? 's' : ''} available</h3>
          <p>Upgrade to see validation results for all your citations</p>
          <button
            onClick={() => {
              trackEvent('upgrade_clicked', {
                trigger_location: 'partial_results',
                citations_locked: citations_remaining
              });

              // Store job_id in localStorage for Polar redirect tracking
              if (job_id) {
                localStorage.setItem('pending_upgrade_job_id', job_id);
              }

              // Call upgrade-event API (non-blocking)
              fetch('/api/upgrade-event', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  event: 'clicked_upgrade',
                  job_id: job_id,
                  trigger_location: 'partial_results',
                  citations_locked: citations_remaining
                })
              }).catch(error => {
                console.error('Error tracking upgrade event:', error);
              });

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