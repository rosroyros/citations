/**
 * A/B Test Variant Assignment Utility
 *
 * Purpose: Randomly assign users to pricing experiment variants
 * - Variant 1: Credits (pay-per-citation)
 * - Variant 2: Passes (time-based unlimited)
 *
 * Design Decision: Assign on first upgrade click, not on page load/validation
 * Rationale: Only count users who expressed purchase intent
 *
 * Storage: localStorage for sticky assignment across sessions
 * Key: 'experiment_v1' (v1 = experiment version 1, for future iterations)
 * Values: '1' (credits) or '2' (passes) - obfuscated to prevent tampering
 *
 * Oracle Feedback #5: Track variant on all upgrade funnel events to measure
 * "how many users saw each pricing table" for accurate conversion analysis
 */

/**
 * Get or assign experiment variant
 *
 * Flow:
 * 1. Check localStorage for existing assignment
 * 2. If exists, return it (sticky assignment)
 * 3. If not exists, randomly assign (50/50 split)
 * 4. Store in localStorage for future
 * 5. Return variant ID
 *
 * @returns {string} '1' for Credits variant, '2' for Passes variant
 *
 * @example
 * const variant = getExperimentVariant()
 * if (variant === '1') {
 *   // Show Credits pricing table
 * } else {
 *   // Show Passes pricing table
 * }
 */
export function getExperimentVariant() {
  // Check if localStorage is available (handles SSR)
  if (typeof localStorage === 'undefined') {
    console.warn('[A/B Test] localStorage not available, defaulting to variant 1')
    return '1'
  }

  // Check if user already has variant assigned
  let variantId = localStorage.getItem('experiment_v1')

  if (!variantId) {
    // First time - randomly assign with 50/50 split
    // Math.random() returns 0 to 0.999...
    // < 0.5 gives ~50% chance for variant 1
    // >= 0.5 gives ~50% chance for variant 2
    variantId = Math.random() < 0.5 ? '1' : '2'

    // Store for future sessions
    localStorage.setItem('experiment_v1', variantId)

    // Log assignment for debugging (remove in production if desired)
    console.log(`[A/B Test] New variant assigned: ${variantId} (${variantId === '1' ? 'Credits' : 'Passes'})`)
  } else {
    // Existing assignment - return it
    console.log(`[A/B Test] Existing variant: ${variantId} (${variantId === '1' ? 'Credits' : 'Passes'})`)
  }

  return variantId
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
 * @param {string} variantId - '1' or '2'
 * @returns {string} 'Credits' or 'Passes' or 'Unknown'
 *
 * @example
 * const variant = getExperimentVariant()
 * const name = getVariantName(variant)
 * console.log(`User is in ${name} variant`)
 */
export function getVariantName(variantId) {
  const names = {
    '1': 'Credits',
    '2': 'Passes'
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
  console.log('[A/B Test] Variant assignment reset - will be reassigned on next call')
}

/**
 * Force set a specific variant (for testing)
 *
 * ⚠️ FOR TESTING/QA ONLY
 *
 * @param {string} variantId - '1' or '2'
 *
 * @example
 * // Force Credits variant for testing:
 * forceVariant('1')
 *
 * // Force Passes variant for testing:
 * forceVariant('2')
 */
export function forceVariant(variantId) {
  if (typeof localStorage === 'undefined') {
    console.warn('[A/B Test] localStorage not available')
    return
  }
  if (variantId !== '1' && variantId !== '2') {
    console.error('[A/B Test] Invalid variant ID. Must be "1" or "2"')
    return
  }
  localStorage.setItem('experiment_v1', variantId)
  console.log(`[A/B Test] Variant forced to: ${variantId} (${getVariantName(variantId)})`)
}