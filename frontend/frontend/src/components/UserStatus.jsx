import { Badge } from './ui/badge';
import { useState, useEffect } from 'react';

export const UserStatus = ({ userStatus, className }) => {
  const [timeUntilReset, setTimeUntilReset] = useState('');

  useEffect(() => {
    if (userStatus?.type === 'pass' && userStatus?.reset_time) {
      const updateCountdown = () => {
        const now = Math.floor(Date.now() / 1000);
        const resetTime = userStatus.reset_time;
        const secondsRemaining = Math.max(0, resetTime - now);

        if (secondsRemaining > 0) {
          const hours = Math.floor(secondsRemaining / 3600);
          const minutes = Math.floor((secondsRemaining % 3600) / 60);

          if (hours > 0) {
            setTimeUntilReset(`${hours}h ${minutes}m`);
          } else {
            setTimeUntilReset(`${minutes}m`);
          }
        } else {
          setTimeUntilReset('soon');
        }
      };

      updateCountdown();
      const interval = setInterval(updateCountdown, 60000); // Update every minute

      return () => clearInterval(interval);
    }
  }, [userStatus]);

  if (!userStatus) {
    return null;
  }

  const getStatusContent = () => {
    switch (userStatus.type) {
      case 'credits':
        return {
          text: `${userStatus.balance || 0} credits remaining`,
          variant: userStatus.balance > 10 ? 'success' : userStatus.balance > 0 ? 'warning' : 'destructive'
        };

      case 'pass':
        // Show pass type and time remaining (daily limit is internal, not user-facing)
        const hoursRemaining = userStatus.hours_remaining || 0;
        const daysRemaining = Math.ceil(hoursRemaining / 24);

        return {
          text: `${daysRemaining}-Day Pass`,
          subtext: daysRemaining > 0 ? `${daysRemaining} day${daysRemaining > 1 ? 's' : ''} left` : 'expires today',
          variant: daysRemaining > 3 ? 'success' : daysRemaining > 0 ? 'warning' : 'destructive'
        };


      case 'free':
        return {
          text: 'Free tier',
          variant: 'secondary'
        };

      default:
        return {
          text: 'Unknown status',
          variant: 'outline'
        };
    }
  };

  const status = getStatusContent();

  return (
    <div className={`user-status ${className}`}>
      <Badge variant={status.variant}>
        {status.text}
      </Badge>
      {status.subtext && (
        <span className="user-status-subtext text-xs text-muted-foreground ml-2">
          {status.subtext}
        </span>
      )}
    </div>
  );
};