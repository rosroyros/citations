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
import { PromoPill } from './PromoPill';
import { PROMO_CONFIG } from '../config/promoConfig';

export function PartialResults({ results, partial, citations_checked, citations_remaining, onUpgrade, job_id, results_gated, onReveal, userStatus, inlineResults, orphanCitations }) {
  const [isRevealed, setIsRevealed] = useState(false);
  const [error, setError] = useState(null);
  const [inlineCheckoutSuccess, setInlineCheckoutSuccess] = useState(false);
  const [purchasedProductName, setPurchasedProductName] = useState(null);
  const [purchasedProductPrice, setPurchasedProductPrice] = useState(null);
  const { trackSourceTypeView } = useAnalyticsTracking();
  const { refreshCreditsWithPolling } = useCredits();

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
        interaction_type: "auto",
        promo_enabled: PROMO_CONFIG.enabled,
        promo_text: PROMO_CONFIG.enabled ? PROMO_CONFIG.text : null
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

  // Scroll success modal into view when it appears
  useEffect(() => {
    if (inlineCheckoutSuccess) {
      // Wait for the success UI to render, then scroll it into view
      setTimeout(() => {
        const successElement = document.querySelector('[data-testid="inline-checkout-success"]');
        // Check if scrollIntoView exists (not available in JSDOM tests)
        if (successElement && typeof successElement.scrollIntoView === 'function') {
          successElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 100);
    }
  }, [inlineCheckoutSuccess]);

  const handleReveal = async () => {
    if (onReveal) {
      onReveal();
    }
    setIsRevealed(true);
  };

  // Helper to get product name from product ID
  const getProductName = (productId) => {
    // Map product IDs to display names (must match PricingTableCredits.jsx and PricingTablePasses.jsx)
    const productNames = {
      // Credits (from PricingTableCredits.jsx)
      '817c70f8-6cd1-4bdc-aa80-dd0a43e69a5e': '100 credits',
      '2a3c8913-2e82-4f12-9eb7-767e4bc98089': '500 credits',
      'fe7b0260-e411-4f9a-87c8-0856bf1d8b95': '2,000 credits',
      // Passes (from PricingTablePasses.jsx)
      '1282bd9b-81b6-4f06-a1f2-29bb0be01f26': '1-Day Pass',
      '5b311653-7127-41b5-aed6-496fb713149c': '7-Day Pass',
      'e0bec30d-5576-481e-86f3-d704529651ae': '30-Day Pass'
    };
    return productNames[productId] || 'purchase';
  };

  // Helper to get product price from product ID
  const getProductPrice = (productId) => {
    const productPrices = {
      // Credits (from PricingTableCredits.jsx)
      '817c70f8-6cd1-4bdc-aa80-dd0a43e69a5e': '$1.99',
      '2a3c8913-2e82-4f12-9eb7-767e4bc98089': '$4.99',
      'fe7b0260-e411-4f9a-87c8-0856bf1d8b95': '$9.99',
      // Passes (from PricingTablePasses.jsx)
      '1282bd9b-81b6-4f06-a1f2-29bb0be01f26': '$1.99',
      '5b311653-7127-41b5-aed6-496fb713149c': '$4.99',
      'e0bec30d-5576-481e-86f3-d704529651ae': '$9.99'
    };
    return productPrices[productId] || '';
  };

  // Scroll to editor and focus
  const scrollToEditor = () => {
    // Try multiple selectors for the editor
    const editor = document.querySelector('.ProseMirror') ||
      document.querySelector('.citation-editor') ||
      document.querySelector('[data-testid="citation-input"]');

    if (editor) {
      editor.scrollIntoView({ behavior: 'smooth', block: 'center' });
      editor.focus();
    } else {
      // Fallback: scroll to top of page where editor typically is
      window.scrollTo({ top: 0, behavior: 'smooth' });
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
        // Set success state with product details immediately
        setPurchasedProductName(getProductName(productId));
        setPurchasedProductPrice(getProductPrice(productId));
        setInlineCheckoutSuccess(true);

        // Poll for credit/pass update (handles webhook delay)
        const updated = await refreshCreditsWithPolling();
        if (!updated) {
          console.log('[PartialResults] Credits did not update after polling, user may need to refresh');
        }

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

  // Success state after inline checkout completes (C2 Receipt Light design)
  // Note: Scroll to top is handled centrally in checkoutFlow.js
  if (inlineCheckoutSuccess) {
    return (
      <div className="partial-results-container" data-testid="partial-results">
        <div className="checkout-success-inline" data-testid="inline-checkout-success">
          {/* Header with checkmark */}
          <div className="checkout-success-header">
            <div className="checkout-success-icon">
              <CheckCircle size={28} color="#16a34a" strokeWidth={2.5} />
            </div>
            <h2 className="checkout-success-title">Thank You!</h2>
            <p className="checkout-success-subtitle">Payment Confirmed</p>
          </div>

          {/* Receipt card */}
          <div className="checkout-success-receipt">
            <span className="checkout-success-receipt-label">Purchased</span>
            <div className="checkout-success-receipt-row">
              <span className="checkout-success-product-name">{purchasedProductName}</span>
              <span className="checkout-success-price">{purchasedProductPrice}</span>
            </div>
          </div>

          {/* What's next section */}
          <div className="checkout-success-next">
            <p className="checkout-success-next-title">What's next?</p>
            <ul className="checkout-success-next-list">
              <li>
                <span className="checkout-success-bullet"></span>
                <span>Check your status in the header (top-right)</span>
              </li>
              <li>
                <span className="checkout-success-bullet"></span>
                <span>Re-submit your citations to see full results</span>
              </li>
            </ul>
          </div>

          {/* Support link */}
          <p className="checkout-success-support">
            Questions? <a href="mailto:support@citationformatchecker.com">Contact support</a>
          </p>

          {/* CTA button */}
          <button
            className="checkout-success-button"
            onClick={scrollToEditor}
            data-testid="validate-now-button"
          >
            Validate Again
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
        inlineResults={inlineResults}
        orphanCitations={orphanCitations}
        jobId={job_id}
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
            <PromoPill className="mt-4" onClick={onUpgrade} />
          </div>
        </div>
      )}
    </div>
  );
}