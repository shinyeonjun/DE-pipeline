"use client";

import { Trophy } from "lucide-react";
import { calculateLevel } from "@/lib/animations";
import { cn } from "@/lib/utils";

interface LevelBadgeProps {
  viewCount: number;
  showProgress?: boolean;
  size?: "sm" | "md" | "lg";
}

export function LevelBadge({ viewCount, showProgress = false, size = "md" }: LevelBadgeProps) {
  const { level, progress } = calculateLevel(viewCount);

  const sizeClasses = {
    sm: "w-8 h-8 text-xs",
    md: "w-10 h-10 text-sm",
    lg: "w-12 h-12 text-base",
  };

  const iconSizes = {
    sm: "h-3 w-3",
    md: "h-4 w-4",
    lg: "h-5 w-5",
  };

  const getLevelColor = (level: number) => {
    if (level >= 15) return "from-purple-500 to-pink-500";
    if (level >= 12) return "from-red-500 to-orange-500";
    if (level >= 9) return "from-yellow-500 to-amber-500";
    if (level >= 6) return "from-blue-500 to-cyan-500";
    return "from-zinc-600 to-zinc-700";
  };

  return (
    <div className="relative group">
      <div
        className={cn(
          "rounded-full bg-gradient-to-br flex items-center justify-center font-bold text-white shadow-lg transition-transform hover:scale-110",
          sizeClasses[size],
          getLevelColor(level)
        )}
      >
        <Trophy className={cn(iconSizes[size], "mr-0.5")} />
        <span>{level}</span>
      </div>

      {/* 툴팁 */}
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10">
        <div className="bg-zinc-900 border border-zinc-700 rounded-lg px-3 py-2 text-xs text-white whitespace-nowrap shadow-xl">
          <p className="font-semibold">레벨 {level}</p>
          {showProgress && (
            <>
              <div className="w-24 h-1.5 bg-zinc-700 rounded-full mt-1.5 overflow-hidden">
                <div
                  className={cn("h-full bg-gradient-to-r", getLevelColor(level))}
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-zinc-400 mt-1">{Math.floor(progress)}% → 레벨 {level + 1}</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

