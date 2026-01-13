"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, Eye, ThumbsUp, MessageSquare, Filter, BarChart3 } from "lucide-react";

interface TableData {
  rank?: number | string;
  channel?: string;
  title?: string;
  views?: number;
  likes?: number;
  comments?: number;
  engagement?: number;
  category?: string;
  // 카테고리 테이블용
  count?: number;
  avg_views?: number;
  avg_engagement?: number;
  share?: number;
  // 채널 테이블용
  total_views?: number;
}

interface StatsData {
  total_views?: number;
  avg_engagement?: number;
  count?: number;
}

interface ResponseTableProps {
  title: string;
  data: TableData[];
  stats?: StatsData;
}

export function ResponseTable({ title, data, stats }: ResponseTableProps) {
  const formatNumber = (num: number | undefined): string => {
    if (!num && num !== 0) return "-";
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  // 데이터 타입 감지 (동영상, 카테고리, 채널)
  const isVideoData = data.length > 0 && 'title' in data[0];
  const isCategoryData = data.length > 0 && 'count' in data[0] && 'share' in data[0];
  const isChannelData = data.length > 0 && 'total_views' in data[0];

  // 필터 적용 여부 확인
  const hasFilter = title.includes("필터");

  return (
    <Card className="mt-4 bg-zinc-900/50 border-zinc-800/50 overflow-hidden">
      <CardHeader className="pb-3 border-b border-zinc-800/50">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg text-white flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-red-400" />
            {title}
          </CardTitle>
          {hasFilter && (
            <span className="flex items-center gap-1 px-2 py-1 rounded-full bg-amber-500/20 text-amber-400 text-xs">
              <Filter className="h-3 w-3" />
              필터 적용됨
            </span>
          )}
        </div>

        {/* 통계 요약 */}
        {stats && (
          <div className="flex gap-4 mt-3 pt-3 border-t border-zinc-800/30">
            {stats.count !== undefined && (
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-zinc-500" />
                <span className="text-sm text-zinc-400">{stats.count}개</span>
              </div>
            )}
            {stats.total_views !== undefined && (
              <div className="flex items-center gap-2">
                <Eye className="h-4 w-4 text-blue-400" />
                <span className="text-sm text-zinc-300">{formatNumber(stats.total_views)}</span>
              </div>
            )}
            {stats.avg_engagement !== undefined && (
              <div className="flex items-center gap-2">
                <ThumbsUp className="h-4 w-4 text-emerald-400" />
                <span className="text-sm text-emerald-400">{stats.avg_engagement.toFixed(2)}%</span>
              </div>
            )}
          </div>
        )}
      </CardHeader>

      <CardContent className="p-0">
        <div className="overflow-x-auto">
          {/* 동영상 테이블 */}
          {isVideoData && (
            <table className="w-full">
              <thead>
                <tr className="bg-zinc-800/30">
                  <th className="text-center py-3 px-3 text-xs font-semibold text-zinc-400 w-16">순위</th>
                  <th className="text-left py-3 px-3 text-xs font-semibold text-zinc-400 w-28">채널</th>
                  <th className="text-left py-3 px-3 text-xs font-semibold text-zinc-400">제목</th>
                  <th className="text-right py-3 px-3 text-xs font-semibold text-zinc-400 w-24">조회수</th>
                  <th className="text-right py-3 px-3 text-xs font-semibold text-zinc-400 w-20">참여율</th>
                  <th className="text-center py-3 px-3 text-xs font-semibold text-zinc-400 w-24">카테고리</th>
                </tr>
              </thead>
              <tbody>
                {data.map((item, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-zinc-800/30 hover:bg-zinc-800/20 transition-colors"
                  >
                    <td className="py-3 px-3 text-center">
                      <span className={`inline-flex items-center justify-center w-7 h-7 rounded-lg font-bold text-sm ${
                        idx < 3
                          ? "bg-gradient-to-br from-red-500 to-red-600 text-white"
                          : "bg-zinc-800 text-zinc-400"
                      }`}>
                        {item.rank || idx + 1}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-white font-medium text-sm truncate block max-w-28">
                        {item.channel || "-"}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="text-zinc-300 text-sm line-clamp-1">
                        {item.title || "-"}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className="text-zinc-300 text-sm font-mono">
                        {formatNumber(item.views)}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right">
                      <span className={`font-medium text-sm ${
                        (item.engagement || 0) >= 5
                          ? "text-emerald-400"
                          : (item.engagement || 0) >= 2
                            ? "text-amber-400"
                            : "text-zinc-400"
                      }`}>
                        {typeof item.engagement === 'number' ? `${item.engagement.toFixed(2)}%` : item.engagement || "-"}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-center">
                      <span className="inline-block px-2 py-1 rounded-md bg-zinc-800 text-zinc-400 text-xs">
                        {item.category || "-"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* 카테고리 테이블 */}
          {isCategoryData && (
            <table className="w-full">
              <thead>
                <tr className="bg-zinc-800/30">
                  <th className="text-left py-3 px-4 text-xs font-semibold text-zinc-400">카테고리</th>
                  <th className="text-right py-3 px-4 text-xs font-semibold text-zinc-400">동영상</th>
                  <th className="text-right py-3 px-4 text-xs font-semibold text-zinc-400">평균 조회수</th>
                  <th className="text-right py-3 px-4 text-xs font-semibold text-zinc-400">평균 참여율</th>
                  <th className="text-right py-3 px-4 text-xs font-semibold text-zinc-400">점유율</th>
                </tr>
              </thead>
              <tbody>
                {data.map((item, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-zinc-800/30 hover:bg-zinc-800/20 transition-colors"
                  >
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${
                          idx === 0 ? "bg-red-400" : idx === 1 ? "bg-amber-400" : idx === 2 ? "bg-emerald-400" : "bg-zinc-500"
                        }`} />
                        <span className="text-white font-medium text-sm">
                          {item.category || "-"}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="text-zinc-300 text-sm">{item.count || 0}개</span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="text-zinc-300 text-sm font-mono">{formatNumber(item.avg_views)}</span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="text-emerald-400 font-medium text-sm">
                        {(item.avg_engagement || 0).toFixed(2)}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 h-2 bg-zinc-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-red-500 rounded-full"
                            style={{ width: `${item.share || 0}%` }}
                          />
                        </div>
                        <span className="text-zinc-300 text-sm w-12 text-right">
                          {(item.share || 0).toFixed(1)}%
                        </span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {/* 채널 테이블 */}
          {isChannelData && !isCategoryData && (
            <table className="w-full">
              <thead>
                <tr className="bg-zinc-800/30">
                  <th className="text-center py-3 px-3 text-xs font-semibold text-zinc-400 w-16">순위</th>
                  <th className="text-left py-3 px-4 text-xs font-semibold text-zinc-400">채널명</th>
                  <th className="text-right py-3 px-4 text-xs font-semibold text-zinc-400">동영상</th>
                  <th className="text-right py-3 px-4 text-xs font-semibold text-zinc-400">총 조회수</th>
                  <th className="text-right py-3 px-4 text-xs font-semibold text-zinc-400">평균 참여율</th>
                </tr>
              </thead>
              <tbody>
                {data.map((item, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-zinc-800/30 hover:bg-zinc-800/20 transition-colors"
                  >
                    <td className="py-3 px-3 text-center">
                      <span className={`inline-flex items-center justify-center w-7 h-7 rounded-lg font-bold text-sm ${
                        idx < 3
                          ? "bg-gradient-to-br from-amber-500 to-amber-600 text-white"
                          : "bg-zinc-800 text-zinc-400"
                      }`}>
                        {item.rank || idx + 1}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-white font-medium text-sm">{item.channel || "-"}</span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="text-zinc-300 text-sm">{item.count || 0}개</span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="text-zinc-300 text-sm font-mono">{formatNumber(item.total_views)}</span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className="text-emerald-400 font-medium text-sm">
                        {(item.avg_engagement || 0).toFixed(2)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
