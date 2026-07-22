/**
 * Notifications API client.
 * See .ai/architecture.md: src/api/ — one file per resource, JWT injection via client.
 * See docs/14_REST_API.md §9 for endpoint specification.
 */
import client from './client';

export const notificationsAPI = {
  /**
   * GET /api/notifications/
   * Returns the authenticated user's notifications, ordered by created_at DESC.
   */
  list: () => client.get('/api/notifications/'),

  /**
   * PATCH /api/notifications/{id}/read/
   * Mark a single notification as read. Returns the updated notification.
   */
  markAsRead: (id) => client.patch(`/api/notifications/${id}/read/`),

  /**
   * PATCH /api/notifications/read-all/
   * Mark all unread notifications as read. Returns { marked_read: N }.
   */
  markAllAsRead: () => client.patch('/api/notifications/read-all/'),
};
