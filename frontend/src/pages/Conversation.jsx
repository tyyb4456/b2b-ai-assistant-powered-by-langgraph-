import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import * as api from '../api/endpoints';
import ConversationMessages from '../components/conversation/ConversationMessages';
import ConversationInput from '../components/conversation/ConversationInput';
import ConnectionStatus from '../components/conversation/ConnectionStatus';
import { Info, Copy } from 'lucide-react';
import toast from 'react-hot-toast';

export default function Conversation() {
  const { threadId } = useParams();
  const navigate = useNavigate();

  const [messages, setMessages] = useState([]);
  const [currentThreadId, setCurrentThreadId] = useState(threadId || null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isWaitingForSupplier, setIsWaitingForSupplier] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [assistantThought, setAssistantThought] = useState('');
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('connected');
  const [retryAttempt, setRetryAttempt] = useState(0);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const cleanupRef = useRef(null);
  const messagesEndRef = useRef(null);
  const lastUserInputRef = useRef('');

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage, assistantThought]);

  useEffect(() => {
    if (threadId) loadExistingConversation(threadId);
    return () => cleanupRef.current?.();
  }, [threadId]);

  const loadExistingConversation = async (tid) => {
    setIsLoadingHistory(true);
    try {
      const response = await api.getConversationMessages(tid);
      if (response.messages) {
        setMessages(
          response.messages.map((msg) => ({
            id: msg.id || Date.now(),
            from: msg.role === 'user' ? 'user' : 'assistant',
            content: msg.content,
            type: msg.type || 'assistant',
            timestamp: msg.timestamp || new Date().toISOString(),
            status: 'complete',
          }))
        );
      }
      setCurrentThreadId(tid);
    } catch (err) {
      console.error(err);
      setError('Failed to load conversation history');
      toast.error('Failed to load conversation');
    } finally {
      setIsLoadingHistory(false);
    }
  };

  const addUserMessage = (content) => {
    const userMessage = {
      id: Date.now(),
      from: 'user',
      content,
      type: 'user',
      timestamp: new Date().toISOString(),
      status: 'complete',
    };
    setMessages((prev) => [...prev, userMessage]);
  };

  const handleStartConversation = (userInput) => {
    lastUserInputRef.current = userInput;
    addUserMessage(userInput);
    setIsStreaming(true);
    setError(null);
    setConnectionStatus('connected');
    setStreamingMessage('');

    cleanupRef.current = api.startConversationStream(
      { userInput, channel: 'web' },
      handleStreamEvent,
      handleStreamComplete,
      handleStreamError
    );
  };

  const handleContinueConversation = (userInput) => {
    lastUserInputRef.current = userInput;
    addUserMessage(userInput);
    setIsStreaming(true);
    setError(null);
    setIsWaitingForSupplier(false);
    setConnectionStatus('connected');
    setStreamingMessage('');

    cleanupRef.current = api.continueConversationStream(
      currentThreadId,
      userInput,
      handleStreamEvent,
      handleStreamComplete,
      handleStreamError
    );
  };

  const handleResumeConversation = () => {
    setIsStreaming(true);
    setError(null);
    setIsWaitingForSupplier(false);
    setConnectionStatus('connected');
    setStreamingMessage('');

    const requestId = 'temp_request_id';
    cleanupRef.current = api.resumeConversationStream(
      currentThreadId,
      requestId,
      handleStreamEvent,
      handleStreamComplete,
      handleStreamError
    );
  };

  // Stream event handler
  const handleStreamEvent = (event) => {
    const { type, data = {} } = event;

    switch (type) {
      case 'reconnecting':
        setConnectionStatus('reconnecting');
        setRetryAttempt(data.attempt || 0);
        break;

      case 'connected':
        setConnectionStatus('connected');
        setRetryAttempt(0);
        if (data.thread_id && !currentThreadId) setCurrentThreadId(data.thread_id);
        break;

      case 'message':
      case 'ai_chunk':
      case 'node_progress':
        if (data.content && data.content.trim() !== lastUserInputRef.current) {
          const displayContent = data.type === 'assistant_thought'
            ? null
            : data.content;

          // Only update streamingMessage live
          if (displayContent) setStreamingMessage((prev) => (prev ? prev + data.content : data.content));

          // Update assistant thought separately
          if (data.type === 'assistant_thought') {
            setAssistantThought((prev) => (prev ? prev + '\n' + data.content : data.content));
          }
        }
        break;

      case 'ai_complete':
      case 'workflow_complete':
        appendAIMessage();
        setIsStreaming(false);
        setIsWaitingForSupplier(false);
        break;

      case 'supplier_wait':
      case 'paused':
        setIsWaitingForSupplier(true);
        break;

      case 'supplier_response':
        setIsWaitingForSupplier(false);
        if (data.content) {
          setMessages((prev) => [
            ...prev,
            {
              id: Date.now(),
              from: 'supplier',
              content: data.content,
              type: 'supplier',
              timestamp: new Date().toISOString(),
              status: 'complete',
            },
          ]);
        }
        break;

      case 'error':
        setError(data.error || 'An error occurred');
        setIsStreaming(false);
        setConnectionStatus('error');
        toast.error('Connection error: ' + (data.error || 'Unknown'));
        break;

      default:
        console.log('Unknown event type:', type);
    }
  };

  const appendAIMessage = () => {
    if (streamingMessage) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now(),
          from: 'assistant',
          content: streamingMessage,
          type: 'assistant',
          timestamp: new Date().toISOString(),
          status: 'complete',
        },
      ]);
      setStreamingMessage('');
    }

    if (assistantThought) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          from: 'assistant',
          content: assistantThought,
          type: 'assistant_thought',
          timestamp: new Date().toISOString(),
          status: 'complete',
        },
      ]);
      setAssistantThought('');
    }
  };

  const handleStreamComplete = () => {
    appendAIMessage();
    setIsStreaming(false);
    setConnectionStatus('connected');
  };

  const handleStreamError = (err) => {
    console.error(err);
    setError(err.message || 'Connection error');
    setIsStreaming(false);
    setConnectionStatus('error');
    toast.error('Connection error: ' + (err.message || 'Unknown'));
  };

  const handleSubmit = (userInput) => {
    if (!userInput.trim() || isStreaming) return;
    if (!currentThreadId) handleStartConversation(userInput);
    else handleContinueConversation(userInput);
  };

  const handleNewConversation = () => {
    cleanupRef.current?.();
    setMessages([]);
    setCurrentThreadId(null);
    setIsStreaming(false);
    setIsWaitingForSupplier(false);
    setStreamingMessage('');
    setAssistantThought('');
    setError(null);
    setConnectionStatus('connected');
    navigate('/conversation');
  };

  const handleCopyConversation = () => {
    const text = messages
      .map((msg) => {
        const sender =
          msg.from === 'user'
            ? 'You'
            : msg.from === 'assistant'
              ? 'AI Assistant'
              : 'Supplier';
        return `${sender}: ${msg.content}`;
      })
      .join('\n\n');
    navigator.clipboard.writeText(text);
    toast.success('Conversation copied!');
  };

  return (
    <div className="flex flex-col h-[calc(100vh-2rem)] bg-neutral-50">
      <ConnectionStatus status={connectionStatus} retryAttempt={retryAttempt} />

      <div className="px-6 py-3 border-b border-neutral-400 bg-white">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-black">
              {currentThreadId ? 'Conversation' : 'Start a conversation'}
            </h1>
            <p className="text-neutral-500 mt-1">
              Get supplier info, request a quote, and negotiate — all from this page.
            </p>
          </div>

          {currentThreadId && (
            <div className="flex items-center gap-2">
              {messages.length > 0 && (
                <button
                  onClick={handleCopyConversation}
                  className="px-3 py-2 text-sm font-medium text-black hover:text-neutral-900 hover:bg-neutral-100 rounded-lg flex items-center gap-2"
                  title="Copy conversation"
                >
                  <Copy size={16} />
                  Copy
                </button>
              )}
              <button
                onClick={() =>
                  navigate(`/conversation/${currentThreadId}/details`)
                }
                className="px-3 py-2 text-sm font-medium text-neutral-600 hover:text-neutral-900 hover:bg-neutral-100 rounded-lg flex items-center gap-2"
                title="View conversation details"
              >
                <Info size={16} />
                Details
              </button>
              <button
                onClick={handleNewConversation}
                className="px-4 py-2 text-sm font-medium text-primary-600 hover:text-primary-700 hover:bg-primary-50 rounded-lg"
              >
                New Conversation
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <ConversationMessages
          messages={messages}
          streamingMessage={streamingMessage}
          assistantThought={assistantThought}
          error={error}
          messagesEndRef={messagesEndRef}
          isLoading={isLoadingHistory}
        />
      </div>

      <div className="border-t border-neutral-200 bg-white">
        <div className="max-w-4xl mx-auto px-3 py-4">
          <ConversationInput
            onSubmit={handleSubmit}
            onResume={handleResumeConversation}
            disabled={isStreaming}
            isWaitingForSupplier={isWaitingForSupplier}
            placeholder={
              isWaitingForSupplier
                ? 'Waiting for supplier response...'
                : 'Type your message...'
            }
          />
        </div>
      </div>
    </div>
  );
}
