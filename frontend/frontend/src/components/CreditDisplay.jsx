import { useCredits } from '../contexts/CreditContext';

export const CreditDisplay = ({ userStatus: propUserStatus }) => {
  const { userStatus: contextUserStatus, loading } = useCredits();

  // Use prop if available (from App.jsx merging logic), otherwise context
  const status = propUserStatus || contextUserStatus;

  // If no status or free user, render nothing (consistent with removing UserStatus for free users)
  if (!status || status.type === 'free') return null;

  if (loading) return <span className="credit-display">Loading...</span>;

  // Show pass status if active
  if (status.type === 'pass') {
    const hours = status.hours_remaining || 0;
    // Round up for days display (e.g. 25h -> 2 days)
    const days = Math.ceil(hours / 24);

    return (
      <div className="credit-display flex flex-col items-end leading-tight">
        <span className="text-brand font-bold">
          {status.pass_product_name ? `${status.pass_product_name} Active` : `${Math.ceil(hours / 24)}-Day Pass Active`}
        </span>
        <span className={`text-xs ${days <= 1 ? 'text-amber-600 font-medium' : 'text-muted-foreground'}`}>
          {days <= 1 ? `${Math.ceil(hours)} hours left` : `${days} days left`}
        </span>
      </div >
    );
  }

  // Show credits
  return (
    <div className="credit-display flex flex-col items-end leading-tight">
      <span className="text-brand font-bold">
        Citation Credits
      </span>
      <span className={`text-xs ${status.balance <= 10 ? 'text-destructive font-medium' : 'text-muted-foreground'}`}>
        {status.balance || 0} remaining
      </span>
    </div>
  );
};