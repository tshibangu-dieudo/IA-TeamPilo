/**
 * Tasks API endpoints.
 * See .ai/architecture.md: src/api/ - one file per resource.
 */
import client from './client';

export const tasksAPI = {
  list: () => client.get('/api/tasks/'),
  get: (id) => client.get(`/api/tasks/${id}/`),
  create: (data) => client.post('/api/tasks/', data),
  update: (id, data) => client.put(`/api/tasks/${id}/`, data),
  delete: (id) => client.delete(`/api/tasks/${id}/`),
};
