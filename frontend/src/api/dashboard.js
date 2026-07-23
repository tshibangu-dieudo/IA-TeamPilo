/**
 * Dashboard API client.
 * See docs/14_REST_API.md §11.
 */
import client from './client';

export const dashboardAPI = {
  /**
   * GET /api/dashboard/summary/
   * Role-aware aggregated dashboard payload.
   */
  getSummary: () => client.get('/api/dashboard/summary/'),
};
