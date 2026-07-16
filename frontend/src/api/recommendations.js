/**
 * Recommendations API endpoints.
 * See .ai/architecture.md: src/api/ - one file per resource.
 */
import client from './client';

export const recommendationsAPI = {
  list: () => client.get('/api/recommendations/'),
  get: (id) => client.get(`/api/recommendations/${id}/`),
  accept: (id) => client.post(`/api/recommendations/${id}/accept/`),
  reject: (id) => client.post(`/api/recommendations/${id}/reject/`),
};
