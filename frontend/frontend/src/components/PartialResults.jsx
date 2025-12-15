import React, { useEffect, useState } from 'react';
import './PartialResults.css';
import { useAnalyticsTracking } from '../hooks/useAnalyticsTracking';
import { trackEvent } from '../utils/analytics';
import { getToken } from '../utils/creditStorage';
import ValidationTable from './ValidationTable';
import GatedResults from './GatedResults';

export function PartialResults({ results, partial, citations_checked, citations_remaining, onUpgrade, job_id, results_gated, onReveal, userStatus }) {
  const [isRevealed, setIsRevealed] = useState(false);
  const { trackSourceTypeView } = useAnalyticsTracking();

  // Track partial results viewed (only on component mount)
  useEffect(() => {
    const token = getToken();
    trackEvent('partial_results_viewed', {
      citations_shown: citations_checked,
      citations_locked: citations_remaining,
      user_type: token ? 'paid' : 'free'
    });

    // Track upgrade presented event
    if (job_id) {
      fetch('/api/upgrade-event', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event: 'upgrade_presented',
          job_id: job_id,
          trigger_location: 'partial_results',
          citations_locked: citations_remaining
        })
      }).catch(error => {
        console.error('Error tracking upgrade presentation:', error);
      });
    }
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

  const handleReveal = async () => {
    if (onReveal) {
      onReveal();
    }
    setIsRevealed(true);
  };

  // If gated and not revealed, show GatedResults overlay
  if (results_gated && !isRevealed) {
    return (
      <GatedResults
        results={results}
        onReveal={handleReveal}
        trackingData={{ partial_results: true }}
      />
    );
  }

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
          <h3>{userStatus?.type === 'pass' ? 'Daily limit (1000) reached.' : 'Free tier limit (10) reached.'} Upgrade to continue.</h3>
          <p>{citations_remaining} more citation{citations_remaining > 1 ? 's' : ''} available</p>
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
            Upgrade to Continue
          </button>
        </div>
      </div>
    </div>
  );
}