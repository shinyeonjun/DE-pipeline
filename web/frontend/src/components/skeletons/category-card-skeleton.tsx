export function CategoryCardSkeleton() {
  return (
    <div className="bg-zinc-900/50 border border-zinc-800/50 rounded-lg p-3 animate-pulse">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 flex-1">
          <div className="w-4 h-4 bg-zinc-800 rounded" />
          <div className="h-4 bg-zinc-800 rounded w-16" />
        </div>
        <div className="h-4 bg-zinc-800 rounded w-12" />
      </div>
      <div className="grid grid-cols-2 gap-2">
        <div>
          <div className="h-3 bg-zinc-800 rounded w-12 mb-1" />
          <div className="h-4 bg-zinc-800 rounded w-8" />
        </div>
        <div>
          <div className="h-3 bg-zinc-800 rounded w-12 mb-1" />
          <div className="h-4 bg-zinc-800 rounded w-12" />
        </div>
      </div>
    </div>
  );
}

