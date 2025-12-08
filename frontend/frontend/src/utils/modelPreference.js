/**
 * Model preference utility for A/B testing
 * Uses opaque internal IDs to avoid exposing model names directly
 */

const MODEL_PREFERENCE_KEY = 'model_preference'
const MODEL_A = 'model_a' // OpenAI (Default)
const MODEL_B = 'model_b' // Gemini (Challenger)

/**
 * Get or assign model preference for A/B testing
 * @returns {string} - 'model_a' or 'model_b'
 */
export const getModelPreference = () => {
  // Check if preference already exists in localStorage
  const stored = localStorage.getItem(MODEL_PREFERENCE_KEY)

  if (stored) {
    // Validate stored value
    if (stored === MODEL_A || stored === MODEL_B) {
      return stored
    }
    // Clear invalid stored value
    localStorage.removeItem(MODEL_PREFERENCE_KEY)
  }

  // Generate new random assignment (50/50 split)
  const assignment = Math.random() < 0.5 ? MODEL_B : MODEL_A

  // Store in localStorage for persistence
  localStorage.setItem(MODEL_PREFERENCE_KEY, assignment)

  return assignment
}

/**
 * Get the human-readable model name for debugging/testing
 * @param {string} modelId - Internal model ID
 * @returns {string} - Human-readable name
 */
export const getModelName = (modelId) => {
  switch (modelId) {
    case MODEL_A:
      return 'OpenAI'
    case MODEL_B:
      return 'Gemini'
    default:
      return 'Unknown'
  }
}