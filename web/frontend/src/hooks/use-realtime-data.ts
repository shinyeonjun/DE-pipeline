/**
 * Supabase Realtime 훅
 * DB 변경사항을 실시간으로 감지하여 UI 업데이트
 */

import { useEffect, useState } from 'react';
import { supabase } from '@/lib/supabase';
import { api } from '@/lib/api';

export function useRealtimeData() {
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    console.log('🔴 Realtime 구독 시작...');

    // fact_video_snapshots 테이블 변경 감지
    const channel = supabase
      .channel('video-snapshots-changes')
      .on(
        'postgres_changes',
        {
          event: '*', // INSERT, UPDATE, DELETE 모두 감지
          schema: 'public',
          table: 'fact_video_snapshots'
        },
        (payload) => {
          console.log('📡 DB 변경 감지:', payload);
          setLastUpdate(new Date());
        }
      )
      .subscribe((status) => {
        console.log('🟢 Realtime 상태:', status);
        setIsConnected(status === 'SUBSCRIBED');
      });

    // Cleanup
    return () => {
      console.log('🔴 Realtime 구독 해제');
      supabase.removeChannel(channel);
    };
  }, []);

  return { lastUpdate, isConnected };
}

// 트렌딩 비디오 Realtime 훅
export function useRealtimeTrending() {
  const [videos, setVideos] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { lastUpdate, isConnected } = useRealtimeData();

  // 초기 로드
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        const data = await api.getTrendingVideos();
        setVideos(data.videos);
      } catch (error) {
        console.error('Failed to load trending videos:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []); // 초기 로드만

  // DB 변경 시 자동 리로드
  useEffect(() => {
    if (!isLoading) {
      const loadData = async () => {
        try {
          const data = await api.getTrendingVideos();
          setVideos(data.videos);
          console.log('📊 트렌딩 데이터 업데이트됨:', new Date(lastUpdate).toLocaleTimeString());
        } catch (error) {
          console.error('Failed to reload trending videos:', error);
        }
      };

      loadData();
    }
  }, [lastUpdate]); // lastUpdate 변경 시만

  return { videos, isLoading, isConnected, lastUpdate };
}

// 오버뷰 통계 Realtime 훅
export function useRealtimeOverview() {
  const [stats, setStats] = useState<any>(null);
  const [categoryData, setCategoryData] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { lastUpdate, isConnected } = useRealtimeData();

  // 초기 로드
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        
        // 오버뷰 통계
        const overviewStats = await api.getOverviewStats();
        setStats(overviewStats);
        
        // 카테고리 분포
        const distribution = await api.getCategoryDistribution();
        const total = Object.values(distribution).reduce((sum: number, count) => sum + (count as number), 0);
        
        const colors = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899'];
        const chartData = Object.entries(distribution).map(([name, count], index) => ({
          name,
          value: Math.round((count as number) / total * 100),
          color: colors[index % colors.length]
        }));
        
        setCategoryData(chartData);
      } catch (error) {
        console.error('Failed to load overview data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []); // 초기 로드만

  // DB 변경 시 자동 리로드
  useEffect(() => {
    if (!isLoading) {
      const loadData = async () => {
        try {
          const overviewStats = await api.getOverviewStats();
          setStats(overviewStats);
          
          const distribution = await api.getCategoryDistribution();
          const total = Object.values(distribution).reduce((sum: number, count) => sum + (count as number), 0);
          
          const colors = ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6', '#ec4899'];
          const chartData = Object.entries(distribution).map(([name, count], index) => ({
            name,
            value: Math.round((count as number) / total * 100),
            color: colors[index % colors.length]
          }));
          
          setCategoryData(chartData);
          console.log('📊 오버뷰 데이터 업데이트됨:', new Date(lastUpdate).toLocaleTimeString());
        } catch (error) {
          console.error('Failed to reload overview data:', error);
        }
      };

      loadData();
    }
  }, [lastUpdate]); // lastUpdate 변경 시만

  return { stats, categoryData, isLoading, isConnected, lastUpdate };
}

