import { useCredits } from '../contexts/CreditContext';

export const CreditDisplay = () => {
  const { credits, activePass, loading, hasToken } = useCredits();

  if (!hasToken) return null;
  if (loading) return <span className="credit-display">Loading...</span>;

  // Show pass status if active
  if (activePass) {
    const hours = Math.ceil(activePass.hours_remaining); // Round up to show full time
    const days = Math.ceil(hours / 24); // Round up so 6.1 days shows as 7 days
    return (
      <span className="credit-display">
        {days > 0 ? `${days}-Day Pass` : `${hours}h Pass`} Active
      </span>
    );
  }

  return (
    <span className="credit-display">
      Citation Credits: {credits || 0}
    </span>
  );
};