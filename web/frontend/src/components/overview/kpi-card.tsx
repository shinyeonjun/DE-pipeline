"use client";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { LucideIcon, TrendingUp, TrendingDown, Minus } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: "positive" | "negative" | "neutral";
  icon: LucideIcon;
  iconColor?: string;
  bgColor?: string;
}

export function KPICard({
  title,
  value,
  change,
  changeType = "neutral",
  icon: Icon,
  iconColor = "text-zinc-400",
  bgColor = "bg-zinc-800",
}: KPICardProps) {
  const TrendIcon =
    changeType === "positive"
      ? TrendingUp
      : changeType === "negative"
      ? TrendingDown
      : Minus;

  return (
    <Card className="bg-zinc-900/80 border-zinc-800/50 hover:border-zinc-700/50 transition-colors">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-xs font-medium text-zinc-500 uppercase tracking-wide">
              {title}
            </p>
            <p className="text-2xl font-bold text-white mt-2 tracking-tight">
              {value}
            </p>
            {change && (
              <div
                className={cn(
                  "flex items-center gap-1 mt-2 text-xs font-medium",
                  changeType === "positive" && "text-green-400",
                  changeType === "negative" && "text-red-400",
                  changeType === "neutral" && "text-zinc-500"
                )}
              >
                <TrendIcon className="h-3 w-3" />
                <span>{change}</span>
              </div>
            )}
          </div>
          <div
            className={cn(
              "p-2.5 rounded-xl",
              bgColor,
              iconColor
            )}
          >
            <Icon className="h-5 w-5" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
