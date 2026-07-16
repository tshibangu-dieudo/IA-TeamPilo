/**
 * Projects API endpoints.
 * See .ai/architecture.md: src/api/ - one file per resource.
 */
import client from './client';

export const projectsAPI = {
  list: () => client.get('/api/projects/'),
  get: (id) => client.get(`/api/projects/${id}/`),
  create: (data) => client.post('/api/projects/', data),
  update: (id, data) => client.put(`/api/projects/${id}/`, data),
  delete: (id) => client.delete(`/api/projects/${id}/`),
};
