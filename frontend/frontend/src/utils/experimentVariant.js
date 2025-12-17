/**
 * A/B Test Variant Assignment Utility
 *
 * Purpose: Randomly assign users to pricing experiment variants
 * - Variant 1.1: Credits + Button (current control)
 * - Variant 1.2: Credits + Inline (test)
 * - Variant 2.1: Passes + Button (current control)
 * - Variant 2.2: Passes + Inline (test)
 *
 * Design Decision: Assign on first upgrade click, not on page load/validation
 * Rationale: Only count users who expressed purchase intent
 *
 * Storage: localStorage for sticky assignment across sessions
 * Key: 'experiment_v1' (v1 = experiment version 1, for future iterations)
 * Values: '1.1', '1.2', '2.1', '2.2' - obfuscated to prevent tampering
 *
 * Oracle Feedback #5: Track variant on all upgrade funnel events to measure
 * "how many users saw each pricing table" for accurate conversion analysis
 */

// Valid variants for 4-way A/B test
const VALID_VARIANTS = ["1.1", "1.2", "2.1", "2.2"]

/**
 * Get or assign experiment variant
 *
 * Flow:
 * 1. Check localStorage for existing assignment
 * 2. If exists and valid, return it (sticky assignment)
 * 3. If not exists or invalid (including old "1"/"2"), randomly assign 25% split
 * 4. Store in localStorage for future
 * 5. Return variant ID
 *
 * @returns {string} One of: '1.1', '1.2', '2.1', '2.2'
 *
 * @example
 * const variant = getExperimentVariant()
 * if (isInlineVariant(variant)) {
 *   // Show inline pricing
 * } else {
 *   // Show button → modal pricing
 * }
 */
export function getExperimentVariant() {
  // Check if localStorage is available (handles SSR)
  if (typeof localStorage === 'undefined') {
    console.warn('[A/B Test] localStorage not available, defaulting to variant 1.1')
    return '1.1'
  }

  // Check if user already has variant assigned
  let variantId = localStorage.getItem('experiment_v1')

  // If no variant or invalid/old format, assign new
  if (!variantId || !VALID_VARIANTS.includes(variantId)) {
    // Migration: users with old "1"/"2" get re-assigned to fresh 25% split
    // This is intentional to ensure proper distribution across all 4 variants

    // 25% split across 4 variants (0-0.249, 0.25-0.499, 0.5-0.749, 0.75-0.999)
    const random = Math.random()
    if (random < 0.25) {
      variantId = '1.1'  // Credits + Button
    } else if (random < 0.5) {
      variantId = '1.2'  // Credits + Inline
    } else if (random < 0.75) {
      variantId = '2.1'  // Passes + Button
    } else {
      variantId = '2.2'  // Passes + Inline
    }

    // Store for future sessions
    localStorage.setItem('experiment_v1', variantId)

    // Log assignment for debugging
    if (import.meta.env.DEV) {
      console.log(`[A/B Test] New variant assigned: ${variantId} (${getVariantName(variantId)})`)
    }
  } else {
    // Existing assignment - return it
    if (import.meta.env.DEV) {
      console.log(`[A/B Test] Existing variant: ${variantId} (${getVariantName(variantId)})`)
    }
  }

  return variantId
}

/**
 * Check if variant uses inline pricing display
 *
 * Inline variants (ending in .2) show pricing directly without button click
 * Button variants (ending in .1) require button click → modal
 *
 * @param {string} variantId - One of: '1.1', '1.2', '2.1', '2.2'
 * @returns {boolean} true if inline pricing variant
 *
 * @example
 * if (isInlineVariant(variant)) {
 *   // Show pricing inline
 * } else {
 *   // Show button that opens modal
 * }
 */
export function isInlineVariant(variantId) {
  return variantId.endsWith('.2')
}

/**
 * Get pricing type for variant
 *
 * @param {string} variantId - One of: '1.1', '1.2', '2.1', '2.2'
 * @returns {string} 'credits' or 'passes'
 *
 * @example
 * const pricingType = getPricingType(variant)
 * if (pricingType === 'credits') {
 *   // Show credits pricing table
 * } else {
 *   // Show passes pricing table
 * }
 */
export function getPricingType(variantId) {
  return variantId.startsWith('1.') ? 'credits' : 'passes'
}

/**
 * Get human-readable variant name
 *
 * Useful for:
 * - Debugging
 * - Admin dashboards
 * - Logging
 * - User testing
 *
 * @param {string} variantId - One of: '1.1', '1.2', '2.1', '2.2'
 * @returns {string} 'Credits (Button)', 'Credits (Inline)', etc.
 *
 * @example
 * const variant = getExperimentVariant()
 * const name = getVariantName(variant)
 * console.log(`User is in ${name} variant`)
 */
export function getVariantName(variantId) {
  const names = {
    '1.1': 'Credits (Button)',
    '1.2': 'Credits (Inline)',
    '2.1': 'Passes (Button)',
    '2.2': 'Passes (Inline)'
  }
  return names[variantId] || 'Unknown'
}

/**
 * Check if user has been assigned a variant
 *
 * @returns {boolean} true if variant exists in localStorage
 *
 * @example
 * if (hasExperimentVariant()) {
 *   console.log('User already assigned')
 * } else {
 *   console.log('User not yet assigned')
 * }
 */
export function hasExperimentVariant() {
  if (typeof localStorage === 'undefined') {
    return false
  }
  return localStorage.getItem('experiment_v1') !== null
}

/**
 * Reset variant assignment
 *
 * ⚠️ FOR TESTING ONLY - DO NOT expose in production UI
 *
 * Use cases:
 * - Local development testing both variants
 * - QA testing
 * - Manual testing before deployment
 *
 * @example
 * // In browser console during testing:
 * resetExperimentVariant()
 * location.reload()  // See different variant
 */
export function resetExperimentVariant() {
  if (typeof localStorage === 'undefined') {
    console.warn('[A/B Test] localStorage not available')
    return
  }
  localStorage.removeItem('experiment_v1')
  if (import.meta.env.DEV) {
    console.log('[A/B Test] Variant assignment reset - will be reassigned on next call')
  }
}

/**
 * Force set a specific variant (for testing)
 *
 * ⚠️ FOR TESTING/QA ONLY
 *
 * @param {string} variantId - One of: '1.1', '1.2', '2.1', '2.2'
 *
 * @example
 * // Force Credits + Button variant for testing:
 * forceVariant('1.1')
 *
 * // Force Credits + Inline variant for testing:
 * forceVariant('1.2')
 *
 * // Force Passes + Button variant for testing:
 * forceVariant('2.1')
 *
 * // Force Passes + Inline variant for testing:
 * forceVariant('2.2')
 */
export function forceVariant(variantId) {
  if (typeof localStorage === 'undefined') {
    console.warn('[A/B Test] localStorage not available')
    return
  }
  if (!VALID_VARIANTS.includes(variantId)) {
    console.error(`[A/B Test] Invalid variant ID: "${variantId}". Must be one of: ${VALID_VARIANTS.join(', ')}`)
    return
  }
  localStorage.setItem('experiment_v1', variantId)
  if (import.meta.env.DEV) {
    console.log(`[A/B Test] Variant forced to: ${variantId} (${getVariantName(variantId)})`)
  }
}