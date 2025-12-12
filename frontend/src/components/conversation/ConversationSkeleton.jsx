// src/components/conversation/ConversationSkeleton.jsx
export default function ConversationSkeleton() {
  return (
    <div className="flex flex-col space-y-6 animate-pulse w-full px-4 md:px-6 py-3">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className={`flex items-start gap-4 w-full ${i % 2 === 0 ? 'flex-row-reverse' : ''}`}
        >
          {/* Avatar skeleton */}
          <div className="w-10 h-10 rounded-full bg-neutral-200 flex-shrink-0" />

          {/* Message skeleton */}
          <div className="flex-1 space-y-2">
            {/* Name/placeholder bar */}
            <div className="h-4 bg-neutral-200 rounded w-32" />

            {/* Chat bubble */}
            <div
              className={`bg-neutral-200 rounded-2xl p-3 space-y-2 w-full max-w-[80%] ${i % 2 === 0 ? 'ml-auto' : ''
                }`}
            >
              <div className="h-4 bg-neutral-300 rounded w-full" />
              <div className="h-4 bg-neutral-300 rounded w-4/5" />
              <div className="h-4 bg-neutral-300 rounded w-3/5" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
