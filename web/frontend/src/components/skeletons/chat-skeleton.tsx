export function ChatSkeleton() {
  return (
    <div className="flex gap-4">
      {/* Avatar */}
      <div className="w-10 h-10 rounded-xl bg-zinc-800 flex-shrink-0 animate-pulse" />
      
      {/* Content */}
      <div className="flex-1 max-w-3xl bg-zinc-900/50 border border-zinc-800/50 rounded-2xl p-5 space-y-3 animate-pulse">
        <div className="h-4 bg-zinc-800 rounded w-3/4" />
        <div className="h-4 bg-zinc-800 rounded w-full" />
        <div className="h-4 bg-zinc-800 rounded w-2/3" />
        
        {/* Chart placeholder */}
        <div className="h-64 bg-zinc-800 rounded-lg mt-4" />
      </div>
    </div>
  );
}

