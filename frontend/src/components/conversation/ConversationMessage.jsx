import { useState } from 'react';
import { User, Bot, Building2, Copy, Check, ThumbsUp, ThumbsDown, RefreshCcw, Lightbulb } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { formatRelativeTime } from '../../utils/dateFormatters';

export default function ConversationMessage({ message, isStreaming = false }) {
  const [copied, setCopied] = useState(false);
  const [liked, setLiked] = useState(false);
  const [disliked, setDisliked] = useState(false);

  const { from, content, timestamp, status, type } = message;

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
  };

  // Bubble styles
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
        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${isUser ? 'bg-primary-100'
            : isSupplier ? 'bg-warning-100'
              : type === 'assistant_thought' ? 'bg-yellow-200'
                : 'bg-secondary-100'
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
          {timestamp && <span className="text-xs text-black">{formatDistanceToNow(new Date(timestamp), { addSuffix: true })}</span>}
          {isStreaming && <span className="flex items-center gap-1 text-xs text-black">● typing...</span>}
        </div>

        {/* Bubble */}
        <div className={`${bubbleStyles} max-h-[500px] overflow-auto`}>
          {type === 'assistant_thought' ? (
            <div className="flex items-start gap-2">
              <Lightbulb className="w-4 h-4 mt-1 text-yellow-700 shrink-0" />
              <div className="text-sm whitespace-pre-wrap">{content}</div>
            </div>
          ) : isUser ? (
            <p className="text-sm leading-relaxed">{content}</p>
          ) : (
            <div className="prose prose-sm max-w-none prose-neutral dark:prose-invert prose-headings:font-semibold prose-a:text-primary-600 prose-code:text-sm prose-pre:bg-neutral-800 prose-pre:text-neutral-100 break-words">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Timestamp */}
        {timestamp && <span className="text-xs text-neutral-500" title={new Date(timestamp).toLocaleString()}>{formatRelativeTime(timestamp)}</span>}

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
