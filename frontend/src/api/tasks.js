/**
 * Tasks API endpoints.
 * See .ai/architecture.md: src/api/ - one file per resource.
 */
import client from './client';

export const tasksAPI = {
  // Current user's tasks
  getMyTasks: () => client.get('/api/tasks/me/'),
  
  // Task detail, update, delete
  get: (id) => client.get(`/api/tasks/${id}/`),
  update: (id, data) => client.patch(`/api/tasks/${id}/`, data),
  delete: (id) => client.delete(`/api/tasks/${id}/`),
  
  // Status update
  updateStatus: (id, data) => client.patch(`/api/tasks/${id}/status/`, data),
  
  // Dependencies
  getDependencies: (id) => client.get(`/api/tasks/${id}/dependencies/`),
  addDependency: (id, data) => client.post(`/api/tasks/${id}/dependencies/`, data),
  removeDependency: (id, depId) => client.delete(`/api/tasks/${id}/dependencies/${depId}/`),
  
  // Status history
  getHistory: (id) => client.get(`/api/tasks/${id}/history/`),
  
  // Project-scoped tasks (for creating tasks in a project)
  getProjectTasks: (projectId) => client.get(`/api/projects/${projectId}/tasks/`),
  createProjectTask: (projectId, data) => client.post(`/api/projects/${projectId}/tasks/`, data),
};
