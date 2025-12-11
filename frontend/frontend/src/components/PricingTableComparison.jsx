import { PricingTableCredits } from './PricingTableCredits'
import { PricingTablePasses } from './PricingTablePasses'

export function PricingTableComparison() {
  const handleSelect = (productId, variant) => {
    alert(`Selected: ${productId} (Variant: ${variant})`)
    console.log('Product selected:', { productId, variant })
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-4">
          A/B Test Pricing Tables
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Comparing Variant 1 (Credits) vs Variant 2 (Passes)
        </p>

        <div className="space-y-16">
          {/* Variant 1: Credits */}
          <div>
            <h2 className="text-2xl font-bold mb-6 text-center">Variant 1: Credits-Based Pricing</h2>
            <PricingTableCredits onSelectProduct={handleSelect} experimentVariant="1" />
          </div>

          {/* Divider */}
          <div className="border-t-4 border-gray-300 pt-16">
            <h2 className="text-2xl font-bold mb-6 text-center">Variant 2: Time-Based Passes</h2>
            <PricingTablePasses onSelectProduct={handleSelect} experimentVariant="2" />
          </div>
        </div>

        {/* Comparison Summary */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="font-bold text-blue-900 mb-4">Credits Model (Variant 1)</h3>
            <ul className="text-sm text-blue-800 space-y-2">
              <li>• Buy X credits, use X credits</li>
              <li>• Credits never expire</li>
              <li>• Best for occasional users</li>
              <li>• Predictable per-citation cost</li>
              <li>• No time pressure</li>
            </ul>
          </div>

          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <h3 className="font-bold text-green-900 mb-4">Passes Model (Variant 2)</h3>
            <ul className="text-sm text-green-800 space-y-2">
              <li>• Unlimited validations during pass</li>
              <li>• Time-limited (1/7/30 days)</li>
              <li>• Best for projects with deadlines</li>
              <li>• Fair use: 1,000 citations/day</li>
              <li>• Passes extend when buying more</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}