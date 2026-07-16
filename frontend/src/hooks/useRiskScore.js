/**
 * Custom hook for risk score data.
 * See .ai/architecture.md: hooks/ - useWorkload, useRiskScore, useNotifications.
 */
import { useState, useEffect } from 'react';
import { analyticsAPI } from '../api/analytics';

export const useRiskScore = (projectId) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (projectId) {
      fetchRiskScore();
    }
  }, [projectId]);

  const fetchRiskScore = async () => {
    try {
      setLoading(true);
      const response = await analyticsAPI.getRiskScore(projectId);
      setData(response.data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, refetch: fetchRiskScore };
};
