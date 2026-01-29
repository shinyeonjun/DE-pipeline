/**
 * API 클라이언트 (최적화됨)
 * - 캐싱, 병렬 호출, 타임아웃 지원
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const CACHE_DURATION = 5000; // 5초 캐시

// 간단한 메모리 캐시
interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

const cache = new Map<string, CacheEntry<any>>();

// 캐시 헬퍼
function getCached<T>(key: string): T | null {
  const entry = cache.get(key);
  if (!entry) return null;

  const now = Date.now();
  if (now - entry.timestamp > CACHE_DURATION) {
    cache.delete(key);
    return null;
  }

  return entry.data;
}

function setCache<T>(key: string, data: T): void {
  cache.set(key, { data, timestamp: Date.now() });
}

// Fetch with timeout and retry
async function fetchWithTimeout(
  url: string,
  timeout = 10000,
  retries = 1
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
      }
    });
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response;
  } catch (error: any) {
    clearTimeout(timeoutId);

    // 네트워크 에러인 경우 재시도
    if (retries > 0 && (error.name === 'AbortError' || error.message.includes('fetch'))) {
      console.warn(`재시도 중... (${retries}회 남음)`);
      await new Promise(resolve => setTimeout(resolve, 1000));
      return fetchWithTimeout(url, timeout, retries - 1);
    }

    throw error;
  }
}

// API 응답 타입
export interface VideoSnapshot {
  video_id: string;
  snapshot_at: string;
  title: string;
  channel_id: string;
  channel_name: string;
  category_id?: number;
  category_name?: string;
  published_at?: string;
  duration_sec?: number;
  is_shorts: boolean;
  view_count: number;
  like_count: number;
  comment_count: number;
  trending_rank: number;
  thumbnail_url?: string;
  hours_since_published?: number;
  engagement_rate?: number;
  view_velocity?: number;
}

export interface TrendingResponse {
  total: number;
  snapshot_at: string;
  videos: VideoSnapshot[];
}

export interface CategoryStats {
  category_name: string;
  video_count: number;
  avg_view_count: number;
  avg_engagement_rate: number;
  shorts_ratio: number;
  trend: string;
  [key: string]: any;
}

export interface OverviewStats {
  total_videos: number;
  total_views: number;
  total_likes: number;
  total_comments: number;
  avg_engagement_rate: number;
  shorts_ratio: number;
  snapshot_at: string;
}

export interface TopChannel {
  channel_id: string;
  channel_name: string;
  video_count: number;
  total_views: number;
  avg_views: number;
}

// API 함수들 (캐싱 + 타임아웃)
export const api = {
  // 트렌딩
  getTrendingVideos: async (skipCache = false): Promise<TrendingResponse> => {
    const cacheKey = 'trending_videos';
    if (!skipCache) {
      const cached = getCached<TrendingResponse>(cacheKey);
      if (cached) return cached;
    }

    const response = await fetchWithTimeout(`${API_BASE_URL}/api/trending/current`);
    if (!response.ok) throw new Error('Failed to fetch trending videos');
    const data = await response.json();
    setCache(cacheKey, data);
    return data;
  },

  getRisingVideos: async (limit: number = 10, skipCache = false): Promise<VideoSnapshot[]> => {
    const cacheKey = `rising_videos_${limit}`;
    if (!skipCache) {
      const cached = getCached<VideoSnapshot[]>(cacheKey);
      if (cached) return cached;
    }

    const response = await fetchWithTimeout(`${API_BASE_URL}/api/trending/velocity?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch rising videos');
    const data = await response.json();
    setCache(cacheKey, data);
    return data;
  },

  // 카테고리
  getCategoryStats: async (skipCache = false): Promise<CategoryStats[]> => {
    const cacheKey = 'category_stats';
    if (!skipCache) {
      const cached = getCached<CategoryStats[]>(cacheKey);
      if (cached) return cached;
    }

    const response = await fetchWithTimeout(`${API_BASE_URL}/api/categories/stats`);
    if (!response.ok) throw new Error('Failed to fetch category stats');
    const data = await response.json();
    setCache(cacheKey, data);
    return data;
  },

  getCategoryDistribution: async (skipCache = false): Promise<Record<string, number>> => {
    const cacheKey = 'category_distribution';
    if (!skipCache) {
      const cached = getCached<Record<string, number>>(cacheKey);
      if (cached) return cached;
    }

    const response = await fetchWithTimeout(`${API_BASE_URL}/api/categories/distribution`);
    if (!response.ok) throw new Error('Failed to fetch category distribution');
    const data = await response.json();
    setCache(cacheKey, data);
    return data;
  },

  // 분석
  getOverviewStats: async (skipCache = false): Promise<OverviewStats> => {
    const cacheKey = 'overview_stats';
    if (!skipCache) {
      const cached = getCached<OverviewStats>(cacheKey);
      if (cached) return cached;
    }

    const response = await fetchWithTimeout(`${API_BASE_URL}/api/analytics/overview`);
    if (!response.ok) throw new Error('Failed to fetch overview stats');
    const data = await response.json();
    setCache(cacheKey, data);
    return data;
  },

  getTopChannels: async (limit: number = 6, skipCache = false): Promise<TopChannel[]> => {
    const cacheKey = `top_channels_${limit}`;
    if (!skipCache) {
      const cached = getCached<TopChannel[]>(cacheKey);
      if (cached) return cached;
    }

    const response = await fetchWithTimeout(`${API_BASE_URL}/api/analytics/top-channels?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to fetch top channels');
    const data = await response.json();
    setCache(cacheKey, data);
    return data;
  },

  getHourlyTrends: async (hours: number = 24, skipCache = false): Promise<any[]> => {
    const cacheKey = `hourly_trends_${hours}`;
    if (!skipCache) {
      const cached = getCached<any[]>(cacheKey);
      if (cached) return cached;
    }

    const response = await fetchWithTimeout(`${API_BASE_URL}/api/analytics/hourly-trends?hours=${hours}`);
    if (!response.ok) throw new Error('Failed to fetch hourly trends');
    const data = await response.json();
    setCache(cacheKey, data);
    return data;
  },

  // 헬스 체크
  healthCheck: async (): Promise<any> => {
    const response = await fetchWithTimeout(`${API_BASE_URL}/health`, 3000);
    if (!response.ok) throw new Error('Backend is not healthy');
    return response.json();
  },

  // 캐시 초기화
  clearCache: () => {
    cache.clear();
  },

  // AI Chat
  chat: {
    send: async (message: string, sessionId?: string): Promise<ChatResponse> => {
      const response = await fetch(`${API_BASE_URL}/api/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, session_id: sessionId }),
      });
      if (!response.ok) throw new Error('Failed to send chat message');
      return response.json();
    },

    clear: async (): Promise<void> => {
      const response = await fetch(`${API_BASE_URL}/api/chat/clear`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to clear chat history');
    },

    getViews: async (): Promise<ViewInfo[]> => {
      const response = await fetchWithTimeout(`${API_BASE_URL}/api/chat/views`);
      if (!response.ok) throw new Error('Failed to fetch views');
      return response.json();
    },

    getSuggestedQuestions: async (): Promise<SuggestedQuestions> => {
      const response = await fetchWithTimeout(`${API_BASE_URL}/api/chat/suggested-questions`);
      if (!response.ok) throw new Error('Failed to fetch suggested questions');
      return response.json();
    },

    healthCheck: async (): Promise<ChatHealthResponse> => {
      const response = await fetchWithTimeout(`${API_BASE_URL}/api/chat/health`, 5000);
      if (!response.ok) throw new Error('Chat service is not healthy');
      return response.json();
    },
  },
};

// Chat API 타입
export interface ChatResponse {
  response: string;
  tools_used: string[];
  session_id?: string;
  error?: string;
  response_type?: "table" | "list" | "stats" | "comparison" | "text" | "cards";
  structured_data?: {
    title?: string;
    columns?: string[];
    data?: any[];
    highlightField?: string;
  };
  // 능동적 제안
  suggested_questions?: string[];
  insights?: string[];
  related_analyses?: string[];
}

export interface ViewInfo {
  name: string;
  description: string;
  columns: string[];
}

export interface SuggestedQuestions {
  categories: {
    name: string;
    questions: string[];
  }[];
}

export interface ChatHealthResponse {
  status: string;
  ollama_connected: boolean;
  available_models?: string[];
  error?: string;
}

