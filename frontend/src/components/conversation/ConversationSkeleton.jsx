export default function ConversationSkeleton() {
  return (
    <div className="flex flex-col h-full p-6 space-y-4 overflow-hidden">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className={`flex gap-3 ${i % 2 === 0 ? 'flex-row-reverse' : 'flex-row'} items-start`}
        >
          {/* Avatar skeleton */}
          <div className="w-8 h-8 rounded-full bg-gray-300 flex-shrink-0" />

          {/* Message skeleton */}
          <div className="flex-1 space-y-2">
            {/* Name/placeholder */}
            <div className="h-4 bg-gray-300 rounded w-24" />

            {/* Chat bubble skeleton */}
            <div
              className={`bg-gray-200 rounded-xl p-3 space-y-2 max-w-[75%] ${i % 2 === 0 ? 'ml-auto' : ''}`}
            >
              <div className="h-4 bg-gray-300 rounded w-full" />
              <div className="h-4 bg-gray-300 rounded w-4/5" />
              <div className="h-4 bg-gray-300 rounded w-3/5" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
