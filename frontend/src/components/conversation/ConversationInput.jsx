import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, Loader2 } from 'lucide-react';

export default function ConversationInput({
  onSubmit,
  onResume,
  disabled = false,
  isWaitingForSupplier = false,
  placeholder = "Type your message..."
}) {
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [ripples, setRipples] = useState([]);
  const [isFocused, setIsFocused] = useState(false);

  const inputRef = useRef(null);
  const sendButtonRef = useRef(null);

  const canSend = message.trim() !== '' && !isSending;
  const canResume = isWaitingForSupplier && !isSending;

  const handleSend = (x, y) => {
    if (!canSend && !canResume) return;

    setIsSending(true);

    if (x !== undefined && y !== undefined) {
      const newRipple = { x, y, id: Date.now() };
      setRipples(prev => [...prev, newRipple]);
      setTimeout(() => setRipples(prev => prev.filter(r => r.id !== newRipple.id)), 600);
    }

    setTimeout(() => {
      if (canResume) onResume();
      else if (message.trim()) {
        onSubmit(message.trim());
        setMessage('');
      }
      setIsSending(false);
      inputRef.current?.focus();
    }, 250);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      const rect = sendButtonRef.current?.getBoundingClientRect();
      if (rect) handleSend(rect.width / 2, rect.height / 2);
      else handleSend();
    } else if (e.key === 'Escape') {
      setMessage('');
    }
  };

  const handleButtonClick = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    handleSend(e.clientX - rect.left, e.clientY - rect.top);
  };

  return (
    <div className="relative w-full max-w-4xl mx-auto">
      {isWaitingForSupplier && (
        <div className="mb-3 px-4 py-2 bg-warning-50 border border-warning-200 rounded-lg flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-warning-600" />
          <span className="text-sm text-warning-800 font-medium">
            Waiting for supplier response...
          </span>
          <span className="text-xs text-warning-600">
            Click the arrow when ready to continue
          </span>
        </div>
      )}

      <div className="relative">
        <AnimatePresence>
          {!message && !isFocused && !isWaitingForSupplier && (
            <motion.div
              className="absolute inset-0 flex items-center pl-5 pr-14 pointer-events-none text-neutral-400"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              transition={{ duration: 0.25 }}
            >
              {placeholder}
            </motion.div>
          )}
        </AnimatePresence>

        <input
          ref={inputRef}
          type="text"
          value={message}
          onChange={e => setMessage(e.target.value)}
          onKeyDown={handleKeyPress}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          disabled={isSending || isWaitingForSupplier || disabled}
          className={`w-full px-5 pr-14 py-3.5 bg-white border-2 rounded-full transition-all duration-200 focus:outline-none text-neutral-900
            ${isFocused ? 'border-primary-500 shadow-lg shadow-primary-100' : 'border-neutral-300 hover:border-neutral-400'}
            ${isSending ? 'bg-neutral-50 cursor-not-allowed' : ''}`}
        />

        <button
          type="button"
          ref={sendButtonRef}
          onClick={handleButtonClick}
          disabled={!canSend && !canResume}
          className={`absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 rounded-full flex items-center justify-center transition-all duration-200
            ${isSending ? 'bg-primary-400 cursor-not-allowed' : (canSend || canResume ? 'bg-primary-600 hover:bg-primary-700 active:scale-95 shadow-lg shadow-primary-200' : 'bg-neutral-300 cursor-not-allowed')}`}
        >
          {isSending ? <Loader2 className="w-5 h-5 text-black animate-spin" /> : <ArrowRight className="w-5 h-5 text-black" />}
          {ripples.map(r => (
            <motion.span
              key={r.id}
              className="absolute inset-0 rounded-full bg-white opacity-30"
              style={{ left: r.x - 20, top: r.y - 20 }}
              initial={{ scale: 0, opacity: 0.5 }}
              animate={{ scale: 2.5, opacity: 0 }}
              transition={{ duration: 0.6, ease: 'easeOut' }}
            />
          ))}
        </button>
      </div>

      <div className="mt-2 px-2 flex items-center justify-between text-xs text-neutral-500">
        <span>Press <kbd className="px-1.5 py-0.5 bg-neutral-100 border border-neutral-300 rounded text-neutral-700 font-mono">Enter</kbd> to send</span>
        <span>Press <kbd className="px-1.5 py-0.5 bg-neutral-100 border border-neutral-300 rounded text-neutral-700 font-mono">Esc</kbd> to clear</span>
      </div>
    </div>
  );
}
