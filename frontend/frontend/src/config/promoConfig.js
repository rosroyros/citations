/**
 * Promo Configuration - Single source of truth for seasonal promotions
 * 
 * To update for a new promotion:
 * 1. Set enabled: true
 * 2. Update text, emoji, discountPercent
 * 3. Deploy
 * 
 * To disable promotions:
 * 1. Set enabled: false
 * 2. Deploy
 */
export const PROMO_CONFIG = {
    enabled: true,
    text: "New Year's Deal — 50% Off",
    emoji: { left: "🎉", right: "⏰" },
    discountPercent: 50
}

/**
 * Check if promo is currently active
 */
export function isPromoEnabled() {
    return PROMO_CONFIG.enabled && PROMO_CONFIG.discountPercent > 0
}

/**
 * Get the promo pill content (for PromoPill component)
 * Returns null if promo disabled
 */
export function getPromoContent() {
    if (!isPromoEnabled()) return null
    return {
        text: PROMO_CONFIG.text,
        emoji: PROMO_CONFIG.emoji
    }
}

/**
 * Calculate original (pre-discount) price from current sale price
 * Returns null if promo disabled
 * 
 * @param {number} currentPrice - The discounted price
 * @returns {number|null} - Original price with .99 ending
 */
export function getOriginalPrice(currentPrice) {
    if (!isPromoEnabled()) return null
    const original = currentPrice / (1 - PROMO_CONFIG.discountPercent / 100)
    return Math.ceil(original) - 0.01
}

/**
 * Get button CTA text - DYNAMIC based on discount
 * 
 * @param {string} productTitle - e.g., "7-Day Pass"
 * @returns {string} - "Get 50% Off" or "Buy 7-Day Pass"
 */
export function getButtonText(productTitle) {
    if (isPromoEnabled()) {
        return `Get ${PROMO_CONFIG.discountPercent}% Off`
    }
    return `Buy ${productTitle}`
}
