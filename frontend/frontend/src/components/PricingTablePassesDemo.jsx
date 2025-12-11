import { PricingTablePasses } from './PricingTablePasses'

export function PricingTablePassesDemo() {
  const handleSelect = (productId, variant) => {
    alert(`Selected: ${productId} (Variant: ${variant})`)
    console.log('Product selected:', { productId, variant })
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-2">
          Passes Pricing (Variant 2)
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Time-based unlimited access model
        </p>

        <PricingTablePasses
          onSelectProduct={handleSelect}
          experimentVariant="2"
        />

        <div className="mt-8 max-w-2xl mx-auto bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-bold text-blue-900 mb-2">How Passes Work:</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>✓ Unlimited validations during pass duration</li>
            <li>✓ Fair use limit: 1,000 citations per day</li>
            <li>✓ Buying another pass extends your access (adds days)</li>
            <li>✓ Example: 3 days left + buy 7-day = 10 days total</li>
          </ul>
        </div>
      </div>
    </div>
  )
}