import { useCredits } from '../contexts/CreditContext';

export const CreditDisplay = ({ userStatus: propUserStatus }) => {
  const { userStatus: contextUserStatus, loading } = useCredits();

  // Use prop if available (from App.jsx merging logic), otherwise context
  const status = propUserStatus || contextUserStatus;

  if (loading) return <span className="credit-display">Loading...</span>;

  // If no status or free user, render nothing (consistent with removing UserStatus for free users)
  if (!status || status.type === 'free') return null;

  // Show pass status if active
  if (status.type === 'pass') {
    const hours = status.hours_remaining || 0;
    // Round up for days display (e.g. 25h -> 2 days)
    const days = Math.ceil(hours / 24);

    // If hours <= 12, show hours (e.g. "5 hours left")
    // If hours > 12, show days (e.g. "1 day left", "2 days left")

    // We still calculate days for the logic, but display varies
    const showHours = hours <= 12;

    return (
      <div className="credit-display flex flex-col items-end leading-tight">
        <span className="text-brand font-bold">
          {status.pass_product_name ? `${status.pass_product_name} Active` : `${Math.ceil(hours / 24)}-Day Pass Active`}
        </span>
        <span className={`text-xs ${showHours ? 'text-amber-600 font-medium' : 'text-muted-foreground'}`}>
          {showHours
            ? `${Math.ceil(hours)} hours left`
            : `${days} ${days === 1 ? 'day' : 'days'} left`}
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