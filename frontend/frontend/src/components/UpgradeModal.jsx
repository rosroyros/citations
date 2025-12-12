import React, { useState, useEffect } from 'react';
import { getExperimentVariant } from '../utils/experimentVariant';
import { formatDailyLimitMessage } from '../utils/passStatus';
import { trackEvent } from '../utils/analytics';
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

  useEffect(() => {
    if (isOpen) {
      // Determine variant when modal opens
      const variantId = getExperimentVariant();
      setVariant(variantId);

      // Track modal shown with variant (Oracle #5)
      trackEvent('upgrade_modal_shown', {
        experiment_variant: variantId,
        limit_type: limitType
      });
    }
  }, [isOpen, limitType]);

  const handleSelectProduct = async (productId, experimentVariant) => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('userToken');

      // Track product selection
      trackEvent('product_selected', {
        product_id: productId,
        experiment_variant: experimentVariant
      });

      // Create checkout
      const response = await fetch('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          productId: productId, // Note: backend expects productId, not product_id
          variantId: experimentVariant
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const { checkout_url } = await response.json();

      if (!checkout_url) {
        throw new Error('No checkout URL received');
      }

      // Redirect to checkout
      window.location.href = checkout_url;

    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  };

  if (!isOpen || !variant) {
    return null;
  }

  // Render content based on limit type
  const renderContent = () => {
    // Oracle Feedback #2: Daily limit insufficient - show helpful message, no pricing
    if (limitType === 'daily_limit_insufficient') {
      return (
        <div className="upgrade-modal-content-centered">
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
          <h2 className="upgrade-modal-title">Your Pass Has Expired</h2>
          <p className="upgrade-modal-message">
            Your {passInfo.pass_type} pass has expired. Renew to continue validating.
          </p>
          <PricingTablePasses
            onSelectProduct={handleSelectProduct}
            experimentVariant="2"  // Always show passes if they had a pass
          />
        </div>
      );
    }

    // Credits exhausted or free limit - show pricing based on variant
    return (
      <div className="upgrade-modal-content-wide pricing-modal">
        <h2 className="upgrade-modal-title">
          {limitType === 'credits_exhausted' ? 'Out of Credits' : 'Upgrade for More Access'}
        </h2>
        <p className="upgrade-modal-message">
          {limitType === 'credits_exhausted'
            ? "You've used all your credits. Purchase more to continue."
            : "Get unlimited citation validations with our affordable pricing."}
        </p>

        <div className="pricing-table" data-variant={variant === '1' ? 'credits' : 'passes'}>
          {variant === '1' ? (
            <PricingTableCredits
              onSelectProduct={handleSelectProduct}
              experimentVariant={variant}
            />
          ) : (
            <PricingTablePasses
              onSelectProduct={handleSelectProduct}
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
        <button className="upgrade-modal-close-x" onClick={onClose} data-testid="close-modal">×</button>

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
