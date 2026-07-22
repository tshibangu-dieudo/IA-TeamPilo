/**
 * Chat API client.
 * See .ai/architecture.md: src/api/ — one file per resource, JWT via client.
 * See docs/14_REST_API.md §10.
 */
import client from './client';

export const chatAPI = {
  /**
   * POST /api/chat/query/
   * { question, project_id?, conversation_id? }
   * Returns { answer, generated_by, conversation_id, conversation_title }
   */
  query: (data) => client.post('/api/chat/query/', data),

  /**
   * POST /api/chat/summary/{project_id}/
   * Returns { answer, generated_by, conversation_id }
   */
  summary: (projectId) => client.post(`/api/chat/summary/${projectId}/`),

  /**
   * GET /api/chat/conversations/
   * Returns paginated list of the user's conversations.
   */
  listConversations: () => client.get('/api/chat/conversations/'),

  /**
   * GET /api/chat/conversations/{id}/
   * Returns conversation detail with all messages.
   */
  getConversation: (id) => client.get(`/api/chat/conversations/${id}/`),

  /**
   * DELETE /api/chat/conversations/{id}/
   */
  deleteConversation: (id) => client.delete(`/api/chat/conversations/${id}/`),
};
