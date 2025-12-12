/**
 * Convert backend error messages to user-friendly messages
 */

export function convertBackendErrorMessage(error) {
  // Handle specific error messages from backend
  if (error.includes('Insufficient credits: need')) {
    // Extract the numbers from the error message
    const match = error.match(/need (\d+), have (\d+)/)
    if (match) {
      const need = match[1]
      const have = match[2]
      return `Request needs ${need} validations but only ${have} remaining today.`
    } else {
      return 'No credits remaining. Purchase more to continue.'
    }
  }

  if (error.includes('Daily citation limit exceeded')) {
    // Backend says "Resets at midnight UTC", convert to user-friendly format
    return 'Daily limit (1000) reached. Resets at midnight UTC.'
  }

  if (error.includes('0 credits')) {
    return 'No credits remaining. Purchase more to continue.'
  }

  if (error.includes('fetch')) {
    return 'Unable to connect to the validation service. Please check if the backend is running.'
  }

  if (error.includes('Network')) {
    return 'Network error occurred. Please check your connection and try again.'
  }

  // Return original error if no specific handling
  return error
}