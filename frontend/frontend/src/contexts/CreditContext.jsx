import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getToken } from '../utils/creditStorage';

const CreditContext = createContext();

export const CreditProvider = ({ children }) => {
  const [credits, setCredits] = useState(null);
  const [activePass, setActivePass] = useState(null);
  const [userStatus, setUserStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const token = getToken();

  const fetchCredits = useCallback(async () => {
    if (!token) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/credits?token=${token}`);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setCredits(data.credits);
      setActivePass(data.active_pass);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [token]);

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
