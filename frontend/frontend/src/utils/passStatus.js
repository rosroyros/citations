/**
 * Pass Status Utilities
 *
 * Handles time calculations for pass display and messaging.
 *
 * Oracle Feedback #3: Use Unix timestamps, not date strings,
 * to avoid timezone confusion.
 */

/**
 * Format pass expiration for display
 *
 * Examples:
 * - "Expires in 2 days"
 * - "Expires in 8 hours"
 * - "Expires in 45 minutes"
 */
export function formatPassExpiration(expirationTimestamp) {
  const now = Math.floor(Date.now() / 1000);
  const secondsRemaining = expirationTimestamp - now;

  if (secondsRemaining <= 0) {
    return "Expired";
  }

  const hours = Math.floor(secondsRemaining / 3600);
  const days = Math.floor(hours / 24);

  if (days > 0) {
    return `Expires in ${days} day${days > 1 ? 's' : ''}`;
  } else if (hours > 0) {
    return `Expires in ${hours} hour${hours > 1 ? 's' : ''}`;
  } else {
    const minutes = Math.floor(secondsRemaining / 60);
    return `Expires in ${minutes} minute${minutes > 1 ? 's' : ''}`;
  }
}

/**
 * Get hours until midnight UTC (for daily limit reset message)
 *
 * Oracle Feedback #3: Store reset_timestamp, calculate hours from that
 */
export function getHoursUntilReset(resetTimestamp) {
  const now = Math.floor(Date.now() / 1000);
  const secondsRemaining = resetTimestamp - now;
  return Math.ceil(secondsRemaining / 3600);
}

/**
 * Format daily limit message
 *
 * Example: "Daily limit reached. Resets at midnight UTC (in 4 hours)"
 */
export function formatDailyLimitMessage(resetTimestamp) {
  const hours = getHoursUntilReset(resetTimestamp);
  return `Daily limit of 1,000 citations reached. Resets at midnight UTC (in ${hours} hour${hours > 1 ? 's' : ''}).`;
}
