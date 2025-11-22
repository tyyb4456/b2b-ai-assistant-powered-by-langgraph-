import apiClient from './client';

// ============================================
// CONVERSATIONS API (non-streaming)
// ============================================

export const startConversation = (data) => {
  return apiClient.post('/conversations', {
    user_input: data.userInput,
    recipient_email: data.recipientEmail || null,
    channel: data.channel || 'web',
  });
};

export const getConversation = (threadId) => {
  return apiClient.get(`/conversations/${threadId}`);
};

export const getConversationComprehensive = (threadId) => {
  return apiClient.get(`/conversations/${threadId}/comprehensive`);
};

export const getQuoteWorkflow = (threadId) => {
  return apiClient.get(`/conversations/${threadId}/quote`);
};

export const getNegotiationWorkflow = (threadId) => {
  return apiClient.get(`/conversations/${threadId}/negotiation`);
};

export const getConversationStatus = (threadId) => {
  return apiClient.get(`/conversations/${threadId}/status`);
};

export const getExtractedParameters = (threadId) => {
  return apiClient.get(`/conversations/${threadId}/extracted-parameters`);
};

export const getSuppliers = (threadId) => {
  return apiClient.get(`/conversations/${threadId}/suppliers`);
};

export const getConversationMessages = (threadId) => {
  return apiClient.get(`/conversations/${threadId}/messages`);
};

export const continueConversation = (threadId, userInput) => {
  return apiClient.post(`/conversations/${threadId}/continue`, {
    user_input: userInput,
  });
};

export const resumeConversation = (threadId, supplierResponse) => {
  return apiClient.post(`/conversations/${threadId}/resume`, {
    supplier_response: supplierResponse,
  });
};

export const listConversations = (params = {}) => {
  return apiClient.get('/conversations', {
    params: {
      limit: params.limit || 20,
    },
  });
};

// ============================================
// STREAMING API - USING XMLHttpRequest
// ============================================

/**
 * 🔥 NUCLEAR OPTION: Use XMLHttpRequest for streaming
 * This is old-school but it ALWAYS works for streaming
 */
/**
 * 🔥 SIMPLIFIED: Match old working Chat.jsx parsing
 */
function createXHRStream(url, method, body, onEvent, onComplete, onError) {
  console.log('[XHR-SSE] 🚀 Starting stream');
  console.log('[XHR-SSE] URL:', url);
  
  const xhr = new XMLHttpRequest();
  xhr.open(method, url, true);
  xhr.setRequestHeader('Content-Type', 'application/json');
  
  let lastIndex = 0;
  let capturedThreadId = null;
  
  xhr.onprogress = () => {
    // Get new data since last progress event
    const newData = xhr.responseText.substring(lastIndex);
    lastIndex = xhr.responseText.length;
    
    if (newData) {
      console.log('[XHR-SSE] 📥 Progress! New bytes:', newData.length);
      
      // Split on newlines
      const lines = newData.split('\n');
      
      for (const line of lines) {
        const trimmedLine = line.trim();
        if (trimmedLine === '') continue;
        
        // 🔥 SIMPLIFIED: Parse like old Chat.jsx
        if (trimmedLine.startsWith('data: ')) {
          const dataStr = trimmedLine.slice(6); // Remove "data: "
          
          try {
            const data = JSON.parse(dataStr);
            console.log('[XHR-SSE] ✅ Parsed:', data);
            
            // CAPTURE thread_id from events
            if (data.thread_id && !capturedThreadId) {
              capturedThreadId = data.thread_id;
              console.log('[XHR-SSE] 🎯 Captured thread_id:', capturedThreadId);
            }
            
            // Extract event type from data (it's inside the JSON now)
            const eventType = data.type || 'message';
            
            // Call callback
            onEvent({ type: eventType, data });
            
          } catch (e) {
            console.error('[XHR-SSE] Parse error:', e);
            console.error('[XHR-SSE] Raw:', dataStr);
          }
        }
        else if (trimmedLine.startsWith('event: done')) {
          console.log('[XHR-SSE] 🏁 Done event');
          // Wait for the data line that follows
        }
      }
    }
  };
  
  xhr.onload = () => {
    console.log('[XHR-SSE] 🏁 Complete!');
    onComplete({ 
      status: 'completed',
      thread_id: capturedThreadId
    });
  };
  
  xhr.onerror = () => {
    console.error('[XHR-SSE] ❌ Error');
    onError({ message: 'Network error' });
  };
  
  xhr.onabort = () => {
    console.log('[XHR-SSE] 🛑 Aborted');
  };
  
  // Send request
  xhr.send(body ? JSON.stringify(body) : null);
  
  // Return cleanup
  return () => {
    console.log('[XHR-SSE] 🛑 Aborting');
    xhr.abort();
  };
}

/**
 * Start conversation with streaming
 */
export const startConversationStream = (data, onEvent, onComplete, onError) => {
  const url = `${apiClient.defaults.baseURL}/conversations/stream`;
  
  return createXHRStream(
    url,
    'POST',
    {
      user_input: data.userInput,
      recipient_email: data.recipientEmail || null,
      channel: data.channel || 'web',
    },
    onEvent,
    onComplete,
    onError
  );
};

/**
 * Continue conversation with streaming
 */
export const continueConversationStream = (threadId, userInput, onEvent, onComplete, onError) => {
  const url = `${apiClient.defaults.baseURL}/conversations/${threadId}/stream/continue`;
  
  return createXHRStream(
    url,
    'POST',
    { user_input: userInput },
    onEvent,
    onComplete,
    onError
  );
};

/**
 * Resume conversation with streaming
 */
export const resumeConversationStream = (threadId, supplierResponse, onEvent, onComplete, onError) => {
  const url = `${apiClient.defaults.baseURL}/conversations/${threadId}/stream/resume`;
  
  return createXHRStream(
    url,
    'POST',
    { supplier_response: supplierResponse },
    onEvent,
    onComplete,
    onError
  );
};

// ============================================
// HEALTH CHECK
// ============================================

export const healthCheck = () => {
  return apiClient.get('/health');
};