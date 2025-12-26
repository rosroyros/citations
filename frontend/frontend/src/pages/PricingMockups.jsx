import React, { useState } from 'react'
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

// Product data
const PRODUCTS_PASSES = [
    { id: '1', title: '1-Day Pass', days: 1, price: 1.99, originalPrice: 3.99, description: 'Finish a paper tonight', perUnit: null },
    { id: '2', title: '7-Day Pass', days: 7, price: 4.99, originalPrice: 9.99, description: 'Best for assignment week', recommended: true, perUnit: 'Just $0.71/day' },
    { id: '3', title: '30-Day Pass', days: 30, price: 9.99, originalPrice: 19.99, description: 'For the whole semester', perUnit: 'Only $0.33/day' }
]

const PRODUCTS_CREDITS = [
    { id: '1', title: '100 Credits', credits: 100, price: 1.99, originalPrice: 3.99, description: 'For a paper or two', perUnit: '~2¢/citation' },
    { id: '2', title: '500 Credits', credits: 500, price: 4.99, originalPrice: 9.99, description: 'For typical students', recommended: true, perUnit: '~1¢/citation' },
    { id: '3', title: '2,000 Credits', credits: 2000, price: 9.99, originalPrice: 19.99, description: 'Best for researchers', perUnit: '~0.5¢/citation' }
]

const benefits = [
    'Full APA 7 Compliance',
    'Detailed citation analysis',
    'Actionable error correction',
    'Risk-free guarantee'
]

// Celebratory promo pill
function PromoPill() {
    return (
        <div className="inline-flex items-center gap-3 bg-gradient-to-r from-amber-200 via-amber-100 to-amber-200 border-2 border-amber-400 text-amber-900 px-6 py-3 rounded-full text-base font-bold shadow-md">
            <span className="text-xl">🎉</span>
            <span>New Year's Deal — 50% Off</span>
            <span className="text-xl">⏰</span>
        </div>
    )
}

// Pricing cards
function PricingCards({ products }) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5 max-w-4xl mx-auto">
            {products.map(product => (
                <Card
                    key={product.id}
                    className={`flex flex-col relative transition-all duration-200 ${product.recommended
                        ? 'border-2 border-purple-600 shadow-xl'
                        : 'border border-gray-200 hover:-translate-y-1 hover:shadow-md'
                        }`}
                >
                    {product.recommended && (
                        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-purple-600 text-white text-xs font-bold px-4 py-1.5 rounded-full uppercase tracking-wide shadow-md z-10">
                            Most Popular
                        </div>
                    )}
                    <CardContent className="flex-1 flex flex-col text-center pt-8 pb-6">
                        <h3 className="text-2xl font-bold text-gray-900 mb-1">{product.title}</h3>
                        <p className="text-gray-500 text-sm mb-4">{product.description}</p>

                        {/* Price - strikethrough LEFT of price, thinner line */}
                        <div className="mb-5">
                            <span className="text-lg text-gray-400 line-through decoration-1 mr-2">${product.originalPrice.toFixed(2)}</span>
                            <span className="text-4xl font-bold text-gray-900">${product.price}</span>
                        </div>

                        <Button className={`w-full font-semibold py-3 rounded-lg transition-colors mb-5 ${product.recommended
                            ? 'bg-purple-600 hover:bg-purple-700 text-white'
                            : 'bg-gray-900 hover:bg-gray-800 text-white'}`}>
                            Get 50% Off
                        </Button>

                        <ul className="space-y-2 text-left">
                            {benefits.map((benefit, idx) => (
                                <li key={idx} className="flex items-start text-sm text-gray-600">
                                    <span className="mr-2 text-green-600 font-bold">✓</span>
                                    <span>{benefit}</span>
                                </li>
                            ))}
                        </ul>

                        <div className="mt-auto pt-4 border-t border-gray-100">
                            {product.perUnit ? (
                                <span className="text-sm font-medium text-green-600">{product.perUnit}</span>
                            ) : (
                                <span className="text-sm text-gray-400">—</span>
                            )}
                        </div>
                    </CardContent>
                </Card>
            ))}
        </div>
    )
}

// ============================================================
// INLINE VERSION
// ============================================================
function InlineVersion({ products }) {
    return (
        <div className="space-y-6">
            <div className="bg-purple-50/80 p-6 rounded-xl text-center">
                <div className="flex items-center justify-center gap-3 mb-2">
                    <span className="text-2xl">🔒</span>
                    <h3 className="text-xl font-bold text-gray-900">1 more citation available</h3>
                </div>
                <p className="text-gray-600">Upgrade to unlock validation results & more usage</p>
            </div>

            <div className="flex justify-center">
                <PromoPill />
            </div>

            <PricingCards products={products} />

            <div className="text-center text-sm text-gray-500">
                Risk-free with money-back guarantee
            </div>
        </div>
    )
}

// ============================================================
// MODAL VERSION - Stage 1: Banner with button (before clicking)
// Promo BELOW the button, button is wider
// ============================================================
function ModalBannerStage({ onUpgrade }) {
    return (
        <div className="bg-purple-50/80 p-8 rounded-2xl text-center space-y-5">
            <div className="flex items-center justify-center gap-3">
                <span className="text-3xl">🔒</span>
                <h3 className="text-2xl font-bold text-gray-900">1 more citation available</h3>
            </div>
            <p className="text-gray-600 text-lg">Upgrade to unlock validation results & more usage</p>

            {/* Wider button */}
            <button
                onClick={onUpgrade}
                className="bg-purple-500 hover:bg-purple-600 text-white font-medium text-lg px-16 py-4 rounded-xl transition-colors shadow-sm"
            >
                Upgrade to Unlock Now
            </button>

            {/* Promo BELOW button */}
            <div className="flex justify-center pt-2">
                <PromoPill />
            </div>
        </div>
    )
}

// ============================================================
// MODAL VERSION - Stage 2: Pricing cards (after clicking upgrade)
// ============================================================
function ModalPricingStage({ products }) {
    return (
        <div className="space-y-6">
            {/* Promo pill above cards */}
            <div className="flex justify-center">
                <PromoPill />
            </div>

            <PricingCards products={products} />

            <div className="text-center text-sm text-gray-500">
                Risk-free with money-back guarantee
            </div>
        </div>
    )
}

// ============================================================
// Main Page
// ============================================================
export default function PricingMockups() {
    const [productType, setProductType] = useState('passes')
    const [modalStage, setModalStage] = useState('banner') // 'banner' or 'pricing'
    const products = productType === 'passes' ? PRODUCTS_PASSES : PRODUCTS_CREDITS

    return (
        <div className="min-h-screen bg-gray-100 py-8">
            <div className="max-w-5xl mx-auto px-4">
                {/* Header */}
                <div className="text-center mb-6">
                    <h1 className="text-3xl font-bold text-gray-900">Final Pricing Design</h1>
                    <p className="text-gray-600 mt-2">Inline vs Modal (with stage toggle)</p>
                </div>

                {/* Product toggle */}
                <div className="flex justify-center gap-3 mb-8">
                    <button
                        onClick={() => setProductType('passes')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${productType === 'passes' ? 'bg-purple-600 text-white' : 'bg-white text-gray-700 border border-gray-200'
                            }`}
                    >
                        Passes
                    </button>
                    <button
                        onClick={() => setProductType('credits')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${productType === 'credits' ? 'bg-purple-600 text-white' : 'bg-white text-gray-700 border border-gray-200'
                            }`}
                    >
                        Credits
                    </button>
                </div>

                {/* Updates */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-8 text-sm text-green-800">
                    <strong>Fixed:</strong> Strikethrough back inline (left of price, thinner) • Modal promo below button • Wider button • Modal shows both stages
                </div>

                {/* Versions */}
                <div className="space-y-12">
                    {/* Inline */}
                    <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
                        <div className="bg-gray-800 text-white px-6 py-4">
                            <h2 className="text-lg font-bold">Inline Version</h2>
                            <p className="text-gray-300 text-sm">Shows after partial results</p>
                        </div>
                        <div className="p-6">
                            <InlineVersion products={products} />
                        </div>
                    </div>

                    {/* Modal Version with stage toggle */}
                    <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
                        <div className="bg-gray-800 text-white px-6 py-4 flex items-center justify-between">
                            <div>
                                <h2 className="text-lg font-bold">Modal Version</h2>
                                <p className="text-gray-300 text-sm">Two stages: Banner → Pricing</p>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setModalStage('banner')}
                                    className={`px-3 py-1.5 rounded text-xs font-medium ${modalStage === 'banner' ? 'bg-purple-500 text-white' : 'bg-gray-600 text-gray-300'
                                        }`}
                                >
                                    1. Banner
                                </button>
                                <button
                                    onClick={() => setModalStage('pricing')}
                                    className={`px-3 py-1.5 rounded text-xs font-medium ${modalStage === 'pricing' ? 'bg-purple-500 text-white' : 'bg-gray-600 text-gray-300'
                                        }`}
                                >
                                    2. Pricing
                                </button>
                            </div>
                        </div>
                        <div className="p-6">
                            {modalStage === 'banner' ? (
                                <ModalBannerStage onUpgrade={() => setModalStage('pricing')} />
                            ) : (
                                <ModalPricingStage products={products} />
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
