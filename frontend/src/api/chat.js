/**
 * Chat API endpoints.
 * See .ai/architecture.md: src/api/ - one file per resource.
 */
import client from './client';

export const chatAPI = {
  sendMessage: (data) => client.post('/api/chat/messages/', data),
  getMessages: (projectId) => client.get(`/api/chat/messages/?project=${projectId}`),
};
