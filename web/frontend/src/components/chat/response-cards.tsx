"use client";

import { Card, CardContent } from "@/components/ui/card";
import { TrendingUp, MessageSquare, ThumbsUp, BarChart3 } from "lucide-react";

interface VideoItem {
  title?: string;
  channel?: string;
  views?: number;
  likes?: number;
  comments?: number;
  engagement?: number;
  ratio?: number;
  [key: string]: any;
}

interface ResponseCardsProps {
  title: string;
  data: VideoItem[];
  highlightField?: string; // 강조할 필드 (예: "ratio", "comments")
}

export function ResponseCards({ title, data, highlightField }: ResponseCardsProps) {
  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  const formatPercent = (num: number): string => {
    return `${(num * 100).toFixed(2)}%`;
  };

  return (
    <div className="mt-4 space-y-3">
      <h4 className="text-white font-semibold text-sm flex items-center gap-2 mb-4">
        <BarChart3 className="h-4 w-4 text-red-400" />
        {title}
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {data.map((item, idx) => (
          <Card
            key={idx}
            className="bg-zinc-900/50 border-zinc-800/50 hover:border-zinc-700/50 transition-all cursor-pointer"
          >
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                  {item.channel && (
                    <p className="text-xs text-zinc-400 mb-1 truncate">{item.channel}</p>
                  )}
                  <h5 className="text-white font-medium text-sm line-clamp-2 mb-2">
                    {item.title || `항목 ${idx + 1}`}
                  </h5>
                </div>
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-red-500/20 text-red-400 font-bold text-xs ml-2 flex-shrink-0">
                  {idx + 1}
                </span>
              </div>

              <div className="space-y-2">
                {item.views !== undefined && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-zinc-500 flex items-center gap-1">
                      <TrendingUp className="h-3 w-3" />
                      조회수
                    </span>
                    <span className="text-zinc-300">{formatNumber(item.views)}</span>
                  </div>
                )}

                {item.likes !== undefined && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-zinc-500 flex items-center gap-1">
                      <ThumbsUp className="h-3 w-3" />
                      좋아요
                    </span>
                    <span className="text-zinc-300">{formatNumber(item.likes)}</span>
                  </div>
                )}

                {item.comments !== undefined && (
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-zinc-500 flex items-center gap-1">
                      <MessageSquare className="h-3 w-3" />
                      댓글
                    </span>
                    <span className="text-zinc-300">{formatNumber(item.comments)}</span>
                  </div>
                )}

                {item.ratio !== undefined && (
                  <div className="flex items-center justify-between text-xs pt-2 border-t border-zinc-800">
                    <span className="text-zinc-400 font-medium">비율</span>
                    <span className={`font-bold ${
                      highlightField === 'ratio' ? 'text-emerald-400' : 'text-blue-400'
                    }`}>
                      {formatPercent(item.ratio)}
                    </span>
                  </div>
                )}

                {item.engagement !== undefined && (
                  <div className="flex items-center justify-between text-xs pt-2 border-t border-zinc-800">
                    <span className="text-zinc-400 font-medium">참여율</span>
                    <span className="text-emerald-400 font-bold">
                      {typeof item.engagement === 'number' 
                        ? `${item.engagement.toFixed(2)}%` 
                        : item.engagement}
                    </span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

