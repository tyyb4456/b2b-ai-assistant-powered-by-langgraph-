import { useState } from 'react';
import { User, Bot, Building2, Copy, Check, ThumbsUp, ThumbsDown, RefreshCcw, Lightbulb, CheckCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatRelativeTime } from '../../utils/dateFormatters';

export default function ConversationMessage({ message, isStreaming = false, onAction }) {
  const [copied, setCopied] = useState(false);
  const [liked, setLiked] = useState(false);
  const [disliked, setDisliked] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const { from, content, timestamp, status, type, suppliers, quote_id } = message;

  const isUser = from === 'user';
  const isAssistant = from === 'assistant';
  const isSupplier = from === 'supplier';

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleRetry = () => {
    console.log('Retry message:', message.id);
    onAction?.('retry', message.id);
  };

  const toggleExpand = () => setExpanded(!expanded);

  const bubbleBase = 'relative max-w-[95%] rounded-2xl px-4 py-3 whitespace-pre-wrap break-words';
  const bubbleStyles = isUser
    ? `${bubbleBase} bg-primary-600 text-black rounded-tr-sm`
    : isSupplier
      ? `${bubbleBase} bg-warning-50 text-neutral-900 border border-warning-200 rounded-tl-sm`
      : type === 'assistant_thought'
        ? `${bubbleBase} bg-yellow-100 text-yellow-900 border border-yellow-300 rounded-tl-sm flex items-start gap-2`
        : `${bubbleBase} bg-neutral-100 text-neutral-900 rounded-tl-sm`;

  return (
    <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : 'flex-row'} w-full`} role="article" aria-label={`Message from ${from}`}>
      {/* Avatar */}
      <div className="shrink-0">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isUser ? 'bg-primary-100' :
            isSupplier ? 'bg-warning-100' :
              type === 'assistant_thought' ? 'bg-yellow-200' : 'bg-secondary-100'
          }`}>
          {isUser && <User className="w-5 h-5 text-primary-600" />}
          {isAssistant && type !== 'assistant_thought' && <Bot className="w-5 h-5 text-secondary-600" />}
          {isAssistant && type === 'assistant_thought' && <Lightbulb className="w-5 h-5 text-yellow-700" />}
          {isSupplier && <Building2 className="w-5 h-5 text-warning-600" />}
        </div>
      </div>

      {/* Message Content */}
      <div className={`flex-1 min-w-0 ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        {/* Header */}
        <div className={`flex items-center gap-2 mb-1 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
          <span className="text-sm font-semibold text-black">
            {isUser ? 'You' : isSupplier ? 'Supplier' : type === 'assistant_thought' ? 'AI Assistant Thought' : 'AI Assistant'}
          </span>
        </div>

        {/* Bubble */}
        <div className={`${bubbleStyles} max-h-[500px] overflow-auto`}>
          {/* Assistant Thought */}
          {type === 'assistant_thought' ? (
            <div className="flex items-start gap-2">
              <Lightbulb className="w-4 h-4 mt-1 text-yellow-700 shrink-0" />
              <div className="text-sm whitespace-pre-wrap">{content}</div>
            </div>
          ) : /* Structured AI message with quote/suppliers */
            isAssistant && (suppliers || quote_id) ? (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <div className="font-semibold text-black flex items-center gap-1">
                    <CheckCircle className="w-4 h-4 text-green-600" /> AI Suggested Quote
                  </div>
                  {suppliers && (
                    <button onClick={toggleExpand} className="text-xs text-primary-600 hover:underline">
                      {expanded ? 'Collapse' : 'Expand'}
                    </button>
                  )}
                </div>

                {expanded && suppliers && (
                  <div className="space-y-1">
                    {suppliers.map((s, idx) => (
                      <div key={idx} className="p-2 bg-gray-50 border rounded flex justify-between items-center text-sm">
                        <div>
                          <p className="font-medium">{s.name}</p>
                          <p>Price: ${s.price_per_unit} / {s.unit}</p>
                        </div>
                        <button className="text-xs text-primary-600 hover:underline" onClick={() => onAction?.('send_to_supplier', message.id, s)}>
                          Send
                        </button>
                      </div>
                    ))}
                  </div>
                )}

                {quote_id && (
                  <div className="p-2 bg-gray-50 border rounded text-sm">
                    Quote ID: <span className="font-medium">{quote_id}</span>
                  </div>
                )}

                <div className="flex gap-2 mt-2">
                  <button className="px-2 py-1 bg-green-100 text-green-800 rounded text-sm hover:bg-green-200" onClick={() => onAction?.('approve', message.id)}>Approve</button>
                  <button className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-sm hover:bg-yellow-200" onClick={() => onAction?.('clarify', message.id)}>Ask Clarification</button>
                </div>
              </div>
            ) : /* User or normal AI message */ (
              <div className="prose prose-sm max-w-none prose-neutral dark:prose-invert prose-headings:font-semibold prose-a:text-primary-600 prose-code:text-sm prose-pre:bg-neutral-800 prose-pre:text-neutral-100 break-words">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
              </div>
            )}
        </div>

        {/* Timestamp */}
        {timestamp && <span className="text-xs text-neutral-500 mt-1" title={new Date(timestamp).toLocaleString()}>{formatRelativeTime(timestamp)}</span>}

        {/* Action Buttons */}
        {isAssistant && !isStreaming && type !== 'assistant_thought' && (
          <div className="flex items-center gap-1 mt-2">
            <button onClick={handleCopy} className="p-1.5 rounded-lg hover:bg-neutral-100 text-neutral-600 hover:text-neutral-900 transition-colors" title="Copy to clipboard">
              {copied ? <Check className="w-4 h-4 text-success-600" /> : <Copy className="w-4 h-4" />}
            </button>
            <button onClick={() => setLiked(!liked)} className={`p-1.5 rounded-lg hover:bg-neutral-100 transition-colors ${liked ? 'text-primary-600' : 'text-neutral-600 hover:text-neutral-900'}`} title="Like this response">
              <ThumbsUp className={`w-4 h-4 ${liked ? 'fill-current' : ''}`} />
            </button>
            <button onClick={() => setDisliked(!disliked)} className={`p-1.5 rounded-lg hover:bg-neutral-100 transition-colors ${disliked ? 'text-error-600' : 'text-neutral-600 hover:text-neutral-900'}`} title="Dislike this response">
              <ThumbsDown className={`w-4 h-4 ${disliked ? 'fill-current' : ''}`} />
            </button>
            {status === 'failed' && (
              <button onClick={handleRetry} className="p-1.5 rounded-lg hover:bg-neutral-100 text-neutral-600 hover:text-neutral-900 transition-colors" title="Retry">
                <RefreshCcw className="w-4 h-4" />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
