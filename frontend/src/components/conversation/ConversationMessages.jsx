import { useRef, useEffect, useState } from 'react';
import { Lightbulb, CheckCircle } from 'lucide-react';

export default function ConversationMessages({
  messages = [],
  streamingMessage,
  assistantThought,
  error,
  messagesEndRef,
  isLoading,
  onAction,
}) {
  const containerRef = useRef(null);
  const [expandedCards, setExpandedCards] = useState({});
  const toggleCard = (id) => setExpandedCards(prev => ({ ...prev, [id]: !prev[id] }));

  // ---- AUTO SCROLL ----
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage, assistantThought]);


  // ---- MERGE STATIC + STREAMING + THOUGHTS ----
  const allMessages = [...messages];

  if (streamingMessage) {
    allMessages.push({
      id: 'streaming',
      from: 'assistant',
      content: streamingMessage,
      type: 'assistant',
      status: 'streaming',
      timestamp: new Date().toISOString(),
    });
  }

  if (assistantThought) {
    allMessages.push({
      id: 'thought',
      from: 'assistant',
      content: assistantThought,
      type: 'assistant_thought',
      status: 'complete',
      timestamp: new Date().toISOString(),
    });
  }


  // ---- MESSAGE RENDER ----
  return (
    <div className="flex-1 overflow-y-auto pr-2 space-y-4 mt-5">

      {/* EMPTY STATE */}
      {allMessages.length === 0 && !isLoading && !error && (
        <p className="text-gray-400 text-center mt-4">Start the conversation below.</p>
      )}

      {allMessages.map((msg) => {
        const isUser = msg.from === 'user';
        const isAssistant = msg.from === 'assistant';
        const isSupplier = msg.from === 'supplier';
        const isThought = msg.type === 'assistant_thought';

        // ---- AVATAR ----
        const avatar = (
          <div className="relative flex shrink-0 overflow-hidden rounded-full w-8 h-8 bg-gray-100 border p-1 flex items-center justify-center">
            {isUser ? (
              // USER AVATAR
              <svg width="20" height="20" viewBox="0 0 16 16" fill="black">
                <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6Zm2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0Zm4 8c0 1-1 1-1 1H3s-1 0-1-1 1-4 6-4 6 3 6 4Zm-1-.004c-.001-.246-.154-.986-.832-1.664C11.516 10.68 10.289 10 8 10c-2.29 0-3.516.68-4.168 1.332-.678.678-.83 1.418-.832 1.664h10Z" />
              </svg>
            ) : (
              // AI / SUPPLIER AVATAR
              <svg width="20" height="20" viewBox="0 0 24 24" fill="black">
                <path d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
              </svg>
            )}
          </div>
        );

        // ---- BUBBLE STYLE ----
        const bubbleStyle = `
          p-4 rounded-xl max-w-[75%] whitespace-pre-wrap
          ${isUser ? 'bg-blue-50 ml-auto' : 'bg-gray-100'}
        `;

        return (
          <div
            key={msg.id}
            className={`flex gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'
              } text-gray-700 text-sm`}
          >
            {avatar}

            <div className={bubbleStyle}>

              {/* ASSISTANT THOUGHT */}
              {isThought && (
                <div className="flex items-start gap-2">
                  <Lightbulb className="w-4 h-4 mt-1 text-yellow-700" />
                  {msg.content}
                </div>
              )}

              {/* QUOTE CARD */}
              {!isThought && (msg.suppliers || msg.quote_id) && (
                <div className="space-y-1">
                  <div className="font-semibold flex items-center gap-1">
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    AI Suggested Quote
                  </div>

                  {expandedCards[msg.id] && msg.suppliers && (
                    <div className="space-y-1">
                      {msg.suppliers.map((s, idx) => (
                        <div
                          key={idx}
                          className="p-2 bg-gray-50 border rounded flex justify-between items-center text-sm"
                        >
                          <div>
                            <p className="font-medium">{s.name}</p>
                            <p>Price: ${s.price_per_unit} / {s.unit}</p>
                          </div>

                          <button
                            className="text-xs text-primary-600 hover:underline"
                            onClick={() => onAction?.('send_to_supplier', msg.id, s)}
                          >
                            Send
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  {msg.quote_id && (
                    <div className="p-2 bg-gray-50 border rounded text-sm">
                      Quote ID: <span className="font-medium">{msg.quote_id}</span>
                    </div>
                  )}

                  <div className="flex gap-2 mt-2">
                    <button
                      className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm hover:bg-green-200"
                      onClick={() => onAction?.('approve', msg.id)}
                    >
                      Approve
                    </button>

                    <button
                      className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-sm hover:bg-yellow-200"
                      onClick={() => onAction?.('clarify', msg.id)}
                    >
                      Ask Clarification
                    </button>
                  </div>
                </div>
              )}

              {/* NORMAL MESSAGE */}
              {!isThought && !msg.quote_id && !msg.suppliers && msg.content}
            </div>
          </div>
        );
      })}

      <div ref={messagesEndRef} />
    </div>
  );
}
