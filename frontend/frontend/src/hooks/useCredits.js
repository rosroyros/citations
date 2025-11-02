import { useState, useEffect } from 'react';
import { getToken } from '../utils/creditStorage';

export const useCredits = () => {
  const [credits, setCredits] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const token = getToken();

  const fetchCredits = async () => {
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
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCredits();
  }, [token]);

  return {
    credits,
    loading,
    error,
    refreshCredits: fetchCredits,
    hasToken: !!token
  };
};