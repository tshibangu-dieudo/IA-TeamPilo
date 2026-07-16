/**
 * Authentication API endpoints.
 * See .ai/architecture.md: src/api/ - one file per resource.
 */
import client from './client';

export const authAPI = {
  login: (credentials) => client.post('/api/auth/login/', credentials),
  logout: () => client.post('/api/auth/logout/'),
  register: (userData) => client.post('/api/auth/register/', userData),
  refreshToken: (refreshToken) => client.post('/api/auth/token/refresh/', { refresh: refreshToken }),
  getCurrentUser: () => client.get('/api/auth/me/'),
};
