/**
 * Notifications API endpoints.
 * See .ai/architecture.md: src/api/ - one file per resource.
 */
import client from './client';

export const notificationsAPI = {
  list: () => client.get('/api/notifications/'),
  markAsRead: (id) => client.patch(`/api/notifications/${id}/`, { is_read: true }),
};
