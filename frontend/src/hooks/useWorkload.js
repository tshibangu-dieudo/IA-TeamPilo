/**
 * Custom hook for workload data.
 * See .ai/architecture.md: hooks/ - useWorkload, useRiskScore, useNotifications.
 */
import { useState, useEffect } from 'react';
import { analyticsAPI } from '../api/analytics';

export const useWorkload = (userId) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (userId) {
      fetchWorkload();
    }
  }, [userId]);

  const fetchWorkload = async () => {
    try {
      setLoading(true);
      const response = await analyticsAPI.getWorkload(userId);
      setData(response.data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, refetch: fetchWorkload };
};
