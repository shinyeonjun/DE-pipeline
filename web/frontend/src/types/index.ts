// Chat types
export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  responseType?: "table" | "list" | "stats" | "comparison" | "text" | "cards" | "bar" | "pie" | "line" | "dashboard";
  structuredData?: {
    title?: string;
    columns?: string[];
    data?: any[];
    highlightField?: string;
    stats?: {
      total_views?: number;
      avg_engagement?: number;
      count?: number;
    };
    chart_type?: string;
    type?: string;
  };
  // 능동적 제안
  suggestedQuestions?: string[];
  insights?: string[];
  relatedAnalyses?: string[];
  thinking?: string;
}

// Video types
export interface VideoData {
  rank: number;
  title: string;
  channelName: string;
  thumbnailUrl: string;
  viewCount: number;
  likeCount: number;
  commentCount: number;
  category: string;
  isShorts: boolean;
  engagementRate: string;
  hoursAgo: number;
  velocity?: number;
}

