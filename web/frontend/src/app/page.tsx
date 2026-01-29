"use client";

import { useEffect, useRef, useState } from "react";
import { ChatInput } from "@/components/chat/chat-input";
import { ChatMessage, ChatLoadingMessage, type LoadingStep } from "@/components/chat/chat-message";
// import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  BarChart3,
  ChevronRight,
  ChevronLeft,
  TrendingUp,
  Users,
  Eye,
  ThumbsUp,
  MessageSquare,
  Clock
} from "lucide-react";
import { api, type OverviewStats } from "@/lib/api";
import type { Message } from "@/types";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState<LoadingStep>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Right Sidebar State
  const [showRightSidebar, setShowRightSidebar] = useState(true);
  const [stats, setStats] = useState<OverviewStats | null>(null);

  // Fetch Stats
  useEffect(() => {
    const loadStats = async () => {
      try {
        const data = await api.getOverviewStats();
        setStats(data);
      } catch (error) {
        console.error("Failed to load stats:", error);
      }
    };
    loadStats();
  }, []);

  useEffect(() => {
    // Scroll to bottom on new message
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  useEffect(() => {
    // Handle suggestion selection
    const handleSuggestion = (e: CustomEvent<string>) => {
      handleSend(e.detail);
    };

    window.addEventListener("suggestionSelected", handleSuggestion as EventListener);
    return () => {
      window.removeEventListener("suggestionSelected", handleSuggestion as EventListener);
    };
  }, []);

  const handleSend = async (text: string) => {
    if (!text.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // 로딩 단계 시뮬레이션
    setLoadingStep("routing");
    const stepTimer1 = setTimeout(() => setLoadingStep("analyzing"), 800);
    const stepTimer2 = setTimeout(() => setLoadingStep("searching"), 1600);
    const stepTimer3 = setTimeout(() => setLoadingStep("generating"), 2400);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
          session_id: "default-session", // You might want to manage session IDs
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to send message");
      }

      const data = await response.json();

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
        responseType: data.response_type,
        structuredData: data.structured_data,
        suggestedQuestions: data.suggested_questions,
        insights: data.insights,
        relatedAnalyses: data.related_analyses,
        thinking: data.thinking,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Chat error:", error);

      // 에러 유형에 따른 친화적 메시지
      let errorContent = "😅 앗, 문제가 생겼어요!\n\n";

      if (error instanceof TypeError && error.message.includes("fetch")) {
        errorContent += "🔌 **서버 연결 실패**\n서버가 꺼져있거나 네트워크 문제인 것 같아요.\n\n_백엔드 서버를 확인해주세요!_";
      } else if (error instanceof Error && error.message.includes("timeout")) {
        errorContent += "⏱️ **응답 시간 초과**\n처리 시간이 너무 오래 걸렸어요.\n\n_잠시 후 다시 시도해주세요!_";
      } else {
        errorContent += "🔧 **일시적인 오류**\n잠시 후 다시 시도해주세요!\n\n_계속 문제가 발생하면 새로고침 해보세요._";
      }

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: errorContent,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      // 타이머 정리
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      clearTimeout(stepTimer3);
      setLoadingStep(null);
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-full bg-zinc-950 text-white overflow-hidden">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col relative h-full">
        {/* Header */}
        <div className="absolute top-0 w-full z-10 p-4 pl-6 flex justify-between items-center bg-zinc-950/80 backdrop-blur-md border-b border-zinc-800/50">
          <div>
            <h1 className="text-lg font-bold bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">
              YouTube Analytics AI
            </h1>
            <p className="text-zinc-500 text-xs mt-0.5">
              데이터 기반 트렌딩 인사이트
            </p>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowRightSidebar(!showRightSidebar)}
            className="text-zinc-400 hover:text-white"
          >
            {showRightSidebar ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
          </Button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto pt-20 scroll-smooth" ref={scrollRef}>
          <div className="max-w-3xl mx-auto px-4 py-8 space-y-8 min-h-full">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6 animate-in fade-in zoom-in duration-500">
                <div className="space-y-3">
                  <h3 className="text-2xl font-bold text-white">
                    무엇을 분석해드릴까요?
                  </h3>
                  <p className="text-zinc-400 max-w-md mx-auto leading-relaxed">
                    "현재 트렌딩 1위는?", "게임 카테고리 분석해줘" 등<br />
                    데이터가 필요한 모든 것을 질문하세요.
                  </p>
                </div>
              </div>
            )}

            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}

            {isLoading && <ChatLoadingMessage step={loadingStep} />}
          </div>
        </div>

        {/* Input */}
        <div className="w-full bg-zinc-950 pb-6 pt-2 border-t border-zinc-800/50">
          <div className="max-w-3xl mx-auto px-4 space-y-3">
            <ChatInput
              value={input}
              onChange={setInput}
              onSend={() => handleSend(input)}
              disabled={isLoading}
            />
            <p className="text-[10px] text-zinc-600 text-center">
              AI는 실시간 데이터를 기반으로 답변하지만, 일부 오차가 있을 수 있습니다.
            </p>
          </div>
        </div>
      </div>

      {/* Right Sidebar - Stats */}
      <div
        className={`
                    border-l border-zinc-800/30 bg-zinc-950/50 transition-all duration-300 ease-in-out flex flex-col
                    ${showRightSidebar ? "w-80 opacity-100 translate-x-0" : "w-0 opacity-0 translate-x-full overflow-hidden"}
                `}
      >
        <div className="p-6 border-b border-zinc-800/30">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-red-500" />
            실시간 현황
          </h3>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {stats ? (
            <>
              <Card className="p-4 bg-zinc-900/50 border-zinc-800/50">
                <p className="text-xs text-zinc-500 mb-1">수집된 동영상</p>
                <div className="flex items-end justify-between">
                  <span className="text-2xl font-bold text-white">{stats.total_videos.toLocaleString()}</span>
                  <TrendingUp className="h-4 w-4 text-emerald-500 mb-1" />
                </div>
              </Card>

              <div className="grid grid-cols-2 gap-3">
                <Card className="p-3 bg-zinc-900/50 border-zinc-800/50">
                  <div className="flex items-center gap-2 mb-2">
                    <Eye className="h-3.5 w-3.5 text-blue-400" />
                    <span className="text-xs text-zinc-400">총 조회수</span>
                  </div>
                  <p className="text-sm font-semibold text-white">
                    {(stats.total_views / 1000000).toFixed(1)}M
                  </p>
                </Card>
                <Card className="p-3 bg-zinc-900/50 border-zinc-800/50">
                  <div className="flex items-center gap-2 mb-2">
                    <ThumbsUp className="h-3.5 w-3.5 text-red-400" />
                    <span className="text-xs text-zinc-400">좋아요</span>
                  </div>
                  <p className="text-sm font-semibold text-white">
                    {(stats.total_likes / 1000).toFixed(1)}K
                  </p>
                </Card>
              </div>

              <Card className="p-4 bg-zinc-900/50 border-zinc-800/50">
                <h4 className="text-xs font-medium text-zinc-400 mb-3">형식 분포</h4>
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-white">Shorts</span>
                      <span className="text-red-400">{stats.shorts_ratio}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-red-500 rounded-full"
                        style={{ width: `${stats.shorts_ratio}%` }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-white">General Video</span>
                      <span className="text-zinc-400">{100 - stats.shorts_ratio}%</span>
                    </div>
                    <div className="h-1.5 w-full bg-zinc-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-zinc-600 rounded-full"
                        style={{ width: `${100 - stats.shorts_ratio}%` }}
                      />
                    </div>
                  </div>
                </div>
              </Card>

              <div className="pt-4 border-t border-zinc-800/30">
                <div className="flex items-center justify-between text-xs text-zinc-500">
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    마지막 업데이트
                  </span>
                  <span>
                    {new Date(stats.snapshot_at).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center py-10 space-y-3 text-zinc-500">
              <div className="w-8 h-8 border-2 border-zinc-700 border-t-red-500 rounded-full animate-spin" />
              <p className="text-xs">데이터 로딩 중...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
