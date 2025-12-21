/**
 * Shared Checkout Flow Utility
 *
 * Purpose: Centralize checkout logic for use by both modal and inline pricing
 * - Product selection tracking
 * - Checkout creation API call
 * - Embedded checkout via Polar SDK
 * - Success/close/error event handling
 * - Job ID storage for attribution
 *
 * Usage:
 *   import { initiateCheckout } from './utils/checkoutFlow';
 *
 *   // On product selection
 *   initiateCheckout({
 *     productId: 'price_123abc',
 *     experimentVariant: '1.2',
 *     jobId: 'job-456def',
 *     onError: (error) => setError(error.message),
 *     onSuccess: () => console.log('Checkout completed!'),
 *     onClose: () => console.log('User closed checkout')
 *   });
 */

import { PolarEmbedCheckout } from '@polar-sh/checkout/embed';
import { trackEvent } from './analytics';
import { getToken, saveToken } from './creditStorage';

/**
 * Detect user's preferred theme for checkout styling
 * @returns {'light' | 'dark'} Theme based on prefers-color-scheme
 */
function detectTheme() {
  if (typeof window !== 'undefined' && window.matchMedia) {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return 'light';
}

/**
 * Initiate checkout flow for a selected product
 *
 * @param {Object} params - Checkout parameters
 * @param {string} params.productId - Polar product ID (e.g., 'price_123abc')
 * @param {string} params.experimentVariant - A/B test variant (e.g., '1.1', '1.2', '2.1', '2.2')
 * @param {string} [params.jobId] - Job ID for attribution (optional)
 * @param {function} params.onError - Error callback function
 * @param {function} [params.onSuccess] - Success callback - called when checkout completes
 * @param {function} [params.onClose] - Close callback - called when user abandons checkout
 * @returns {Promise<void>}
 */
export async function initiateCheckout({
  productId,
  experimentVariant,
  jobId = null,
  onError,
  onSuccess = null,
  onClose = null
}) {
  try {
    // Track product selection event
    trackEvent('product_selected', {
      product_id: productId,
      experiment_variant: experimentVariant
    });

    // Store job ID for attribution
    if (jobId) {
      localStorage.setItem('pending_upgrade_job_id', jobId);
    }

    // Get user token (uses correct key from creditStorage)
    const token = getToken();

    // Create checkout session
    const response = await fetch('/api/create-checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token,
        productId: productId, // Note: backend expects productId, not product_id
        variantId: experimentVariant,
        job_id: jobId
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    const checkout_url = data.checkout_url;
    const newToken = data.token;

    // Save the new token if returned (critical for user recognition after purchase)
    if (newToken) {
      saveToken(newToken);
    }

    if (!checkout_url) {
      throw new Error('No checkout URL received');
    }

    // Track embed opened event
    trackEvent('checkout_embed_opened', {
      product_id: productId,
      experiment_variant: experimentVariant
    });

    // Detect theme for checkout styling
    const theme = detectTheme();

    // Open embedded checkout
    // Use window mock if available (E2E testing), otherwise use real SDK
    const CheckoutSDK = window.PolarEmbedCheckout || PolarEmbedCheckout;
    // Note: SDK.create() takes (url, theme) where theme is a string, not an object
    const embedCheckout = await CheckoutSDK.create(checkout_url, theme);

    // Handle checkout success
    // Note: SDK uses addEventListener, not .on()
    embedCheckout.addEventListener('success', () => {
      trackEvent('checkout_completed', {
        product_id: productId,
        experiment_variant: experimentVariant
      });

      // Clean up pending job ID
      localStorage.removeItem('pending_upgrade_job_id');

      // Close the embedded checkout iframe
      // This is required when using embed_origin instead of success_url redirect
      embedCheckout.close();

      if (onSuccess) {
        onSuccess();
      }
    });

    // Handle checkout close (user abandonment)
    embedCheckout.addEventListener('close', () => {
      trackEvent('checkout_abandoned', {
        product_id: productId,
        experiment_variant: experimentVariant
      });

      if (onClose) {
        onClose();
      }
    });

  } catch (error) {
    // Track checkout error
    trackEvent('checkout_error', {
      product_id: productId,
      experiment_variant: experimentVariant,
      error_message: error.message
    });

    // Call error callback
    onError(error);

    // Re-throw so callers can also handle the error (e.g., PricingTableCredits shows error UI)
    throw error;
  }
}

/**
 * Get job ID from various sources for attribution
 *
 * @returns {string|null} Job ID if found, null otherwise
 */
export function getJobIdForAttribution() {
  // Try URL params first (most reliable for current session)
  const urlParams = new URLSearchParams(window.location.search);
  const fromUrl = urlParams.get('jobId');
  if (fromUrl) {
    return fromUrl;
  }

  // Try pending upgrade job ID (set during checkout)
  const pendingJobId = localStorage.getItem('pending_upgrade_job_id');
  if (pendingJobId) {
    return pendingJobId;
  }

  // Try current job ID (if validation just completed)
  const currentJobId = localStorage.getItem('current_job_id');
  if (currentJobId) {
    return currentJobId;
  }

  return null;
}