import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { getToken } from '../utils/creditStorage';

const CreditContext = createContext();

// Polling config for post-purchase refresh
const POLL_INTERVAL_MS = 1000;
const MAX_POLL_ATTEMPTS = 10;

export const CreditProvider = ({ children }) => {
  const [credits, setCredits] = useState(null);
  const [activePass, setActivePass] = useState(null);
  const [userStatus, setUserStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const token = getToken();

  // Track baseline values for polling comparison
  const baselineRef = useRef({ credits: null, activePass: null });

  const fetchCredits = useCallback(async () => {
    // Get token fresh each time - important after checkout saves new token
    const currentToken = getToken();
    if (!currentToken) return { credits: null, activePass: null };

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/credits?token=${currentToken}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setCredits(data.credits);
      setActivePass(data.active_pass);
      return { credits: data.credits, activePass: data.active_pass };
    } catch (e) {
      setError(e.message);
      return { credits: null, activePass: null };
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Poll for credit/pass changes after purchase.
   * Keeps checking until values change from baseline or max attempts reached.
   * This handles webhook processing delays from Polar.
   */
  const refreshCreditsWithPolling = useCallback(async () => {
    // Capture baseline before polling starts
    const baseline = {
      credits: credits,
      hasPass: activePass !== null,
      passExpiration: activePass?.expiration_timestamp
    };

    console.log('[CreditContext] Starting polling, baseline:', baseline);

    for (let attempt = 1; attempt <= MAX_POLL_ATTEMPTS; attempt++) {
      // Wait before each attempt (including first, to give webhook time)
      await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS));

      const result = await fetchCredits();

      // Check if credits increased
      if (result.credits !== null && baseline.credits !== null && result.credits > baseline.credits) {
        console.log(`[CreditContext] Credits increased: ${baseline.credits} -> ${result.credits}`);
        return true;
      }

      // Check if a new pass was added or pass was extended
      if (result.activePass !== null) {
        if (!baseline.hasPass) {
          console.log('[CreditContext] New pass detected');
          return true;
        }
        if (result.activePass.expiration_timestamp > baseline.passExpiration) {
          console.log('[CreditContext] Pass extended');
          return true;
        }
      }

      console.log(`[CreditContext] Poll attempt ${attempt}/${MAX_POLL_ATTEMPTS}, no change yet`);
    }

    console.log('[CreditContext] Polling timed out, no change detected');
    return false;
  }, [credits, activePass, fetchCredits]);

  useEffect(() => {
    fetchCredits();
  }, [fetchCredits]);

  // Compute userStatus from credits and activePass
  useEffect(() => {
    if (activePass) {
      setUserStatus({
        type: 'pass',
        pass_type: activePass.pass_type,
        pass_product_name: activePass.pass_product_name, // Propagate explicit name from backend
        expiration_timestamp: activePass.expiration_timestamp,
        hours_remaining: activePass.hours_remaining,
        daily_used: activePass.daily_used || 0,
        daily_limit: activePass.daily_limit || 1000,
        reset_time: activePass.reset_time
      });
    } else if (credits !== null) {
      setUserStatus({
        type: 'credits',
        balance: credits
      });
    } else {
      setUserStatus(null);
    }
  }, [credits, activePass]);

  return (
    <CreditContext.Provider value={{
      credits,
      activePass,
      userStatus,
      loading,
      error,
      refreshCredits: fetchCredits,
      refreshCreditsWithPolling,
      hasToken: !!token
    }}>
      {children}
    </CreditContext.Provider>
  );
};

export const useCredits = () => {
  const context = useContext(CreditContext);
  if (!context) {
    throw new Error('useCredits must be used within CreditProvider');
  }
  return context;
};
