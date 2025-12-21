import { useState } from 'react'
import { PricingTableCredits } from './components/PricingTableCredits'
import { initiateCheckout } from './utils/checkoutFlow'

export function TestPricingTable() {
  const [checkoutSuccess, setCheckoutSuccess] = useState(false);
  const [checkoutError, setCheckoutError] = useState(null);

  const handleCheckout = (productId) => {
    initiateCheckout({
      productId,
      experimentVariant: '1',
      jobId: null,
      onError: (err) => setCheckoutError(err.message),
      onSuccess: () => setCheckoutSuccess(true),
      onClose: () => {
        // User closed checkout without completing
      }
    });
  };

  if (checkoutSuccess) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-6xl mx-auto px-4 text-center">
          <div className="bg-green-100 border-2 border-green-500 rounded-lg p-8 max-w-md mx-auto">
            <h2 className="text-2xl font-bold text-green-700 mb-2">Payment Successful!</h2>
            <p className="text-green-600">Your credits have been added.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-6xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-center mb-2">
          Credits Pricing (Variant 1)
        </h1>
        <p className="text-center text-gray-600 mb-8">
          Pay-per-citation model - Test Page
        </p>

        {checkoutError && (
          <div className="text-center text-red-600 mb-4">
            {checkoutError}
          </div>
        )}

        <PricingTableCredits
          experimentVariant="1"
          onCheckout={handleCheckout}
        />
      </div>
    </div>
  )
}