import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

// Product configuration
// NOTE: Product IDs are placeholders - will be replaced with real Polar IDs in Phase 4
const PRODUCTS = [
  {
    id: 'prod_pass_1day',
    days: 1,
    price: 1.99,
    pricePerDay: 1.99,
    recommended: false,
    benefits: [
      'Unlimited validations for 24 hours',
      'Up to 1,000 citations per day',
      'APA / MLA / Chicago support',
      'Perfect for finishing a paper'
    ]
  },
  {
    id: 'prod_pass_7day',
    days: 7,
    price: 4.99,
    pricePerDay: 0.71,  // $4.99 / 7 days
    recommended: true,  // This is the tier we want to highlight
    benefits: [
      '7 days of unlimited access',
      'Best value ($0.71/day)',
      'Up to 1,000 citations per day',
      'Export to BibTeX / RIS'
    ]
  },
  {
    id: 'prod_pass_30day',
    days: 30,
    price: 9.99,
    pricePerDay: 0.33,  // $9.99 / 30 days
    recommended: false,
    benefits: [
      '30 days of unlimited access',
      'Lowest daily cost ($0.33/day)',
      'Perfect for ongoing research',
      'Priority support'
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
export function PricingTablePasses({ onSelectProduct, experimentVariant }) {
  return (
    <div className="space-y-4">
      {/* Pricing Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto p-4">
        {PRODUCTS.map(product => (
          <Card
            key={product.id}
            className={
              product.recommended
                ? 'border-primary border-2 shadow-lg relative'
                : 'border-gray-200 relative'
            }
          >
            {/* "Recommended" badge - only shown on recommended tier */}
            {product.recommended && (
              <div className="absolute top-0 right-0 bg-success text-white text-xs font-bold px-3 py-1 rounded-bl-lg rounded-tr-lg">
                Recommended
              </div>
            )}

            {/* Card Header */}
            <CardHeader>
              <CardTitle className="text-2xl font-heading text-heading">
                {product.days}-Day Pass
              </CardTitle>
              <CardDescription className="text-sm font-body text-body">
                ${product.pricePerDay.toFixed(2)} per day
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
                onClick={() => onSelectProduct(product.id, experimentVariant)}
                className="w-full"
                variant={product.recommended ? "default" : "outline"}
              >
                Buy {product.days}-Day Pass
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>

      {/* Fair Use Disclaimer - below all cards */}
      <div className="text-center text-sm font-body text-body max-w-5xl mx-auto px-4">
        <p>
          Fair use: 1,000 citations per day. Passes can be extended anytime.
        </p>
        <p className="text-xs mt-1 opacity-75">
          Buying another pass adds days to your existing pass.
        </p>
      </div>
    </div>
  )
}