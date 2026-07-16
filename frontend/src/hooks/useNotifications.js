/**
 * Custom hook for notifications data.
 * See .ai/architecture.md: hooks/ - useWorkload, useRiskScore, useNotifications.
 */
import { useState, useEffect } from 'react';
import { notificationsAPI } from '../api/notifications';

export const useNotifications = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchNotifications();
    // Poll every 30 seconds as per architecture
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      const response = await notificationsAPI.list();
      setData(response.data);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id) => {
    try {
      await notificationsAPI.markAsRead(id);
      fetchNotifications();
    } catch (err) {
      setError(err);
    }
  };

  return { data, loading, error, markAsRead, refetch: fetchNotifications };
};
