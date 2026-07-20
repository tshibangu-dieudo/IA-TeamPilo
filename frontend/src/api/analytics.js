/**
 * Analytics API endpoints.
 * See .ai/architecture.md: src/api/ - one file per resource.
 */
import client from './client';

export const analyticsAPI = {
  // Workload endpoints
  getWorkload: (userId) => client.get(`/api/analytics/workload/${userId}/`),
  getWorkloadHistory: (userId) => client.get(`/api/analytics/workload/${userId}/history/`),
  getTeamWorkload: (teamId) => client.get(`/api/analytics/workload/team/${teamId}/`),
  
  // Risk score endpoints
  getRiskScore: (projectId) => client.get(`/api/analytics/risk/${projectId}/`),
  getRiskHistory: (projectId) => client.get(`/api/analytics/risk/${projectId}/history/`),
  getPortfolioRisk: () => client.get('/api/analytics/risk/portfolio/'),
};
