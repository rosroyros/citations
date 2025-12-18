import React, { useEffect, useState } from 'react';
import { Lock } from 'lucide-react';
import './PartialResults.css';
import { useAnalyticsTracking } from '../hooks/useAnalyticsTracking';
import { trackEvent } from '../utils/analytics';
import { getToken } from '../utils/creditStorage';
import ValidationTable from './ValidationTable';
import GatedResults from './GatedResults';
import { getExperimentVariant, isInlineVariant, getPricingType } from '../utils/experimentVariant';
import { initiateCheckout } from '../utils/checkoutFlow';
import { PricingTableCredits } from './PricingTableCredits';
import { PricingTablePasses } from './PricingTablePasses';

export function PartialResults({ results, partial, citations_checked, citations_remaining, onUpgrade, job_id, results_gated, onReveal, userStatus }) {
  const [isRevealed, setIsRevealed] = useState(false);
  const [error, setError] = useState(null);
  const { trackSourceTypeView } = useAnalyticsTracking();

  // Get experiment variant
  const variant = getExperimentVariant();
  const showInline = isInlineVariant(variant);
  const pricingType = getPricingType(variant);

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
          citations_locked: citations_remaining,
          variant: variant
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

  // Analytics for inline variants - fire pricing_viewed and clicked events on mount
  useEffect(() => {
    if (showInline) {
      // Truthful event for new analysis
      trackEvent("pricing_viewed", {
        variant,
        interaction_type: "auto"
      });

      // Legacy compatibility - maintain funnel step 2 count
      trackEvent("clicked", {
        variant,
        interaction_type: "auto",
        note: "legacy_funnel_support"
      });
    }
  }, [showInline, variant]);

  const handleReveal = async () => {
    if (onReveal) {
      onReveal();
    }
    setIsRevealed(true);
  };

  // Checkout handler for inline pricing
  const handleCheckout = (productId) => {
    initiateCheckout({
      productId,
      experimentVariant: variant,
      jobId: job_id,
      onError: (err) => setError(err.message)
    });
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

      {showInline ? (
        // Inline pricing variant - show banner text without button + pricing table
        <>
          <div className="upgrade-banner">
            <div className="upgrade-content">
              {userStatus?.type === 'pass' ? (
                <h3>Daily limit reached. Upgrade to continue.</h3>
              ) : (
                <>
                  <div className="upgrade-header-row">
                    <Lock className="lock-icon" size={24} />
                    <h3>{citations_remaining} more citation{citations_remaining > 1 ? 's' : ''} available</h3>
                  </div>
                  <p>Upgrade to unlock validation results & more usage</p>
                </>
              )}
            </div>
          </div>

          <div className="inline-pricing-container">
            {pricingType === 'credits' ? (
              <PricingTableCredits onCheckout={handleCheckout} />
            ) : (
              <PricingTablePasses onCheckout={handleCheckout} />
            )}
          </div>
        </>
      ) : (
        // Button variant - keep existing behavior
        <div className="upgrade-banner">
          <div className="upgrade-content">
            {userStatus?.type === 'pass' ? (
              <h3>Daily limit reached. Upgrade to continue.</h3>
            ) : (
              <>
                <div className="upgrade-header-row">
                  <Lock className="lock-icon" size={24} />
                  <h3>{citations_remaining} more citation{citations_remaining > 1 ? 's' : ''} available</h3>
                </div>
                <p>Upgrade to unlock validation results & more usage</p>
              </>
            )}
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
                    citations_locked: citations_remaining,
                    variant: variant
                  })
                }).catch(error => {
                  console.error('Error tracking upgrade event:', error);
                });

                onUpgrade();
              }}
              className="upgrade-button"
            >
              Upgrade to Unlock Now
            </button>
          </div>
        </div>
      )}
    </div>
  );
}