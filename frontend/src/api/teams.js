/**
 * Teams API endpoints.
 * See .ai/architecture.md: src/api/ - one file per resource.
 */
import client from './client';

export const teamsAPI = {
  // Teams
  list: () => client.get('/api/teams/teams/'),
  get: (id) => client.get(`/api/teams/teams/${id}/`),
  create: (data) => client.post('/api/teams/teams/', data),
  update: (id, data) => client.put(`/api/teams/teams/${id}/`, data),
  delete: (id) => client.delete(`/api/teams/teams/${id}/`),
  getMyTeams: () => client.get('/api/teams/my-teams/'),
  
  // Skills
  getSkills: () => client.get('/api/teams/skills/'),
  getSkill: (id) => client.get(`/api/teams/skills/${id}/`),
  createSkill: (data) => client.post('/api/teams/skills/', data),
  updateSkill: (id, data) => client.put(`/api/teams/skills/${id}/`, data),
  deleteSkill: (id) => client.delete(`/api/teams/skills/${id}/`),
  
  // Team Memberships
  getMemberships: () => client.get('/api/teams/memberships/'),
  getMembership: (id) => client.get(`/api/teams/memberships/${id}/`),
  createMembership: (data) => client.post('/api/teams/memberships/', data),
  updateMembership: (id, data) => client.put(`/api/teams/memberships/${id}/`, data),
  deleteMembership: (id) => client.delete(`/api/teams/memberships/${id}/`),
};
