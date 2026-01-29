"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Eye, ThumbsUp, MessageSquare, Clock } from "lucide-react";
import type { VideoData } from "@/types";
import { formatNumber, formatTimeAgo, getEngagementColorClass } from "@/lib/formatters";
import { getCategoryName } from "@/lib/constants";
import { cn } from "@/lib/utils";

interface VideoTableProps {
  videos: VideoData[];
}

function getRankStyle(rank: number) {
  if (rank === 1) return "bg-gradient-to-br from-yellow-400 to-yellow-600 text-black font-bold";
  if (rank === 2) return "bg-gradient-to-br from-zinc-300 to-zinc-400 text-black font-bold";
  if (rank === 3) return "bg-gradient-to-br from-amber-600 to-amber-700 text-white font-bold";
  if (rank <= 10) return "bg-zinc-700 text-white font-semibold";
  return "bg-zinc-800/50 text-zinc-400";
}

export function VideoTable({ videos }: VideoTableProps) {
  return (
    <Card className="bg-zinc-900 border-zinc-800 overflow-hidden">
      <CardContent className="p-0">
        <div className="overflow-x-auto">
          <Table>
          <TableHeader>
            <TableRow className="border-zinc-800 bg-zinc-800/30">
              <TableHead className="text-zinc-400 w-16 text-center">순위</TableHead>
              <TableHead className="text-zinc-400">영상 정보</TableHead>
              <TableHead className="text-zinc-400 w-32">채널</TableHead>
              <TableHead className="text-zinc-400 w-28">카테고리</TableHead>
              <TableHead className="text-zinc-400 text-right w-24">조회수</TableHead>
              <TableHead className="text-zinc-400 text-right w-24">좋아요</TableHead>
              <TableHead className="text-zinc-400 text-right w-20">댓글</TableHead>
              <TableHead className="text-zinc-400 text-right w-20">참여율</TableHead>
              <TableHead className="text-zinc-400 text-right w-24">업로드</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {videos.map((video) => (
              <TableRow
                key={video.rank}
                className={cn(
                  "border-zinc-800/50 hover:bg-zinc-800/40 transition-colors",
                  video.rank <= 3 && "bg-zinc-800/20"
                )}
              >
                <TableCell className="text-center">
                  <div className={cn(
                    "w-8 h-8 rounded-lg flex items-center justify-center text-sm mx-auto",
                    getRankStyle(video.rank)
                  )}>
                    {video.rank}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="relative w-24 h-14 rounded-lg overflow-hidden bg-zinc-800 flex-shrink-0 shadow-md">
                      <img
                        src={video.thumbnailUrl}
                        alt={`${video.title} 썸네일`}
                        className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                        loading="lazy"
                        decoding="async"
                      />
                      {video.isShorts && (
                        <Badge
                          className="absolute top-1 left-1 bg-red-500/90 text-white text-[9px] px-1 py-0 font-medium"
                          aria-label="쇼츠 영상"
                        >
                          쇼츠
                        </Badge>
                      )}
                    </div>
                    <div className="min-w-0">
                      <p className="text-white text-sm font-medium truncate max-w-xs hover:text-red-400 transition-colors cursor-pointer">
                        {video.title}
                      </p>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <span className="text-zinc-400 text-sm truncate block max-w-[120px]">
                    {video.channelName}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="border-zinc-700 text-zinc-400 text-xs">
                    {getCategoryName(video.category)}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    <Eye className="h-3.5 w-3.5 text-blue-400" aria-hidden="true" />
                    <span className="text-white font-medium text-sm">{formatNumber(video.viewCount)}</span>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    <ThumbsUp className="h-3.5 w-3.5 text-green-400" aria-hidden="true" />
                    <span className="text-zinc-300 text-sm">{formatNumber(video.likeCount)}</span>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1.5">
                    <MessageSquare className="h-3.5 w-3.5 text-purple-400" aria-hidden="true" />
                    <span className="text-zinc-300 text-sm">{formatNumber(video.commentCount)}</span>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <Badge
                    className={cn("text-xs", getEngagementColorClass(video.engagementRate))}
                    aria-label={`참여율: ${video.engagementRate}%`}
                  >
                    {video.engagementRate}%
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  <div className="flex items-center justify-end gap-1 text-zinc-500 text-xs">
                    <Clock className="h-3 w-3" />
                    {formatTimeAgo(video.hoursAgo)}
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        </div>
      </CardContent>
    </Card>
  );
}
