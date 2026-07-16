/**
 * Analytics API endpoints.
 * See .ai/architecture.md: src/api/ - one file per resource.
 */
import client from './client';

export const analyticsAPI = {
  getWorkload: (userId) => client.get(`/api/analytics/workload/${userId}/`),
  getRiskScore: (projectId) => client.get(`/api/analytics/risk/${projectId}/`),
};
