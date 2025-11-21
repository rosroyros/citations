import React, { useState } from 'react';
import { getToken } from '../utils/creditStorage.js';
import { trackEvent } from '../utils/analytics';
import './UpgradeModal.css';

export const UpgradeModal = ({ isOpen, onClose }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleCheckout = async () => {
    trackEvent('upgrade_button_clicked', {});
    setLoading(true);
    setError(null);

    try {
      const token = getToken();
      const response = await fetch('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const { checkout_url } = await response.json();

      if (!checkout_url) {
        throw new Error('No checkout URL received');
      }

      // Redirect to Polar checkout
      window.location.href = checkout_url;
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleContentClick = (e) => {
    e.stopPropagation();
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="upgrade-modal-overlay"
      onClick={handleOverlayClick}
      data-testid="upgrade-modal"
    >
      <div
        className="upgrade-modal-content"
        onClick={handleContentClick}
        data-testid="modal-content"
      >
        <button
          className="upgrade-modal-close"
          onClick={onClose}
          aria-label="Close modal"
        >
          ×
        </button>

        <div className="upgrade-modal-header">
          <h2 className="upgrade-modal-title">Get 1,000 Citation Credits</h2>
          <div className="upgrade-modal-price">$8.99</div>
          <p className="upgrade-modal-subtitle">Credits never expire</p>
        </div>

        <div className="upgrade-modal-benefits">
          <div className="upgrade-modal-benefit">
            <span className="upgrade-modal-checkmark">✓</span>
            <span>Check citations for 50+ research papers</span>
          </div>
          <div className="upgrade-modal-benefit">
            <span className="upgrade-modal-checkmark">✓</span>
            <span>Credits never expire - use anytime</span>
          </div>
          <div className="upgrade-modal-benefit">
            <span className="upgrade-modal-checkmark">✓</span>
            <span>Risk-free with money-back guarantee</span>
          </div>
        </div>

        {error && (
          <div className="upgrade-modal-error">
            {error}
          </div>
        )}

        <button
          className="upgrade-modal-button"
          onClick={handleCheckout}
          disabled={loading}
        >
          {loading ? 'Processing...' : 'Continue to Checkout'}
        </button>
      </div>
    </div>
  );
};