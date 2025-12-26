import { PROMO_CONFIG } from '../config/promoConfig';

/**
 * PromoPill - Celebratory banner displaying the current promotion
 * Used in: PricingTablePasses, PricingTableCredits, PartialResults, UpgradeModal
 * 
 * @param {string} className - Additional classes for the outer container
 * @param {function} onClick - Optional click handler to make pill interactive
 */
export function PromoPill({ className = '', onClick }) {
    if (!PROMO_CONFIG.enabled) return null;

    const isClickable = typeof onClick === 'function';

    return (
        <div className={`flex justify-center ${className}`}>
            <div
                className={`inline-flex items-center gap-2 sm:gap-3 bg-gradient-to-r from-amber-200 via-amber-100 to-amber-200 border-2 border-amber-400 text-amber-900 px-4 sm:px-6 py-2 sm:py-3 rounded-full text-sm sm:text-base font-bold shadow-md ${isClickable ? 'cursor-pointer hover:shadow-lg hover:scale-105 transition-all duration-200' : ''}`}
                onClick={onClick}
                role={isClickable ? 'button' : undefined}
                tabIndex={isClickable ? 0 : undefined}
                onKeyDown={isClickable ? (e) => { if (e.key === 'Enter' || e.key === ' ') onClick(); } : undefined}
            >
                <span className="text-lg sm:text-xl">{PROMO_CONFIG.emoji.left}</span>
                <span>{PROMO_CONFIG.text}</span>
                <span className="text-lg sm:text-xl">{PROMO_CONFIG.emoji.right}</span>
            </div>
        </div>
    );
}
