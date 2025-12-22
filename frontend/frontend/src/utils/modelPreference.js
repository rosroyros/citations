/**
 * Model preference utility for A/B testing
 * Uses opaque internal IDs to avoid exposing model names directly
 * 
 * Currently using Gemini 3 Flash (model_c) for all users.
 * A/B testing infrastructure preserved for future experiments.
 */

const MODEL_PREFERENCE_KEY = 'model_preference'
const MODEL_A = 'model_a' // OpenAI (Fallback)
const MODEL_B = 'model_b' // Gemini 2.5 Flash (Legacy)
const MODEL_C = 'model_c' // Gemini 3 Flash (Current Default)

/**
 * Get model preference.
 * Currently returns model_c for all users (Gemini 3 Flash).
 * A/B testing infrastructure preserved for future experiments.
 * 
 * @returns {string} - 'model_c' (Gemini 3 Flash)
 */
export const getModelPreference = () => {
  // Currently using Gemini 3 Flash (model_c) for all users
  // To re-enable A/B testing, uncomment below and adjust split logic
  // const stored = localStorage.getItem(MODEL_PREFERENCE_KEY)
  // if (stored && [MODEL_A, MODEL_B, MODEL_C].includes(stored)) {
  //   return stored
  // }
  // const assignment = Math.random() < 0.5 ? MODEL_B : MODEL_A
  // localStorage.setItem(MODEL_PREFERENCE_KEY, assignment)
  // return assignment

  return MODEL_C
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
    case MODEL_C:
      return 'Gemini 3'
    default:
      return 'Unknown'
  }
}