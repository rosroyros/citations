import { PricingTableCredits } from './PricingTableCredits'

export function PricingTableCreditsDemo() {
  const handleSelect = (productId: string, variant: string) => {
    alert(`Selected: ${productId} (Variant: ${variant})`)
    console.log('Product selected:', { productId, variant })
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-center mb-2">
          Credits Pricing (Variant 1)
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Pay-per-citation model
        </p>

        <PricingTableCredits
          onSelectProduct={handleSelect}
          experimentVariant="1"
        />
      </div>
    </div>
  )
}