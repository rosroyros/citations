import React, { useEffect, useState } from 'react';
import { Lock, CheckCircle } from 'lucide-react';
import './PartialResults.css';
import { useAnalyticsTracking } from '../hooks/useAnalyticsTracking';
import { trackEvent } from '../utils/analytics';
import { getToken } from '../utils/creditStorage';
import { useCredits } from '../contexts/CreditContext';
import ValidationTable from './ValidationTable';
import GatedResults from './GatedResults';
import { getExperimentVariant, isInlineVariant, getPricingType } from '../utils/experimentVariant';
import { initiateCheckout } from '../utils/checkoutFlow';
import { PricingTableCredits } from './PricingTableCredits';
import { PricingTablePasses } from './PricingTablePasses';

export function PartialResults({ results, partial, citations_checked, citations_remaining, onUpgrade, job_id, results_gated, onReveal, userStatus }) {
  const [isRevealed, setIsRevealed] = useState(false);
  const [error, setError] = useState(null);
  const [inlineCheckoutSuccess, setInlineCheckoutSuccess] = useState(false);
  const [purchasedProductName, setPurchasedProductName] = useState(null);
  const { trackSourceTypeView } = useAnalyticsTracking();
  const { refreshCredits } = useCredits();

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
      // Truthful event for new analysis (GA)
      trackEvent("pricing_viewed", {
        variant,
        interaction_type: "auto"
      });

      // Send to backend for dashboard tracking
      if (job_id) {
        fetch('/api/upgrade-event', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            event: 'pricing_viewed',
            job_id: job_id,
            variant: variant,
            interaction_type: 'auto',
            trigger_location: 'partial_results_inline',
            citations_locked: citations_remaining
          })
        }).catch(error => {
          console.error('Error tracking pricing_viewed:', error);
        });
      }

      // Legacy compatibility - maintain funnel step 2 count
      trackEvent("clicked", {
        variant,
        interaction_type: "auto",
        note: "legacy_funnel_support"
      });
    }
  }, [showInline, variant, job_id, citations_remaining]);

  const handleReveal = async () => {
    if (onReveal) {
      onReveal();
    }
    setIsRevealed(true);
  };

  // Helper to get product name from product ID
  const getProductName = (productId) => {
    // Map product IDs to display names
    const productNames = {
      '29749045-dbb4-4716-8e6c-5a66bd0e8a0e': '100 credits',
      '1d6e5839-c859-4a24-ba7e-48d4555b6823': '500 credits',
      'fe7b0260-e411-4f9a-87c8-0856bf1d8b95': '2000 credits',
      '54e09bb2-3e4c-41a5-a304-ce7db642dbe5': 'Day Pass',
      '76aa138a-e7fe-4815-9a32-f52312e0035d': 'Week Pass',
      '7efb5825-e5df-480a-8f3d-04ce8c5ec01c': 'Month Pass'
    };
    return productNames[productId] || 'purchase';
  };

  // Scroll to editor and focus
  const scrollToEditor = () => {
    const editor = document.querySelector('.ProseMirror');
    if (editor) {
      editor.scrollIntoView({ behavior: 'smooth', block: 'center' });
      editor.focus();
    }
  };

  // Checkout handler for inline pricing
  const handleCheckout = (productId) => {
    initiateCheckout({
      productId,
      experimentVariant: variant,
      jobId: job_id,
      onError: (err) => setError(err.message),
      onSuccess: async () => {
        // Refresh credits after successful purchase
        await refreshCredits();
        // Set success state
        setPurchasedProductName(getProductName(productId));
        setInlineCheckoutSuccess(true);
        // Track success
        trackEvent('inline_checkout_completed', {
          product_id: productId,
          variant: variant
        });
      },
      onClose: () => {
        // User closed/abandoned checkout - already tracked by checkoutFlow.js
      }
    });
  };

  // Success state after inline checkout completes
  if (inlineCheckoutSuccess) {
    return (
      <div className="partial-results-container" data-testid="partial-results">
        <div className="inline-checkout-success" data-testid="inline-checkout-success">
          <CheckCircle className="success-icon" size={48} />
          <h3>Payment Successful!</h3>
          <p>Your {purchasedProductName} is now active.</p>
          <button
            className="validate-now-button"
            onClick={scrollToEditor}
            data-testid="validate-now-button"
          >
            Validate Your Citations Now
          </button>
        </div>
      </div>
    );
  }

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