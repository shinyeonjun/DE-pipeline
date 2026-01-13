"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { supabase } from './supabase';

interface RealtimeContextType {
  isConnected: boolean;
  lastUpdate: Date | null;
}

const RealtimeContext = createContext<RealtimeContextType>({
  isConnected: false,
  lastUpdate: null,
});

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  useEffect(() => {
    console.log('🔴 Realtime 전역 구독 시작...');

    const channel = supabase
      .channel('global-video-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
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

    return () => {
      console.log('🔴 Realtime 전역 구독 해제');
      supabase.removeChannel(channel);
    };
  }, []);

  return (
    <RealtimeContext.Provider value={{ isConnected, lastUpdate }}>
      {children}
    </RealtimeContext.Provider>
  );
}

export function useRealtime() {
  return useContext(RealtimeContext);
}

