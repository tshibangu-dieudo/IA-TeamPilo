/**
 * Projects API endpoints.
 * See .ai/architecture.md: src/api/ - one file per resource.
 */
import client from './client';

export const projectsAPI = {
  list: () => client.get('/api/projects/projects/'),
  get: (id) => client.get(`/api/projects/projects/${id}/`),
  create: (data) => client.post('/api/projects/projects/', data),
  update: (id, data) => client.put(`/api/projects/projects/${id}/`, data),
  delete: (id) => client.delete(`/api/projects/projects/${id}/`),
  getMyProjects: () => client.get('/api/projects/my-projects/'),
};
