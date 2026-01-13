"use client";

import { getEarnedBadges, type Badge } from "@/lib/animations";
import { cn } from "@/lib/utils";

interface BadgeCollectionProps {
  video: {
    viewCount: number;
    likeCount: number;
    commentCount: number;
    engagementRate: string;
    hoursAgo: number;
  };
  maxDisplay?: number;
}

export function BadgeCollection({ video, maxDisplay = 3 }: BadgeCollectionProps) {
  const earnedBadges = getEarnedBadges(video);
  const displayBadges = earnedBadges.slice(0, maxDisplay);
  const remainingCount = Math.max(0, earnedBadges.length - maxDisplay);

  if (earnedBadges.length === 0) return null;

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {displayBadges.map((badge) => (
        <BadgeItem key={badge.id} badge={badge} />
      ))}
      {remainingCount > 0 && (
        <div className="w-7 h-7 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center text-[10px] text-zinc-400 font-semibold">
          +{remainingCount}
        </div>
      )}
    </div>
  );
}

function BadgeItem({ badge }: { badge: Badge }) {
  return (
    <div className="relative group">
      <div
        className={cn(
          "w-7 h-7 rounded-lg bg-gradient-to-br flex items-center justify-center text-base shadow-md cursor-pointer transition-transform hover:scale-125",
          badge.color
        )}
      >
        {badge.icon}
      </div>

      {/* 툴팁 */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
        <div className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white whitespace-nowrap shadow-xl">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">{badge.icon}</span>
            <p className="font-semibold">{badge.name}</p>
          </div>
          <p className="text-zinc-400">{badge.description}</p>
        </div>
      </div>
    </div>
  );
}

