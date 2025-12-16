import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useState, useEffect } from "react"
import React from "react"

/**
 * Pricing Table for Credits Variant (Variant 1)
 *
 * Design: Pay-per-citation model
 *
 * Positioning:
 * - 100 credits: Entry tier for occasional users
 * - 500 credits: Recommended tier (best value per citation)
 * - 2000 credits: Power user tier
 *
 * A/B Test Hypothesis: Lower price point ($1.99) converts better than single $8.99 option
 *
 * Props:
 * @param {function} onSelectProduct - Callback when user clicks buy button
 *                                      Signature: (productId, variantId) => void
 * @param {string} experimentVariant - The variant ID ('1' for credits)
 *
 * Usage:
 * <PricingTableCredits
 *   onSelectProduct={(productId, variant) => handlePurchase(productId, variant)}
 *   experimentVariant="1"
 * />
 */
export function PricingTableCredits({ onSelectProduct, experimentVariant }: {
  onSelectProduct?: (productId: string, variantId: string) => void;
  experimentVariant?: string;
}) {
  const [loadingProductId, setLoadingProductId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Log pricing table shown event
  useEffect(() => {
    // TODO: Implement analytics logging
    console.log('pricing_table_shown', { variant: experimentVariant || '1' })
  }, [experimentVariant])

  const handleCheckout = async (productId: string) => {
    setLoadingProductId(productId)
    setError(null)

    try {
      // Log product selection
      console.log('product_selected', { productId, variant: experimentVariant || '1' })

      // Get job_id from URL params or localStorage
      const urlParams = new URLSearchParams(window.location.search);
      const jobId = urlParams.get('jobId') || localStorage.getItem('pending_upgrade_job_id') || localStorage.getItem('current_job_id');

      // Create Polar checkout via backend API
      const response = await fetch('/api/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          productId,
          variantId: experimentVariant || '1',
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

      // Log checkout started
      console.log('checkout_started', { productId, checkoutUrl: checkout_url })

      // Redirect to checkout
      window.location.href = checkout_url
    } catch (err) {
      setError('Failed to open checkout. Please try again.')
      console.error('Checkout error:', err)
    } finally {
      setLoadingProductId(null)
    }
  }
  // Product configuration
  // Updated with real Polar product IDs from pricing_config.py
  const products = [
    {
      id: '817c70f8-6cd1-4bdc-aa80-dd0a43e69a5e',
      credits: 100,
      price: 1.99,
      pricePerCitation: 0.0199,
      recommended: false,
      benefits: [
        '100 citation validations',
        'APA / MLA / Chicago support',
        'Credits never expire',
        'Use anytime at your pace'
      ]
    },
    {
      id: '2a3c8913-2e82-4f12-9eb7-767e4bc98089',
      credits: 500,
      price: 4.99,
      pricePerCitation: 0.00998,  // ~50% cheaper per citation than 100-pack
      recommended: true,  // This is the tier we want to highlight
      benefits: [
        '500 citation validations',
        'Best value ($0.01/citation)',
        'APA / MLA / Chicago support',
        'Export to BibTeX / RIS'
      ]
    },
    {
      id: 'fe7b0260-e411-4f9a-87c8-0856bf1d8b95',
      credits: 2000,
      price: 9.99,
      pricePerCitation: 0.004995,  // ~75% cheaper than 100-pack
      recommended: false,
      benefits: [
        '2,000 citation validations',
        'For heavy academic writing',
        'Lowest per-citation cost',
        'Priority support'
      ]
    }
  ]

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto p-4">
        {products.map(product => (
          <Card
            key={product.id}
            className={
              product.recommended
                ? 'border-primary border-2 shadow-lg relative'
                : 'border-gray-200 relative'
            }
          >
            {/* "Best Value" badge - only shown on recommended tier */}
            {product.recommended && (
              <div className="absolute top-0 right-0 bg-success text-white text-xs font-bold px-3 py-1 rounded-bl-lg rounded-tr-lg">
                Best Value
              </div>
            )}

            {/* Card Header */}
            <CardHeader className="pb-0">
              <CardTitle className="text-xl font-semibold font-heading text-heading">
                {product.credits.toLocaleString()} Credits
              </CardTitle>
              <CardDescription className="text-sm font-body text-body mt-2">
                ${product.pricePerCitation.toFixed(3)} per citation
              </CardDescription>
            </CardHeader>

            {/* Card Content - Price and Benefits */}
            <CardContent className="pt-4">
              {/* Price Display */}
              <div className="mb-4">
                <span className="text-4xl font-bold font-heading text-heading">
                  ${product.price}
                </span>
                <span className="text-body ml-2 text-sm">
                  one-time
                </span>
              </div>

              {/* Benefits List with Checkmarks */}
              <ul className="space-y-2 text-sm font-body">
                {product.benefits.map((benefit, idx) => (
                  <li key={idx} className="flex items-start">
                    {/* Green checkmark icon */}
                    <svg
                      className="w-5 h-5 text-success mr-2 flex-shrink-0 mt-0.5"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    <span className="text-body">{benefit}</span>
                  </li>
                ))}
              </ul>
            </CardContent>

            {/* Card Footer - Buy Button */}
            <CardFooter>
              <Button
                onClick={() => handleCheckout(product.id)}
                disabled={loadingProductId === product.id}
                className="w-full"
                variant={product.recommended ? "default" : "outline"}
              >
                {loadingProductId === product.id ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Opening checkout...
                  </>
                ) : (
                  `Buy ${product.credits.toLocaleString()} Credits`
                )}
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
      {/* Error Display */}
      {error && (
        <div className="text-center text-red-600 mt-4 max-w-5xl mx-auto">
          {error}
        </div>
      )}
    </>
  )
}