import React, { useState, useEffect } from 'react';
import { getExperimentVariant, getPricingType } from '../utils/experimentVariant';
import { formatDailyLimitMessage } from '../utils/passStatus';
import { trackEvent } from '../utils/analytics';
import { initiateCheckout } from '../utils/checkoutFlow';
import { useCredits } from '../contexts/CreditContext';
import { PricingTableCredits } from './PricingTableCredits';
import { PricingTablePasses } from './PricingTablePasses';
import './UpgradeModal.css';

/**
 * Upgrade Modal - Orchestrates pricing display based on limit type and variant
 *
 * Props:
 * - limitType: 'credits_exhausted' | 'pass_expired' | 'daily_limit' | 'daily_limit_insufficient' | 'free_limit'
 * - passInfo: {pass_type, expiration_timestamp} if user had pass that expired
 * - resetTimestamp: Unix timestamp of next reset (for daily limit messaging)
 * - dailyRemaining: Citations left in window (for insufficient message)
 * - requestedCitations: How many user tried to validate (for insufficient message)
 *
 * Oracle Feedback #2: Show helpful message for daily_limit_insufficient
 * Oracle Feedback #5: Track variant on clicked_upgrade for conversion analysis
 */
export const UpgradeModal = ({
  isOpen,
  onClose,
  limitType,
  passInfo,
  resetTimestamp,
  dailyRemaining,
  requestedCitations
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [variant, setVariant] = useState(null);
  const [checkoutSuccess, setCheckoutSuccess] = useState(false);
  const { refreshCredits } = useCredits();

  useEffect(() => {
    if (isOpen) {
      // Reset success state when modal opens/reopens
      setCheckoutSuccess(false);
      setError(null);
      setLoading(false);

      // Determine variant when modal opens
      const variantId = getExperimentVariant();
      setVariant(variantId);

      // Track modal shown with variant (Oracle #5)
      trackEvent('upgrade_modal_shown', {
        experiment_variant: variantId,
        limit_type: limitType
      });

      // Truthful event for funnel comparison with inline variants
      trackEvent("pricing_viewed", {
        variant: variantId,
        interaction_type: "active"  // User actively clicked to see this
      });
    }
  }, [isOpen, limitType]);

  const handleSelectProduct = async (productId, experimentVariant) => {
    setLoading(true);
    setError(null);

    // Get job_id from URL params or localStorage
    const urlParams = new URLSearchParams(window.location.search);
    const jobId = urlParams.get('jobId') || localStorage.getItem('pending_upgrade_job_id') || localStorage.getItem('current_job_id');

    await initiateCheckout({
      productId,
      experimentVariant,
      jobId,
      onError: (error) => {
        setError(error.message);
        setLoading(false);
      },
      onSuccess: async () => {
        // Show success state immediately
        setLoading(false);
        setCheckoutSuccess(true);

        // Wait 2 seconds for Polar's order.created webhook to be processed
        await new Promise(resolve => setTimeout(resolve, 2000));
        await refreshCredits();
      },
      onClose: () => {
        // User closed/abandoned checkout - reset loading state
        setLoading(false);
      }
    });
  };

  if (!isOpen || !variant) {
    return null;
  }

  // Render content based on limit type
  const renderContent = () => {
    // Success state after checkout completes (C2 Receipt Light design)
    if (checkoutSuccess) {
      return (
        <div className="checkout-success-container" data-testid="checkout-success">
          {/* Header with checkmark */}
          <div className="checkout-success-header">
            <div className="checkout-success-icon">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
            </div>
            <h2 className="checkout-success-title">Thank You!</h2>
            <p className="checkout-success-subtitle">Payment Confirmed</p>
          </div>

          {/* Receipt card */}
          <div className="checkout-success-receipt">
            <span className="checkout-success-receipt-label">Purchased</span>
            <div className="checkout-success-receipt-row">
              <span className="checkout-success-product-name">7-Day Pass</span>
              <span className="checkout-success-price">$4.99</span>
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
            onClick={() => {
              onClose();
              // Scroll to editor after modal closes
              setTimeout(() => {
                const editor = document.querySelector('.ProseMirror');
                if (editor) {
                  editor.scrollIntoView({ behavior: 'smooth', block: 'center' });
                  editor.focus();
                }
              }, 100);
            }}
            data-testid="continue-button"
          >
            Continue
          </button>
        </div>
      );
    }

    // Oracle Feedback #2: Daily limit insufficient - show helpful message, no pricing
    if (limitType === 'daily_limit_insufficient') {
      return (
        <div className="upgrade-modal-content-centered">
          <button className="upgrade-modal-close-x" onClick={onClose} data-testid="close-modal">×</button>
          <h2 className="upgrade-modal-title">Request Too Large</h2>
          <p className="upgrade-modal-message">
            You have {dailyRemaining} citations remaining in your daily limit.
          </p>
          <p className="upgrade-modal-submessage">
            Please reduce your request to {dailyRemaining} citations or less,
            or wait until {formatDailyLimitMessage(resetTimestamp)}.
          </p>
          <button className="upgrade-modal-close-button" onClick={onClose}>
            Close
          </button>
        </div>
      );
    }

    // Daily limit hit - show reset message, no pricing
    if (limitType === 'daily_limit') {
      return (
        <div className="upgrade-modal-content-centered">
          <button className="upgrade-modal-close-x" onClick={onClose} data-testid="close-modal">×</button>
          <h2 className="upgrade-modal-title">Daily Limit Reached</h2>
          <p className="upgrade-modal-message">
            {formatDailyLimitMessage(resetTimestamp)}
          </p>
          <p className="upgrade-modal-submessage">
            Your pass will allow up to 1,000 citations again after reset.
          </p>
          <button className="upgrade-modal-close-button" onClick={onClose}>
            Close
          </button>
        </div>
      );
    }

    // Pass expired - show passes table (match what they had)
    if (limitType === 'pass_expired' && passInfo) {
      return (
        <div className="upgrade-modal-content-wide">
          <button className="upgrade-modal-close-x" onClick={onClose} data-testid="close-modal">×</button>
          <h2 className="upgrade-modal-title">Your Pass Has Expired</h2>
          <p className="upgrade-modal-message">
            Your {passInfo.pass_type} pass has expired. Renew to continue validating.
          </p>
          <PricingTablePasses
            onCheckout={(productId) => handleSelectProduct(productId, '2')}
            experimentVariant="2"  // Always show passes if they had a pass
          />
        </div>
      );
    }

    // Credits exhausted or free limit - show pricing based on variant
    return (
      <div className="upgrade-modal-content-wide pricing-modal">
        <button className="upgrade-modal-close-x" onClick={onClose} data-testid="close-modal">×</button>
        <h2 className="upgrade-modal-title">
          {limitType === 'credits_exhausted' ? 'Out of Credits' : 'Upgrade for More Access'}
        </h2>
        <p className="upgrade-modal-message">
          {limitType === 'credits_exhausted'
            ? "You've used all your credits. Purchase more to continue."
            : getPricingType(variant) === 'credits'
              ? "Credit never expires. Use them at your own pace."
              : "Unlimited citation validation with the most accurate formatting insights."}
        </p>

        <div className="pricing-table" data-variant={getPricingType(variant)}>
          {getPricingType(variant) === 'credits' ? (
            <PricingTableCredits
              onCheckout={(productId) => handleSelectProduct(productId, variant)}
              experimentVariant={variant}
            />
          ) : (
            <PricingTablePasses
              onCheckout={(productId) => handleSelectProduct(productId, variant)}
              experimentVariant={variant}
            />
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="upgrade-modal-overlay" onClick={onClose}>
      <div className="upgrade-modal-container" onClick={(e) => e.stopPropagation()}>
        {error && (
          <div className="upgrade-modal-error">
            {error}
          </div>
        )}

        {renderContent()}
      </div>
    </div>
  );
};
