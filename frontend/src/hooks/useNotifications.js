/**
 * Custom hook for notifications data.
 * See .ai/architecture.md: hooks/ — polling every 15–30s, no WebSockets.
 * See docs/12_Frontend_Architecture.md §6.
 *
 * Exposes:
 *   notifications  — full list (array)
 *   unreadCount    — integer, derived from notifications
 *   loading        — true only on the initial fetch, not on background polls
 *   error          — last error or null
 *   markAsRead(id) — marks a single notification read and refreshes
 *   markAllAsRead  — marks all read and refreshes
 *   refetch        — manual refresh
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { notificationsAPI } from '../api/notifications';

const POLL_INTERVAL_MS = 30_000; // 30 seconds — within the 15–30s spec range

export const useNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);   // true only on initial load
  const [error, setError] = useState(null);
  const initialFetchDone = useRef(false);

  const fetchNotifications = useCallback(async () => {
    try {
      const response = await notificationsAPI.list();
      // Handle both paginated ({ results: [...] }) and non-paginated responses
      const data = response.data;
      setNotifications(Array.isArray(data) ? data : (data.results ?? []));
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      // Only clear the initial loading spinner once
      if (!initialFetchDone.current) {
        setLoading(false);
        initialFetchDone.current = true;
      }
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const markAsRead = useCallback(async (id) => {
    try {
      await notificationsAPI.markAsRead(id);
      // Optimistic local update: flip is_read without waiting for a full refetch
      setNotifications((prev) =>
        prev.map((n) =>
          n.id === id ? { ...n, is_read: true, read_at: new Date().toISOString() } : n
        )
      );
    } catch (err) {
      setError(err);
      // On error, fall back to a full refresh to ensure consistent state
      fetchNotifications();
    }
  }, [fetchNotifications]);

  const markAllAsRead = useCallback(async () => {
    try {
      await notificationsAPI.markAllAsRead();
      // Optimistic local update
      const now = new Date().toISOString();
      setNotifications((prev) =>
        prev.map((n) => ({ ...n, is_read: true, read_at: n.read_at ?? now }))
      );
    } catch (err) {
      setError(err);
      fetchNotifications();
    }
  }, [fetchNotifications]);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return {
    notifications,
    unreadCount,
    loading,
    error,
    markAsRead,
    markAllAsRead,
    refetch: fetchNotifications,
  };
};
