/**
 * Teams API endpoints.
 * See .ai/architecture.md: src/api/ - one file per resource.
 */
import client from './client';

export const teamsAPI = {
  list: () => client.get('/api/teams/'),
  get: (id) => client.get(`/api/teams/${id}/`),
  create: (data) => client.post('/api/teams/', data),
  update: (id, data) => client.put(`/api/teams/${id}/`, data),
  delete: (id) => client.delete(`/api/teams/${id}/`),
};
