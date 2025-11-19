import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import * as api from './endpoints';
import toast from 'react-hot-toast';

// ============================================
// QUERY KEYS
// ============================================

export const queryKeys = {
  conversations: ['conversations'],
  conversation: (threadId) => ['conversation', threadId],
  conversationComprehensive: (threadId) => ['conversation-comprehensive', threadId],
  conversationQuote: (threadId) => ['conversation-quote', threadId],
  conversationNegotiation: (threadId) => ['conversation-negotiation', threadId],
  conversationStatus: (threadId) => ['conversation-status', threadId],
  conversationParameters: (threadId) => ['conversation-parameters', threadId],
  conversationSuppliers: (threadId) => ['conversation-suppliers', threadId],
  conversationMessages: (threadId) => ['conversation-messages', threadId],
  health: ['health'],
};

// ============================================
// QUERIES
// ============================================

/**
 * Hook to fetch all conversations
 */
export function useConversations(params = {}) {
  return useQuery({
    queryKey: [...queryKeys.conversations, params],
    queryFn: () => api.listConversations(params),
    select: (response) => response.data,
  });
}

/**
 * Hook to fetch a single conversation (basic)
 */
export function useConversation(threadId, options = {}) {
  return useQuery({
    queryKey: queryKeys.conversation(threadId),
    queryFn: () => api.getConversation(threadId),
    select: (response) => response.data,
    enabled: !!threadId && (options.enabled !== false),
    ...options,
  });
}

/**
 * Hook to fetch COMPREHENSIVE conversation data (all state fields)
 */
export function useConversationComprehensive(threadId, options = {}) {
  return useQuery({
    queryKey: queryKeys.conversationComprehensive(threadId),
    queryFn: () => api.getConversationComprehensive(threadId),
    select: (response) => response.data,
    enabled: !!threadId && (options.enabled !== false),
    ...options,
  });
}

/**
 * Hook to fetch quote workflow data
 */
export function useQuoteWorkflow(threadId, options = {}) {
  return useQuery({
    queryKey: queryKeys.conversationQuote(threadId),
    queryFn: () => api.getQuoteWorkflow(threadId),
    select: (response) => response.data,
    enabled: !!threadId && (options.enabled !== false),
    ...options,
  });
}

/**
 * Hook to fetch negotiation workflow data
 */
export function useNegotiationWorkflow(threadId, options = {}) {
  return useQuery({
    queryKey: queryKeys.conversationNegotiation(threadId),
    queryFn: () => api.getNegotiationWorkflow(threadId),
    select: (response) => response.data,
    enabled: !!threadId && (options.enabled !== false),
    ...options,
  });
}

/**
 * Hook to fetch conversation status
 */
export function useConversationStatus(threadId, options = {}) {
  return useQuery({
    queryKey: queryKeys.conversationStatus(threadId),
    queryFn: () => api.getConversationStatus(threadId),
    select: (response) => response.data,
    enabled: !!threadId && (options.enabled !== false),
    refetchInterval: options.refetchInterval,
    ...options,
  });
}

/**
 * Hook to fetch extracted parameters
 */
export function useExtractedParameters(threadId, options = {}) {
  return useQuery({
    queryKey: queryKeys.conversationParameters(threadId),
    queryFn: () => api.getExtractedParameters(threadId),
    select: (response) => response.data,
    enabled: !!threadId && (options.enabled !== false),
    ...options,
  });
}

/**
 * Hook to fetch suppliers
 */
export function useSuppliers(threadId, options = {}) {
  return useQuery({
    queryKey: queryKeys.conversationSuppliers(threadId),
    queryFn: () => api.getSuppliers(threadId),
    select: (response) => response.data,
    enabled: !!threadId && (options.enabled !== false),
    ...options,
  });
}

/**
 * Hook to fetch conversation messages
 */
export function useConversationMessages(threadId, options = {}) {
  return useQuery({
    queryKey: queryKeys.conversationMessages(threadId),
    queryFn: () => api.getConversationMessages(threadId),
    select: (response) => response.data,
    enabled: !!threadId && (options.enabled !== false),
    ...options,
  });
}

/**
 * Hook to check API health
 */
export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: api.healthCheck,
    select: (response) => response.data,
    staleTime: Infinity,
  });
}

// ============================================
// MUTATIONS
// ============================================

/**
 * Hook to start a new conversation
 */
export function useStartConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: api.startConversation,
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.conversations });
      toast.success('Conversation started successfully!');
      return response.data;
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to start conversation');
    },
  });
}

/**
 * Hook to continue a conversation
 */
export function useContinueConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ threadId, userInput }) => 
      api.continueConversation(threadId, userInput),
    onSuccess: (response, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.conversation(variables.threadId) 
      });
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.conversationComprehensive(variables.threadId) 
      });
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.conversationStatus(variables.threadId) 
      });
      
      toast.success('Conversation continued successfully!');
      return response.data;
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to continue conversation');
    },
  });
}

/**
 * Hook to resume a paused conversation
 */
export function useResumeConversation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ threadId, supplierResponse }) => 
      api.resumeConversation(threadId, supplierResponse),
    onSuccess: (response, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.conversation(variables.threadId) 
      });
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.conversationComprehensive(variables.threadId) 
      });
      queryClient.invalidateQueries({ 
        queryKey: queryKeys.conversationStatus(variables.threadId) 
      });
      
      toast.success('Conversation resumed successfully!');
      return response.data;
    },
    onError: (error) => {
      toast.error(error.message || 'Failed to resume conversation');
    },
  });
}