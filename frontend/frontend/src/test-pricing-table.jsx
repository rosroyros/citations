import { PricingTableCredits } from './components/PricingTableCredits'

export function TestPricingTable() {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-center mb-2">
          Credits Pricing (Variant 1)
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Pay-per-citation model - Test Page
        </p>

        <PricingTableCredits
          experimentVariant="1"
        />
      </div>
    </div>
  )
}