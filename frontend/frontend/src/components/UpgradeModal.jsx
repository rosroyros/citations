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
        // Refresh credits after successful purchase
        await refreshCredits();
        setLoading(false);
        setCheckoutSuccess(true);
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
    // Success state after checkout completes
    if (checkoutSuccess) {
      return (
        <div className="upgrade-modal-content-centered" data-testid="checkout-success">
          <div className="upgrade-modal-success-icon">✅</div>
          <h2 className="upgrade-modal-title">Payment Successful!</h2>
          <p className="upgrade-modal-message">
            Your purchase is now active. You can continue validating citations.
          </p>
          <button
            className="upgrade-modal-continue-button"
            onClick={onClose}
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
