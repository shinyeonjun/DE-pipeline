"use client";

import { useEffect, useRef, useState } from "react";
import { ChatInput } from "@/components/chat/chat-input";
import { ChatMessage, ChatLoadingMessage, type LoadingStep } from "@/components/chat/chat-message";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { Message } from "@/types";

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [loadingStep, setLoadingStep] = useState<LoadingStep>(null);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        // Scroll to bottom on new message
        if (scrollRef.current) {
            const scrollArea = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
            if (scrollArea) {
                scrollArea.scrollTop = scrollArea.scrollHeight;
            }
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
        <div className="flex flex-col h-screen bg-zinc-950 text-white p-4 md:p-6 lg:p-8">
            <div className="max-w-4xl mx-auto w-full flex flex-col h-full bg-zinc-900/50 rounded-xl border border-zinc-800 overflow-hidden shadow-2xl backdrop-blur-sm">
                {/* Header */}
                <div className="p-4 border-b border-zinc-800 bg-zinc-900/80">
                    <h1 className="text-xl font-bold bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">
                        YouTube Analytics AI
                    </h1>
                    <p className="text-zinc-400 text-sm">
                        데이터 기반으로 트렌딩 인사이트를 질문해보세요
                    </p>
                </div>

                {/* Messages */}
                <ScrollArea className="flex-1 p-4" ref={scrollRef}>
                    <div className="space-y-6">
                        {messages.length === 0 && (
                            <div className="flex flex-col items-center justify-center h-[50vh] text-center space-y-4">
                                <div className="p-4 bg-zinc-800/50 rounded-full">
                                    <span className="text-4xl">🤖</span>
                                </div>
                                <h3 className="text-lg font-medium text-zinc-200">
                                    무엇을 분석해드릴까요?
                                </h3>
                                <p className="text-zinc-500 max-w-md">
                                    "현재 트렌딩 1위는?", "게임 카테고리 분석해줘", "쇼츠와 일반 영상 비교" 등 궁금한 점을 물어보세요.
                                </p>
                            </div>
                        )}

                        {messages.map((message) => (
                            <ChatMessage key={message.id} message={message} />
                        ))}

                        {isLoading && <ChatLoadingMessage step={loadingStep} />}
                    </div>
                </ScrollArea>

                {/* Input */}
                <div className="p-4 bg-zinc-900/80 border-t border-zinc-800">
                    <ChatInput
                        value={input}
                        onChange={setInput}
                        onSend={() => handleSend(input)}
                        disabled={isLoading}
                    />
                    <p className="text-xs text-zinc-600 mt-2 text-center">
                        AI는 데이터를 기반으로 답변하지만, 실시간성에 따라 오차가 있을 수 있습니다.
                    </p>
                </div>
            </div>
        </div>
    );
}
