import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

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
          <CardHeader>
            <CardTitle className="text-2xl font-heading text-heading">
              {product.credits} Credits
            </CardTitle>
            <CardDescription className="text-sm font-body text-body">
              ${product.pricePerCitation.toFixed(3)} per citation
            </CardDescription>
          </CardHeader>

          {/* Card Content - Price and Benefits */}
          <CardContent>
            {/* Price Display */}
            <div className="mb-6">
              <span className="text-4xl font-bold font-heading text-heading">
                ${product.price}
              </span>
              <span className="text-body ml-2 text-sm">
                one-time
              </span>
            </div>

            {/* Benefits List with Checkmarks */}
            <ul className="space-y-3 text-sm font-body">
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
              onClick={() => onSelectProduct?.(product.id, experimentVariant || '1')}
              className="w-full"
              variant={product.recommended ? "default" : "outline"}
            >
              Buy {product.credits.toLocaleString()} Credits
            </Button>
          </CardFooter>
        </Card>
      ))}
    </div>
  )
}