export function VideoCardSkeleton() {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800/50 rounded-lg p-4 animate-pulse">
      <div className="flex items-center gap-4">
        {/* Rank */}
        <div className="w-11 h-11 bg-zinc-800 rounded-xl flex-shrink-0" />
        
        {/* Thumbnail */}
        <div className="w-44 h-26 bg-zinc-800 rounded-lg flex-shrink-0" />
        
        {/* Info */}
        <div className="flex-1 space-y-3">
          {/* Title */}
          <div className="h-5 bg-zinc-800 rounded w-3/4" />
          {/* Channel */}
          <div className="h-4 bg-zinc-800 rounded w-1/4" />
          {/* Stats */}
          <div className="grid grid-cols-4 gap-4">
            <div className="h-10 bg-zinc-800 rounded" />
            <div className="h-10 bg-zinc-800 rounded" />
            <div className="h-10 bg-zinc-800 rounded" />
            <div className="h-10 bg-zinc-800 rounded" />
          </div>
          {/* Chart */}
          <div className="h-10 bg-zinc-800 rounded" />
        </div>
      </div>
    </div>
  );
}

