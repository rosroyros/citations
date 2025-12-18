import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useState, useEffect } from "react"
import React from "react"
import { trackEvent } from '../utils/analytics'
import { getToken } from '../utils/creditStorage'

// Product configuration
// Updated with real Polar product IDs from pricing_config.py
const PRODUCTS = [
  {
    id: '817c70f8-6cd1-4bdc-aa80-dd0a43e69a5e',
    title: '100 Credits',
    credits: 100,
    price: 1.99,
    description: 'For occasional users.',
    pricePerCitation: 0.0199,
    recommended: false,
    benefits: [
      'Full APA 7 Compliance',
      'Detailed citation analysis',
      'Actionable error correction feedback',
      'No expiration date'
    ]
  },
  {
    id: '2a3c8913-2e82-4f12-9eb7-767e4bc98089',
    title: '500 Credits',
    credits: 500,
    price: 4.99,
    description: 'Best balance of price & usage.',
    pricePerCitation: 0.00998,
    recommended: true,
    benefits: [
      'Full APA 7 Compliance',
      'Detailed citation analysis',
      'Actionable error correction feedback',
      'No expiration date'
    ]
  },
  {
    id: 'fe7b0260-e411-4f9a-87c8-0856bf1d8b95',
    title: '2,000 Credits',
    credits: 2000,
    price: 9.99,
    description: 'For frequent academic writing.',
    pricePerCitation: 0.004995,
    recommended: false,
    benefits: [
      'Full APA 7 Compliance',
      'Detailed citation analysis',
      'Actionable error correction feedback',
      'No expiration date'
    ]
  }
]

/**
 * Pricing Table for Credits Variant (Variant 1)
 *
 * Design: Pay-per-citation model
 * Positioning:
 * - 100 credits: Entry tier for occasional users
 * - 500 credits: Recommended tier (best value per citation)
 * - 2000 credits: Power user tier
 *
 * A/B Test Hypothesis: Lower price point ($1.99) converts better than single $8.99 option
 */
export function PricingTableCredits({ onSelectProduct, experimentVariant, onCheckout }) {
  const [loadingProductId, setLoadingProductId] = useState(null)
  const [error, setError] = useState(null)

  // Log pricing table shown event
  useEffect(() => {
    console.log('pricing_table_shown', { variant: experimentVariant || '1' })
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
      console.log('product_selected', { productId, variant: experimentVariant || '1' })

      // Get job_id from localStorage if available
      const jobId = localStorage.getItem('pending_upgrade_job_id') || localStorage.getItem('current_job_id')

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
          variantId: experimentVariant || '1',
          job_id: jobId  // Include job_id for upgrade tracking
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
      trackEvent('checkout_started', { productId, checkoutUrl: checkout_url })

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
    <div className="space-y-4">
      {/* Pricing Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto p-4">
        {PRODUCTS.map(product => (
          <Card
            key={product.id}
            className={`flex flex-col relative transition-all duration-200 ${product.recommended
              ? 'border-2 border-purple-600 shadow-xl -translate-y-1 z-10'
              : 'border border-gray-200 hover:-translate-y-1 hover:shadow-md'
              }`}
          >
            {/* "Recommended" badge - only shown on recommended tier */}
            {product.recommended && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-purple-600 text-white text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wide">
                Best Value
              </div>
            )}

            {/* Card Header */}
            <CardHeader className="pb-2">
              <CardTitle className="text-xl font-bold text-gray-900">
                {product.title}
              </CardTitle>
              <CardDescription className="text-gray-500 mt-1 text-sm font-medium">
                {product.description}
              </CardDescription>
            </CardHeader>

            {/* Card Content - Price and Benefits */}
            <CardContent className="flex-1 pt-4">
              {/* Price Display */}
              <div className="mb-4">
                <span className="text-4xl font-bold text-gray-900">
                  ${product.price}
                </span>
              </div>

              {/* Buy Button - Moved above benefits */}
              <div className="mb-6">
                <Button
                  onClick={() => handleCheckout(product.id)}
                  disabled={loadingProductId === product.id}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 rounded-lg transition-colors"
                  variant="default"
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
                    `Buy ${product.title}`
                  )}
                </Button>
              </div>

              {/* Benefits List with Checkmarks */}
              <ul className="space-y-3">
                {product.benefits.map((benefit, idx) => (
                  <li key={idx} className="flex items-start text-sm text-gray-700">
                    <span className="mr-3 text-green-600 font-bold">✓</span>
                    <span>{benefit}</span>
                  </li>
                ))}
              </ul>
            </CardContent>

            {/* Empty footer acting as spacer if needed, or removed */}
            <CardFooter className="pt-0 pb-6">
            </CardFooter>
          </Card>
        ))}
      </div>

      {/* Footer Info */}
      <div className="text-center text-sm font-body text-body max-w-5xl mx-auto px-4 mt-4">
        <p>
          Risk-free with money-back guarantee.
        </p>
      </div>

      {/* Error Display */}
      {error && (
        <div className="text-center text-red-600 mt-4 max-w-5xl mx-auto">
          {error}
        </div>
      )}
    </div>
  )
}