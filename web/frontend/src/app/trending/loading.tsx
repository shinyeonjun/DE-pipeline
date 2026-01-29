import { VideoCardSkeleton, CategoryCardSkeleton } from "@/components/skeletons";

export default function TrendingLoading() {
  return (
    <div className="flex h-full bg-zinc-950">
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-zinc-800/30 px-8 py-6">
          <div className="h-8 bg-zinc-800 rounded w-48 mb-2 animate-pulse" />
          <div className="h-4 bg-zinc-800 rounded w-64 animate-pulse" />
        </div>

        {/* Filter */}
        <div className="border-b border-zinc-800/30 px-8 py-4">
          <div className="h-10 bg-zinc-800 rounded w-96 animate-pulse" />
        </div>

        {/* Video List */}
        <div className="flex-1 overflow-auto p-8">
          <div className="max-w-6xl mx-auto space-y-3">
            {Array.from({ length: 8 }).map((_, i) => (
              <VideoCardSkeleton key={i} />
            ))}
          </div>
        </div>
      </div>

      {/* Right Sidebar */}
      <div className="w-80 border-l border-zinc-800/30 bg-zinc-950/50">
        <div className="p-6 space-y-6">
          <div>
            <div className="h-5 bg-zinc-800 rounded w-32 mb-4 animate-pulse" />
            <div className="space-y-2">
              {Array.from({ length: 4 }).map((_, i) => (
                <CategoryCardSkeleton key={i} />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

