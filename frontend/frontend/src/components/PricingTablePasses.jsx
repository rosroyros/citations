import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useState, useEffect } from "react"
import React from "react"
import { trackEvent } from '../utils/analytics'
import { getToken } from '../utils/creditStorage'
import { PromoPill } from './PromoPill'
import { getOriginalPrice, getButtonText, isPromoEnabled } from '../config/promoConfig'

// Product configuration
// Updated with real Polar product IDs from pricing_config.py
const PRODUCTS = [
  {
    id: '1282bd9b-81b6-4f06-a1f2-29bb0be01f26',
    title: '1-Day Pass',
    days: 1,
    price: 1.99,
    description: 'Finish a paper tonight',
    recommended: false,
    perUnit: null,
    benefits: [
      'Full APA 7 Compliance',
      'Detailed citation analysis',
      'Actionable error correction feedback',
      'Risk-free with money-back guarantee'
    ]
  },
  {
    id: '5b311653-7127-41b5-aed6-496fb713149c',
    title: '7-Day Pass',
    days: 7,
    price: 4.99,
    description: 'Best for assignment week',
    recommended: true,  // This is the tier we want to highlight
    perUnit: 'Just $0.71/day',
    benefits: [
      'Full APA 7 Compliance',
      'Detailed citation analysis',
      'Actionable error correction feedback',
      'Risk-free with money-back guarantee'
    ]
  },
  {
    id: 'e0bec30d-5576-481e-86f3-d704529651ae',
    title: '30-Day Pass',
    days: 30,
    price: 9.99,
    description: 'For the whole semester',
    recommended: false,
    perUnit: 'Only $0.33/day',
    benefits: [
      'Full APA 7 Compliance',
      'Detailed citation analysis',
      'Actionable error correction feedback',
      'Risk-free with money-back guarantee'
    ]
  }
]

/**
 * Pricing Table for Passes Variant (Variant 2)
 *
 * Design: Time-based unlimited access (with 1000/day fair use limit)
 *
 * Positioning:
 * - 1-day pass: Quick validation needs (e.g., finishing a paper)
 * - 7-day pass: Recommended for most users (best $/day value)
 * - 30-day pass: Power users, ongoing research projects
 *
 * A/B Test Hypothesis: "Unlimited" messaging converts better than per-citation
 *
 * Oracle Feedback #14: Credits don't kick in when pass hits daily limit
 * (user is blocked until reset - this prevents confusion between access types)
 *
 * Oracle Feedback #15: Passes extend (add days to expiration), don't replace
 * Example: 3 days left + buy 7-day = 10 days total
 *
 * Props:
 * @param {function} onSelectProduct - Callback when user clicks buy button
 *                                      Signature: (productId, variantId) => void
 * @param {string} experimentVariant - The variant ID ('2' for passes)
 *
 * Usage:
 * <PricingTablePasses
 *   onSelectProduct={(productId, variant) => handlePurchase(productId, variant)}
 *   experimentVariant="2"
 * />
 */
export function PricingTablePasses({ onSelectProduct, experimentVariant, onCheckout }) {
  const [loadingProductId, setLoadingProductId] = useState(null)
  const [error, setError] = useState(null)

  // Log pricing table shown event
  useEffect(() => {
    console.log('pricing_table_shown', { variant: experimentVariant || '2' })
  }, [experimentVariant])

  const handleCheckout = async (productId) => {
    // If parent provides onCheckout callback, use it (preserves job_id from parent scope)
    // This is critical for inline variants where job_id is passed from PartialResults
    if (onCheckout) {
      setLoadingProductId(productId)
      setError(null)
      try {
        await onCheckout(productId)
      } catch (err) {
        setError('Failed to open checkout. Please try again.')
        console.error('Checkout error:', err)
      } finally {
        setLoadingProductId(null)
      }
      return
    }

    // Fallback: internal checkout logic for standalone/modal usage
    setLoadingProductId(productId)
    setError(null)

    try {
      // Log product selection
      console.log('product_selected', { productId, variant: experimentVariant || '2' })

      // Get job_id from URL params or localStorage
      const urlParams = new URLSearchParams(window.location.search);
      const jobId = urlParams.get('jobId') || localStorage.getItem('pending_upgrade_job_id') || localStorage.getItem('current_job_id')

      // Call upgrade-event API (non-blocking)
      if (jobId) {
        fetch('/api/upgrade-event', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            event: 'modal_proceed',
            job_id: jobId,
            variant: experimentVariant,
            product_id: productId
          })
        }).catch(error => {
          console.error('Error tracking modal proceed event:', error)
        })
      }

      // Get user token
      const token = getToken()

      // Create Polar checkout via backend API
      const response = await fetch('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          productId,
          variantId: experimentVariant || '2',
          job_id: jobId
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const { checkout_url } = await response.json()

      if (!checkout_url) {
        throw new Error('No checkout URL returned')
      }

      // Track checkout started
      trackEvent('checkout_started', { productId, checkoutUrl: checkout_url, promo_enabled: isPromoEnabled() })

      // Redirect to checkout
      window.location.href = checkout_url
    } catch (err) {
      setError('Failed to open checkout. Please try again.')
      console.error('Checkout error:', err)
    } finally {
      setLoadingProductId(null)
    }
  }
  return (
    <div className="space-y-6">
      {/* Promo Pill - Above cards */}
      <PromoPill className="mb-6" />

      {/* Pricing Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-4xl mx-auto">
        {PRODUCTS.map(product => (
          <Card
            key={product.id}
            className={`flex flex-col relative transition-all duration-200 ${product.recommended
              ? 'border-2 border-purple-600 shadow-xl'
              : 'border border-gray-200 hover:-translate-y-1 hover:shadow-md'
              }`}
          >
            {/* "Most Popular" badge - only shown on recommended tier */}
            {product.recommended && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-purple-600 text-white text-xs font-bold px-4 py-1.5 rounded-full uppercase tracking-wide shadow-md z-10">
                Most Popular
              </div>
            )}

            {/* Card Content - centered layout */}
            <CardContent className="flex-1 flex flex-col text-center pt-8 pb-6">
              {/* Title */}
              <h3 className="text-2xl font-bold text-gray-900 mb-1">{product.title}</h3>

              {/* Description */}
              <p className="text-gray-500 text-sm mb-4">{product.description}</p>

              {/* Price with strikethrough */}
              <div className="mb-5">
                {getOriginalPrice(product.price) && (
                  <span className="text-lg text-gray-400 line-through decoration-1 mr-2">
                    ${getOriginalPrice(product.price).toFixed(2)}
                  </span>
                )}
                <span className="text-4xl font-bold text-gray-900">${product.price}</span>
              </div>

              {/* Buy Button with dynamic text and styling */}
              <Button
                onClick={() => handleCheckout(product.id)}
                disabled={loadingProductId === product.id}
                className={`w-full font-semibold py-3 rounded-lg transition-colors mb-5 ${product.recommended
                  ? 'bg-purple-600 hover:bg-purple-700 text-white'
                  : 'bg-gray-900 hover:bg-gray-800 text-white'}`}
              >
                {loadingProductId === product.id ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Opening checkout...
                  </>
                ) : (
                  getButtonText(product.title)
                )}
              </Button>

              {/* Benefits List with Checkmarks */}
              <ul className="space-y-2 text-left">
                {product.benefits.map((benefit, idx) => (
                  <li key={idx} className="flex items-start text-sm text-gray-600">
                    <span className="mr-2 text-green-600 font-bold">✓</span>
                    <span>{benefit}</span>
                  </li>
                ))}
              </ul>

              {/* Per-unit cost at bottom */}
              <div className="mt-auto pt-4 border-t border-gray-100">
                {product.perUnit ? (
                  <span className="text-sm font-medium text-green-600">{product.perUnit}</span>
                ) : (
                  <span className="text-sm text-gray-400">—</span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Fair Use Disclaimer - below all cards */}
      <div className="text-center text-sm text-gray-500 max-w-4xl mx-auto px-4">
        <p>
          Fair use: 1,000 citations per day. Passes can be extended anytime.
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="text-center text-red-600 mt-4 max-w-4xl mx-auto">
          {error}
        </div>
      )}
    </div>
  )
}