import { Badge } from "@/components/ui/badge";
import { Eye, ThumbsUp, MessageSquare, TrendingUp } from "lucide-react";
import { formatNumber, formatTimeAgo } from "@/lib/formatters";
import { getCategoryName } from "@/lib/constants";
import { cn } from "@/lib/utils";

interface VideoCardProps {
  rank: number;
  title: string;
  channelName: string;
  thumbnailUrl: string;
  viewCount: number;
  likeCount: number;
  commentCount: number;
  category: string;
  isShorts?: boolean;
  hoursAgo: number;
  velocity?: number;
}

function getRankStyle(rank: number) {
  if (rank === 1) return "bg-gradient-to-br from-yellow-400 to-yellow-600 text-black";
  if (rank === 2) return "bg-gradient-to-br from-zinc-300 to-zinc-400 text-black";
  if (rank === 3) return "bg-gradient-to-br from-amber-600 to-amber-700 text-white";
  return "bg-zinc-800 text-zinc-400";
}

export function VideoCard({
  rank,
  title,
  channelName,
  thumbnailUrl,
  viewCount,
  likeCount,
  commentCount,
  category,
  isShorts = false,
  hoursAgo,
  velocity,
}: VideoCardProps) {
  const engagementRate = ((likeCount + commentCount) / viewCount * 100).toFixed(1);

  return (
    <div className="group flex gap-4 p-3 rounded-xl bg-zinc-800/30 hover:bg-zinc-800/60 transition-all duration-200 border border-transparent hover:border-zinc-700/50">
      {/* Rank Badge */}
      <div className="flex items-center">
        <div className={cn(
          "w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold shadow-lg",
          getRankStyle(rank)
        )}>
          {rank}
        </div>
      </div>

      {/* Thumbnail */}
      <div className="relative w-32 h-20 rounded-lg overflow-hidden bg-zinc-800 flex-shrink-0 shadow-md">
        <img
          src={thumbnailUrl || "/placeholder.jpg"}
          alt={title}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        />
        {isShorts && (
          <Badge className="absolute top-1 left-1 bg-red-500/90 text-white text-[10px] px-1.5 py-0 font-medium">
            쇼츠
          </Badge>
        )}
        <div className="absolute bottom-1 right-1 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded">
          {formatTimeAgo(hoursAgo)}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0 flex flex-col justify-between py-0.5">
        <div>
          <h3 className="text-white font-medium text-sm leading-tight line-clamp-2 group-hover:text-red-400 transition-colors">
            {title}
          </h3>
          <p className="text-xs text-zinc-500 mt-1">{channelName}</p>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1 text-zinc-400">
            <Eye className="h-3 w-3" />
            <span className="font-medium text-white">{formatNumber(viewCount)}</span>
          </span>
          <span className="flex items-center gap-1 text-zinc-400">
            <ThumbsUp className="h-3 w-3" />
            {formatNumber(likeCount)}
          </span>
          <span className="flex items-center gap-1 text-zinc-400">
            <MessageSquare className="h-3 w-3" />
            {formatNumber(commentCount)}
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="flex flex-col items-end justify-between py-0.5 flex-shrink-0">
        <Badge variant="outline" className="border-zinc-700 text-zinc-400 text-[10px] px-2">
          {getCategoryName(category)}
        </Badge>

        <div className="flex flex-col items-end gap-1">
          <div className="flex items-center gap-1 text-xs">
            <span className="text-zinc-500">참여율</span>
            <span className={cn(
              "font-medium",
              Number(engagementRate) >= 5 ? "text-green-400" :
              Number(engagementRate) >= 3 ? "text-yellow-400" : "text-zinc-400"
            )}>
              {engagementRate}%
            </span>
          </div>
          {velocity && (
            <div className="flex items-center gap-1 text-[10px] text-emerald-400">
              <TrendingUp className="h-3 w-3" />
              {formatNumber(velocity)}/h
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
