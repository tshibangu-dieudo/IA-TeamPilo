/**
 * Recommendations API endpoints.
 * See .ai/architecture.md: src/api/ - one file per resource.
 */
import client from './client';

export const recommendationsAPI = {
  // GET /api/recommendations/
  list: (status = 'pending') => client.get(`/api/recommendations/?status=${status}`),
  
  // GET /api/recommendations/project/{project_id}/
  listByProject: (projectId, status = '') => client.get(`/api/recommendations/project/${projectId}/${status ? `?status=${status}` : ''}`),
  
  // GET /api/recommendations/{id}/
  get: (id) => client.get(`/api/recommendations/${id}/`),
  
  // POST /api/recommendations/generate/
  generate: (projectId) => client.post('/api/recommendations/generate/', { project_id: projectId }),
  
  // PATCH /api/recommendations/{id}/accept/
  accept: (id) => client.patch(`/api/recommendations/${id}/accept/`),
  
  // PATCH /api/recommendations/{id}/dismiss/
  dismiss: (id) => client.patch(`/api/recommendations/${id}/dismiss/`),
};
