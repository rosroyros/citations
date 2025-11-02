import { useCredits } from '../hooks/useCredits';

export const CreditDisplay = () => {
  const { credits, loading, hasToken } = useCredits();

  if (!hasToken) return null;
  if (loading) return <span className="credit-display">Loading...</span>;

  return (
    <span className="credit-display">
      Citation Credits: {credits || 0}
    </span>
  );
};