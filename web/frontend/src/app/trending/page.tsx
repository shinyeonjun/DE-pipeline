"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Eye, ThumbsUp, MessageSquare, Clock, Play, TrendingUp, TrendingDown,
  Minus, Music, Gamepad2, Film, Users, Target, Zap, Video, BarChart3,
  ChevronRight, ChevronLeft
} from "lucide-react";
import { LineChart, Line, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { formatNumber, formatTimeAgo } from "@/lib/formatters";
import { getCategoryName } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { useSidebarState } from "@/hooks";
import { VideoCardSkeleton, CategoryCardSkeleton } from "@/components/skeletons";
import { api, type VideoSnapshot, type CategoryStats } from "@/lib/api";
import { useRealtime } from "@/lib/realtime-provider";

type FilterType = "all" | string;

export default function TrendingPage() {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [filter, setFilter] = useState<FilterType>("all");
  const { sidebarCollapsed, toggleSidebar, isHydrated } = useSidebarState();

  // Realtime 연결 상태
  const { isConnected, lastUpdate } = useRealtime();

  // 데이터
  const [videos, setVideos] = useState<VideoSnapshot[]>([]);
  const [categoryStats, setCategoryStats] = useState<CategoryStats[]>([]);
  const [topChannels, setTopChannels] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [hasLoaded, setHasLoaded] = useState(false);

  // 중복 실행 방지
  const lastUpdateRef = useRef<Date | null>(null);
  const loadingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const isLoadingRef = useRef(false); // 로딩 중 중복 방지

  // 초기 데이터 로드
  useEffect(() => {
    // 이미 로딩 중이면 스킵
    if (isLoadingRef.current) {
      console.log('⏭️ 이미 로딩 중');
      return;
    }

    // 데이터가 이미 있으면 스킵
    if (videos.length > 0 && hasLoaded) {
      console.log('⏭️ 데이터 이미 있음:', videos.length);
      return;
    }

    isLoadingRef.current = true;
    let isMounted = true;

    const loadData = async () => {
      try {
        setIsLoading(true);
        console.log('📊 트렌딩 데이터 로드 시작');

        // API 호출
        const trendingResponse = await api.getTrendingVideos();
        const catStats = await api.getCategoryStats();
        const channels = await api.getTopChannels(6);

        console.log('📦 API 응답 확인:', {
          trendingResponse,
          catStats,
          channels
        });

        if (!isMounted) {
          console.log('⚠️ 컴포넌트 언마운트됨 - 데이터 설정 취소');
          return;
        }

        // 데이터 설정
        const videosData = trendingResponse?.videos || [];
        console.log('✅ 비디오 개수:', videosData.length);

        setVideos(videosData);
        setCategoryStats(catStats || []);
        setTopChannels(channels || []);
        setHasLoaded(true);
        setIsLoading(false);
        isLoadingRef.current = false;

        console.log('✅ 데이터 로드 완료 - videos:', videosData.length);
      } catch (error) {
        console.error('❌ 데이터 로드 실패:', error);
        if (isMounted) {
          setIsLoading(false);
          isLoadingRef.current = false;
        }
      }
    };

    loadData();

    return () => {
      isMounted = false;
      isLoadingRef.current = false; // 언마운트 시 리셋
    };
  }, []); // 빈 배열: 마운트 시 한 번만 실행

  // Realtime 변경 감지 시 자동 리로드 (디바운스 + 병렬)
  useEffect(() => {
    // 초기 로드가 완료되지 않았거나 lastUpdate가 없으면 스킵
    if (!lastUpdate || !hasLoaded) return;

    // 첫 로딩 직후에는 실시간 업데이트 로직이 중복 실행되지 않도록 방지
    // (이미 최신 데이터를 로드했으므로 Ref만 동기화하고 스킵)
    if (lastUpdateRef.current === null) {
      lastUpdateRef.current = lastUpdate;
      console.log('🔄 초기 로드 완료 - 실시간 업데이트 중복 방지');
      return;
    }

    // 같은 시간에 여러번 업데이트 방지
    if (lastUpdateRef.current.getTime() === lastUpdate.getTime()) {
      return;
    }
    lastUpdateRef.current = lastUpdate;

    let isMounted = true;

    // 기존 타임아웃 취소
    if (loadingTimeoutRef.current) {
      clearTimeout(loadingTimeoutRef.current);
    }

    // 디바운스: 500ms 후 실행
    loadingTimeoutRef.current = setTimeout(async () => {
      try {
        console.log('🔄 트렌딩 데이터 실시간 업데이트 시작');

        // 🚀 병렬 호출 + 캐시 스킵
        const [trendingData, catStats, channels] = await Promise.all([
          api.getTrendingVideos(true),
          api.getCategoryStats(true),
          api.getTopChannels(6, true)
        ]);

        if (!isMounted) return;

        setVideos(trendingData.videos);
        setCategoryStats(catStats);
        setTopChannels(channels);

        console.log('✅ 트렌딩 데이터 업데이트 완료');
      } catch (error) {
        console.error('❌ 트렌딩 데이터 업데이트 실패:', error);
      }
    }, 500);

    return () => {
      isMounted = false;
      if (loadingTimeoutRef.current) {
        clearTimeout(loadingTimeoutRef.current);
        loadingTimeoutRef.current = null;
      }
    };
  }, [lastUpdate, hasLoaded]); // lastUpdate 변경 시에만 실행

  const filteredVideos = filter === "all"
    ? videos
    : videos.filter(v => v.category_name === filter);

  // 카테고리 아이콘 매핑
  const getCategoryIcon = (name: string) => {
    if (name.includes('음악') || name.includes('Music')) return Music;
    if (name.includes('게임') || name.includes('Gaming')) return Gamepad2;
    if (name.includes('엔터') || name.includes('Entertainment')) return Film;
    return Video;
  };

  const getCategoryColor = (index: number) => {
    const colors = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899'];
    return colors[index % colors.length];
  };

  return (
    <div className="flex h-full bg-zinc-950">
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-zinc-800/30 px-8 py-6">
          <h1 className="text-2xl font-bold text-white mb-2">트렌딩 분석</h1>
          <div className="flex items-center gap-4">
            <p className="text-sm text-zinc-400">실시간 순위 + 카테고리 + 채널 통합 분석</p>
            <div className="flex items-center gap-2">
              <div className={`w-1.5 h-1.5 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`} />
              <span className="text-xs text-zinc-500">
                {isConnected ? 'Live' : '연결 중...'}
              </span>
            </div>
            {lastUpdate && (
              <span className="text-xs text-zinc-600">
                {lastUpdate.toLocaleTimeString('ko-KR')}
              </span>
            )}
          </div>
        </div>

        {/* Category Filter */}
        <div className="border-b border-zinc-800/30 px-8 py-4">
          <Tabs value={filter} onValueChange={(v) => setFilter(v as FilterType)}>
            <TabsList className="bg-zinc-900/90 border border-zinc-800">
              <TabsTrigger value="all" className="data-[state=active]:bg-red-500/10 data-[state=active]:text-white">
                전체 ({videos.length})
              </TabsTrigger>
              {categoryStats.slice(0, 3).map((cat) => (
                <TabsTrigger
                  key={cat.category_name}
                  value={cat.category_name}
                  className="data-[state=active]:bg-red-500/10 data-[state=active]:text-white"
                >
                  {cat.category_name} ({cat.video_count})
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </div>

        {/* Video List */}
        <div className="flex-1 overflow-auto p-8">
          <div className="max-w-6xl mx-auto space-y-3">
            {isLoading ? (
              // Skeleton Loading
              Array.from({ length: 8 }).map((_, i) => (
                <VideoCardSkeleton key={i} />
              ))
            ) : filteredVideos.length === 0 ? (
              <div className="text-center py-12 text-zinc-500">
                <p>데이터가 없습니다.</p>
                <p className="text-sm mt-2">videos: {videos.length}, filtered: {filteredVideos.length}, isLoading: {String(isLoading)}</p>
              </div>
            ) : (
              filteredVideos.map((video, index) => (
                <Card
                  key={video.video_id}
                  className={cn(
                    "bg-zinc-900/50 border-zinc-800/50 transition-all cursor-pointer",
                    hoveredIndex === index && "border-zinc-700 bg-zinc-900/70"
                  )}
                  onMouseEnter={() => setHoveredIndex(index)}
                  onMouseLeave={() => setHoveredIndex(null)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center gap-4">
                      {/* Rank + Velocity */}
                      <div className="flex flex-col items-center gap-2">
                        <div className={cn(
                          "w-11 h-11 rounded-xl flex items-center justify-center",
                          video.trending_rank === 1 ? "bg-red-500" :
                            video.trending_rank <= 3 ? "bg-zinc-700" :
                              video.trending_rank <= 10 ? "bg-zinc-800" : "bg-zinc-800/50"
                        )}>
                          <span className={cn(
                            "font-bold",
                            video.trending_rank <= 10 ? "text-white text-base" : "text-zinc-500 text-sm"
                          )}>
                            {video.trending_rank}
                          </span>
                        </div>
                        {video.view_velocity !== null && video.view_velocity !== undefined && (
                          <div className={cn(
                            "flex items-center gap-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded",
                            video.view_velocity > 0 ? "text-emerald-400 bg-emerald-500/10" : "text-zinc-500 bg-zinc-800"
                          )}>
                            {video.view_velocity > 0 ? "🔥" : "-"}
                          </div>
                        )}
                      </div>

                      {/* Thumbnail */}
                      <div className="relative w-44 h-26 rounded-lg overflow-hidden bg-zinc-800 flex-shrink-0">
                        {video.thumbnail_url && (
                          <img
                            src={video.thumbnail_url}
                            alt={video.title}
                            className={cn(
                              "w-full h-full object-cover transition-all duration-500",
                              hoveredIndex === index && "scale-105"
                            )}
                          />
                        )}
                        {video.is_shorts && (
                          <Badge className="absolute top-1.5 left-1.5 bg-red-500/90 text-white text-[10px] px-1.5">
                            쇼츠
                          </Badge>
                        )}
                        {hoveredIndex === index && (
                          <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                            <Play className="h-10 w-10 text-white" fill="white" />
                          </div>
                        )}
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between mb-2">
                          <h3 className={cn(
                            "font-semibold line-clamp-2 flex-1",
                            video.trending_rank <= 3 ? "text-white text-base" : "text-white text-sm",
                            hoveredIndex === index && "text-red-400"
                          )}>
                            {video.title}
                          </h3>
                          {video.category_name && (
                            <Badge variant="outline" className="border-zinc-700 text-zinc-400 text-xs ml-2 flex-shrink-0">
                              {video.category_name}
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-zinc-500 mb-3">{video.channel_name}</p>

                        {/* Stats */}
                        <div className="grid grid-cols-4 gap-4">
                          <div>
                            <p className="text-xs text-zinc-500 mb-0.5">조회수</p>
                            <p className="text-white font-medium text-sm">{formatNumber(video.view_count)}</p>
                          </div>
                          <div>
                            <p className="text-xs text-zinc-500 mb-0.5">좋아요</p>
                            <p className="text-white font-medium text-sm">{formatNumber(video.like_count)}</p>
                          </div>
                          <div>
                            <p className="text-xs text-zinc-500 mb-0.5">참여율</p>
                            <span className={cn(
                              "text-xs font-medium px-2 py-0.5 rounded",
                              (video.engagement_rate || 0) >= 5 ? "bg-green-500/10 text-green-400" :
                                (video.engagement_rate || 0) >= 3 ? "bg-yellow-500/10 text-yellow-400" :
                                  "bg-zinc-800 text-zinc-400"
                            )}>
                              {video.engagement_rate?.toFixed(1) || 0}%
                            </span>
                          </div>
                          <div>
                            <p className="text-xs text-zinc-500 mb-0.5">업로드</p>
                            <p className="text-zinc-400 text-xs">{formatTimeAgo(video.hours_since_published || 0)}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Right Sidebar - Analytics */}
      <div
        className={cn(
          "border-l border-zinc-800/30 bg-zinc-950/50 overflow-hidden flex-shrink-0",
          isHydrated && "transition-all duration-300",
          sidebarCollapsed ? "w-12" : "w-80"
        )}
        suppressHydrationWarning
      >
        {/* Toggle Button */}
        <div className="h-full flex flex-col">
          <div className="border-b border-zinc-800/30 h-16 flex items-center px-3">
            <button
              onClick={toggleSidebar}
              className="w-8 h-8 rounded-lg bg-zinc-800/50 hover:bg-zinc-700/50 flex items-center justify-center text-zinc-400 hover:text-white transition-all"
              aria-label={sidebarCollapsed ? "사이드바 펼치기" : "사이드바 접기"}
            >
              {sidebarCollapsed ? (
                <ChevronLeft className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
          </div>

          {!sidebarCollapsed && (
            <div className="flex-1 overflow-auto p-6 space-y-6">
              {/* Category Stats */}
              <div>
                <h3 className="text-white font-semibold text-sm mb-4 flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-purple-400" />
                  카테고리 현황
                </h3>
                <div className="space-y-2">
                  {isLoading ? (
                    Array.from({ length: 4 }).map((_, i) => (
                      <CategoryCardSkeleton key={i} />
                    ))
                  ) : (
                    categoryStats.map((cat) => {
                      const Icon = getCategoryIcon(cat.category_name);
                      return (
                        <Card key={cat.category_name} className="p-3 bg-zinc-900/50 border-zinc-800/50 hover:border-zinc-700 transition-colors cursor-pointer">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Icon className="h-4 w-4 text-red-400" />
                              <span className="text-white font-medium text-sm">{cat.category_name}</span>
                            </div>
                            <span className="text-xs font-semibold text-emerald-400">
                              {cat.trend}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div>
                              <p className="text-zinc-500">영상 수</p>
                              <p className="text-white font-medium">{cat.video_count}개</p>
                            </div>
                            <div>
                              <p className="text-zinc-500">참여율</p>
                              <p className="text-white font-medium">{cat.avg_engagement_rate}%</p>
                            </div>
                          </div>
                        </Card>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Top Channels */}
              <div>
                <h3 className="text-white font-semibold text-sm mb-4 flex items-center gap-2">
                  <Users className="h-4 w-4 text-blue-400" />
                  상위 채널
                </h3>
                <div className="space-y-2">
                  {topChannels.map((channel, i) => (
                    <Card key={channel.channel_id} className="p-3 bg-zinc-900/50 border-zinc-800/50">
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg bg-gradient-to-br from-red-500 to-red-600 flex items-center justify-center text-white text-xs font-bold`}>
                          {i + 1}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-white font-medium text-sm truncate">{channel.channel_name}</p>
                          <p className="text-zinc-400 text-xs">{channel.video_count}개 영상</p>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>

              {/* Distribution */}
              <div>
                <h3 className="text-white font-semibold text-sm mb-4">카테고리 분포</h3>
                <ResponsiveContainer width="100%" height={150}>
                  <PieChart>
                    <Pie
                      data={categoryStats}
                      cx="50%"
                      cy="50%"
                      innerRadius={40}
                      outerRadius={60}
                      dataKey="video_count"
                    >
                      {categoryStats.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={getCategoryColor(index)} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-1 mt-2">
                  {categoryStats.map((cat, index) => (
                    <div key={cat.category_name} className="flex items-center justify-between text-xs">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getCategoryColor(index) }} />
                        <span className="text-zinc-400">{cat.category_name}</span>
                      </div>
                      <span className="text-white font-medium">{cat.video_count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
