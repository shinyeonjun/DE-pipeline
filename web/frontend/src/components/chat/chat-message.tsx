import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Bot, User } from "lucide-react";
import type { Message } from "@/types";
import { ResponseCharts } from "./response-charts";
import { ResponseTable } from "./response-table";
import { ProactiveSuggestions } from "./proactive-suggestions";
import ReactMarkdown from "react-markdown";


interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  return (
    <div
      className={`flex gap-4 ${message.role === "user" ? "flex-row-reverse" : ""
        }`}
    >
      <Avatar className="h-10 w-10 flex-shrink-0">
        <AvatarFallback
          className={
            message.role === "assistant"
              ? "bg-red-500 text-white"
              : "bg-zinc-700 text-white"
          }
        >
          {message.role === "assistant" ? (
            <Bot className="h-5 w-5" />
          ) : (
            <User className="h-5 w-5" />
          )}
        </AvatarFallback>
      </Avatar>

      <div
        className={`flex-1 ${message.role === "user" ? "text-right" : ""
          }`}
      >
        <div
          className={`inline-block p-4 rounded-2xl max-w-[80%] ${message.role === "assistant"
              ? "bg-zinc-800 text-white rounded-tl-none"
              : "bg-red-500 text-white rounded-tr-none"
            }`}
        >
          {message.role === "assistant" ? (
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown
                components={{
                  // 헤딩 스타일
                  h1: ({ children }) => <h1 className="text-xl font-bold mt-4 mb-2">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-lg font-semibold mt-3 mb-2">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-base font-medium mt-2 mb-1">{children}</h3>,
                  // 리스트 스타일
                  ul: ({ children }) => <ul className="list-disc list-inside my-2 space-y-1">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal list-inside my-2 space-y-1">{children}</ol>,
                  li: ({ children }) => <li className="text-sm">{children}</li>,
                  // 강조 스타일
                  strong: ({ children }) => <strong className="font-bold text-red-400">{children}</strong>,
                  em: ({ children }) => <em className="italic text-zinc-300">{children}</em>,
                  // 코드 스타일
                  code: ({ children }) => <code className="bg-zinc-700 px-1 py-0.5 rounded text-xs">{children}</code>,
                  // 링크 스타일
                  a: ({ href, children }) => <a href={href} className="text-red-400 underline" target="_blank">{children}</a>,
                  // 단락 스타일
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}
        </div>
        <p className="text-xs text-zinc-500 mt-2">
          {message.timestamp.toLocaleTimeString("ko-KR", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>

        {/* Structured Data rendering */}
        {message.structuredData && (
          <div className="mt-4">
            {/* Chart rendering */}
            {(message.responseType === "bar" ||
              message.responseType === "pie" ||
              message.responseType === "line" ||
              message.responseType === "comparison" ||
              message.responseType === "dashboard") && (
                <ResponseCharts structuredData={message.structuredData} />
              )}

            {/* Table rendering (default fallback or specific type) */}
            {(message.responseType === "table" || message.responseType === "list") && message.structuredData && (
              <ResponseTable
                title={message.structuredData.title || ""}
                data={message.structuredData.data || []}
                stats={message.structuredData.stats}
              />
            )}
          </div>
        )}

        {/* Proactive Suggestions */}
        {message.suggestedQuestions && message.suggestedQuestions.length > 0 && (
          <ProactiveSuggestions
            suggestedQuestions={message.suggestedQuestions}
            insights={message.insights}
            relatedAnalyses={message.relatedAnalyses}
            onQuestionClick={(question) => {
              // This needs to be handled by parent, but for now we'll just show them
              const event = new CustomEvent("suggestionSelected", { detail: question });
              window.dispatchEvent(event);
            }}
          />
        )}
      </div>

    </div >
  );
}

// 로딩 상태 타입
export type LoadingStep =
  | "routing"      // 질문 분류 중
  | "analyzing"    // 질문 분석 중
  | "searching"    // 데이터 검색 중
  | "generating"   // 답변 생성 중
  | null;

const LOADING_MESSAGES: Record<NonNullable<LoadingStep>, string> = {
  routing: "질문 유형 분석 중...",
  analyzing: "질문 분석 중...",
  searching: "데이터 검색 중...",
  generating: "답변 생성 중...",
};

interface ChatLoadingMessageProps {
  step?: LoadingStep;
}

export function ChatLoadingMessage({ step }: ChatLoadingMessageProps) {
  const message = step ? LOADING_MESSAGES[step] : "생각 중...";

  return (
    <div className="flex gap-4">
      <Avatar className="h-10 w-10">
        <AvatarFallback className="bg-red-500 text-white">
          <Bot className="h-5 w-5" />
        </AvatarFallback>
      </Avatar>
      <div className="bg-zinc-800 p-4 rounded-2xl rounded-tl-none">
        <div className="flex items-center gap-3">
          {/* 로딩 애니메이션 */}
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-red-500 rounded-full animate-bounce" />
            <span
              className="w-2 h-2 bg-red-500 rounded-full animate-bounce"
              style={{ animationDelay: "0.1s" }}
            />
            <span
              className="w-2 h-2 bg-red-500 rounded-full animate-bounce"
              style={{ animationDelay: "0.2s" }}
            />
          </div>
          {/* 단계 메시지 */}
          <span className="text-sm text-zinc-400">{message}</span>
        </div>
      </div>
    </div>
  );
}


