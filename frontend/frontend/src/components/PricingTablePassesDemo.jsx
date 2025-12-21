import { useState } from 'react'
import { PricingTablePasses } from './PricingTablePasses'
import { initiateCheckout } from '../utils/checkoutFlow'

export function PricingTablePassesDemo() {
  const [checkoutSuccess, setCheckoutSuccess] = useState(false);
  const [checkoutError, setCheckoutError] = useState(null);

  const handleCheckout = (productId) => {
    initiateCheckout({
      productId,
      experimentVariant: '2',
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
        <div className="max-w-6xl mx-auto text-center">
          <div className="bg-green-100 border-2 border-green-500 rounded-lg p-8 max-w-md mx-auto">
            <h2 className="text-2xl font-bold text-green-700 mb-2">Payment Successful!</h2>
            <p className="text-green-600">Your pass has been activated.</p>
          </div>
        </div>
      </div>
    );
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

        {checkoutError && (
          <div className="text-center text-red-600 mb-4">
            {checkoutError}
          </div>
        )}

        <PricingTablePasses
          onCheckout={handleCheckout}
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