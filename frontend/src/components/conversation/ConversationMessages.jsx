import { useRef, useEffect } from 'react';
import { MessageSquareIcon, AlertCircle, Lightbulb } from 'lucide-react';
import ConversationMessage from './ConversationMessage';

export default function ConversationMessages({
  messages,
  streamingMessage,
  assistantThought,
  error,
  messagesEndRef,
  isLoading
}) {
  const containerRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage, assistantThought]);

  return (
    <div ref={containerRef} className="h-full overflow-y-auto scroll-smooth bg-neutral-50">
      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* EMPTY STATE */}
        {messages.length === 0 && !streamingMessage && !assistantThought && !error && !isLoading && (
          <div className="flex flex-col items-center justify-center min-h-[50vh] text-center">
            <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center mb-4">
              <MessageSquareIcon className="w-8 h-8 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold text-neutral-900 mb-2">
              Start a conversation
            </h3>
            <p className="text-neutral-600 max-w-md">
              Messages will appear here once you begin.
            </p>
          </div>
        )}

        {/* LOADING HISTORY */}
        {isLoading && (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
              <p className="text-neutral-600">Loading conversation...</p>
            </div>
          </div>
        )}

        {/* ERROR */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-red-900 mb-1">Error</p>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        )}

        {/* MESSAGES */}
        <div className="space-y-6">
          {messages.map((msg) => (
            <ConversationMessage
              key={msg.id}
              message={msg}
              isStreaming={msg.status === 'streaming'}
            />
          ))}

          {/* CURRENT STREAMING MESSAGE */}
          {streamingMessage && (
            <ConversationMessage
              message={{
                id: 'streaming',
                from: 'assistant',
                content: streamingMessage,
                type: 'assistant',
                status: 'streaming',
              }}
              isStreaming={true}
            />
          )}

          {/* CURRENT ASSISTANT THOUGHT */}
          {assistantThought && (
            <div className="bg-yellow-100 border border-yellow-300 text-yellow-900 p-4 rounded-xl flex items-start gap-3 shadow-sm">
              <Lightbulb className="w-5 h-5 mt-1 text-yellow-700" />
              <div className="whitespace-pre-wrap text-sm">{assistantThought}</div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>
    </div>
  );
}
