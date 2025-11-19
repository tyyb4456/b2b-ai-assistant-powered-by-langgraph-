// src/services/conversationService.js
// ============================================
// Conversation API calls
// ============================================
import api from './api';

export const conversationService = {
  /**
   * Start a new conversation
   * @param {Object} data - { user_input, recipient_email?, channel? }
   * @returns {Promise<Object>} - { thread_id, status, intent, ... }
   */
  start: async (data) => {
    return api.post('/conversations', {
      user_input: data.user_input,
      recipient_email: data.recipient_email || null,
      channel: data.channel || 'web',
    });
  },

  /**
   * Get conversation details
   * @param {string} threadId - Conversation thread ID
   * @returns {Promise<Object>} - Full conversation details
   */
  get: async (threadId) => {
    return api.get(`/conversations/${threadId}`);
  },

  /**
   * Get conversation status (lighter than full details)
   * @param {string} threadId - Conversation thread ID
   * @returns {Promise<Object>} - Status info
   */
  getStatus: async (threadId) => {
    return api.get(`/conversations/${threadId}/status`);
  },

  /**
   * List all conversations
   * @param {Object} params - { limit? }
   * @returns {Promise<Array>} - List of conversations
   */
  list: async (params = {}) => {
    return api.get('/conversations', { params });
  },

  /**
   * Continue a conversation with new input
   * @param {string} threadId - Conversation thread ID
   * @param {Object} data - { user_input }
   * @returns {Promise<Object>} - Updated conversation
   */
  continue: async (threadId, data) => {
    return api.post(`/conversations/${threadId}/continue`, {
      user_input: data.user_input,
    });
  },

  /**
   * Resume with supplier response
   * @param {string} threadId - Conversation thread ID
   * @param {Object} data - { supplier_response }
   * @returns {Promise<Object>} - Updated conversation
   */
  resume: async (threadId, data) => {
    return api.post(`/conversations/${threadId}/resume`, {
      supplier_response: data.supplier_response,
    });
  },
};
