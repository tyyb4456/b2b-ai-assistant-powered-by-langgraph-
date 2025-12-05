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

export const selectSupplier = (threadId, supplierData) => {
  return apiClient.post(`/conversations/${threadId}/select-supplier`, supplierData);
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

// ============================================
// SUPPLIER RESPONSE WORKFLOW CONTROL
// ============================================

/**
 * Check if supplier response is available for a request
 */
export const checkSupplierResponse = (threadId, requestId) => {
  return apiClient.get(`/supplier/requests/${requestId}`);
};

/**
 * Manually resume workflow after supplier response
 */
export const resumeWorkflowFromSupplierResponse = (requestId) => {
  return apiClient.post(`/supplier/requests/${requestId}/resume-workflow`);
};

export const listConversations = (params = {}) => {
  return apiClient.get('/conversations', {
    params: {
      limit: params.limit || 20,
    },
  });
};

// ============================================
// STREAMING API - HEAVY DEBUG VERSION
// ============================================

/**
 * 🔥 NUCLEAR DEBUG VERSION
 */
function createXHRStream(url, method, body, onEvent, onComplete, onError) {
  console.log('═══════════════════════════════════════════════════════');
  console.log('[XHR-SSE] 🚀🚀🚀 STARTING NEW STREAM');
  console.log('[XHR-SSE] 📍 URL:', url);
  console.log('[XHR-SSE] 📦 Method:', method);
  console.log('[XHR-SSE] 📝 Body:', JSON.stringify(body, null, 2));
  console.log('═══════════════════════════════════════════════════════');
  
  const xhr = new XMLHttpRequest();
  xhr.open(method, url, true);
  xhr.setRequestHeader('Content-Type', 'application/json');
  
  let lastIndex = 0;
  let capturedThreadId = null;
  let eventCount = 0;
  
  xhr.onprogress = () => {
    // Get new data since last progress event
    const newData = xhr.responseText.substring(lastIndex);
    lastIndex = xhr.responseText.length;
    
    if (newData) {
      console.log('─────────────────────────────────────────────────────');
      console.log(`[XHR-SSE] 📥 PROGRESS #${++eventCount}`);
      console.log(`[XHR-SSE] 📏 New bytes: ${newData.length}`);
      console.log(`[XHR-SSE] 📄 Total bytes so far: ${lastIndex}`);
      console.log('[XHR-SSE] 🔍 Raw chunk:');
      console.log(newData.substring(0, 500)); // Show first 500 chars
      console.log('─────────────────────────────────────────────────────');
      
      // Split on newlines
      const lines = newData.split('\n');
      console.log(`[XHR-SSE] 📋 Split into ${lines.length} lines`);
      
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const trimmedLine = line.trim();
        
        console.log(`[XHR-SSE] Line ${i}:`, trimmedLine === '' ? '(empty)' : trimmedLine.substring(0, 100));
        
        if (trimmedLine === '') continue;
        
        // Skip ping lines
        if (trimmedLine.startsWith(': ping')) {
          console.log('[XHR-SSE] ⏭️  Skipping ping');
          continue;
        }
        
        // Backend format: "data: {...json...}"
        if (trimmedLine.startsWith('data: ')) {
          const dataStr = trimmedLine.slice(6); // Remove "data: "
          console.log('[XHR-SSE] 🎯 Found data line!');
          console.log('[XHR-SSE] 📝 Data string:', dataStr);
          
          try {
            const parsedData = JSON.parse(dataStr);
            console.log('[XHR-SSE] ✅ Parsed successfully!');
            console.log('[XHR-SSE] 📦 Parsed data:', JSON.stringify(parsedData, null, 2));
            
            // Extract type
            const eventType = parsedData.type;
            console.log('[XHR-SSE] 🏷️  Event type:', eventType);
            
            // CAPTURE thread_id
            if (parsedData.thread_id) {
              if (!capturedThreadId) {
                capturedThreadId = parsedData.thread_id;
                console.log('[XHR-SSE] 🎯🎯🎯 CAPTURED thread_id:', capturedThreadId);
              }
            }
            
            // Create event object
            const event = { 
              type: eventType,
              data: parsedData
            };
            
            console.log('[XHR-SSE] 🚀 CALLING onEvent with:', JSON.stringify(event, null, 2));
            
            // Call the callback
            onEvent(event);
            
            console.log('[XHR-SSE] ✅ onEvent callback completed');
            
          } catch (e) {
            console.error('[XHR-SSE] ❌❌❌ PARSE ERROR!');
            console.error('[XHR-SSE] Error:', e);
            console.error('[XHR-SSE] Raw data string:', dataStr);
            console.error('[XHR-SSE] Stack:', e.stack);
          }
        }
      }
    }
  };
  
  xhr.onload = () => {
    console.log('═══════════════════════════════════════════════════════');
    console.log('[XHR-SSE] 🏁 STREAM COMPLETED (onload)');
    console.log('[XHR-SSE] 📊 Total events:', eventCount);
    console.log('[XHR-SSE] 🎯 Captured thread_id:', capturedThreadId || '(none)');
    console.log('[XHR-SSE] 📡 Status:', xhr.status);
    console.log('[XHR-SSE] 📏 Total response length:', xhr.responseText.length);
    console.log('═══════════════════════════════════════════════════════');
    
    onComplete({ 
      status: 'completed',
      thread_id: capturedThreadId
    });
  };
  
  xhr.onerror = () => {
    console.error('═══════════════════════════════════════════════════════');
    console.error('[XHR-SSE] ❌❌❌ NETWORK ERROR');
    console.error('[XHR-SSE] Status:', xhr.status);
    console.error('[XHR-SSE] Ready state:', xhr.readyState);
    console.error('═══════════════════════════════════════════════════════');
    onError({ message: 'Network error' });
  };
  
  xhr.onabort = () => {
    console.log('═══════════════════════════════════════════════════════');
    console.log('[XHR-SSE] 🛑 STREAM ABORTED');
    console.log('═══════════════════════════════════════════════════════');
  };
  
  // Send request
  console.log('[XHR-SSE] 📤 Sending request...');
  xhr.send(body ? JSON.stringify(body) : null);
  console.log('[XHR-SSE] ✅ Request sent!');
  
  // Return cleanup
  return () => {
    console.log('[XHR-SSE] 🧹 Cleanup called - aborting XHR');
    xhr.abort();
  };
}

/**
 * Start conversation with streaming
 */
export const startConversationStream = (data, onEvent, onComplete, onError) => {
  const url = `${apiClient.defaults.baseURL}/conversations/stream`;
  console.log('[API] 🎬 startConversationStream called');
  
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
  console.log('[API] 🎬 continueConversationStream called');
  console.log('[API] 🆔 Thread ID:', threadId);
  console.log('[API] 💬 User input:', userInput);
  
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
  console.log('[API] 🎬 resumeConversationStream called');
  console.log('[API] 🆔 Thread ID:', threadId);
  console.log('[API] 💬 Supplier response:', supplierResponse.substring(0, 100));
  
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