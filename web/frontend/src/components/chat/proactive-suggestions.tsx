"use client";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { 
  Lightbulb, 
  TrendingUp, 
  BarChart3, 
  Sparkles,
  ChevronRight,
  ArrowRight
} from "lucide-react";

interface ProactiveSuggestionsProps {
  suggestedQuestions?: string[];
  insights?: string[];
  relatedAnalyses?: string[];
  dataPatterns?: string[];
  onQuestionClick?: (question: string) => void;
}

export function ProactiveSuggestions({
  suggestedQuestions = [],
  insights = [],
  relatedAnalyses = [],
  dataPatterns = [],
  onQuestionClick
}: ProactiveSuggestionsProps) {
  const hasAnySuggestions = 
    suggestedQuestions.length > 0 ||
    insights.length > 0 ||
    relatedAnalyses.length > 0 ||
    dataPatterns.length > 0;

  if (!hasAnySuggestions) {
    return null;
  }

  return (
    <div className="mt-6 space-y-4">
      {/* 데이터 인사이트 */}
      {insights.length > 0 && (
        <Card className="bg-gradient-to-br from-amber-500/10 to-orange-500/10 border-amber-500/20 p-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-amber-500/20 flex items-center justify-center flex-shrink-0">
              <Lightbulb className="h-4 w-4 text-amber-400" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-amber-300 mb-2">💡 데이터 인사이트</h4>
              <ul className="space-y-1.5">
                {insights.map((insight, idx) => (
                  <li key={idx} className="text-sm text-zinc-300 flex items-start gap-2">
                    <span className="text-amber-400 mt-1">•</span>
                    <span>{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      )}

      {/* 데이터 패턴 */}
      {dataPatterns.length > 0 && (
        <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-purple-500/20 p-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center flex-shrink-0">
              <TrendingUp className="h-4 w-4 text-purple-400" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-purple-300 mb-2">📊 발견된 패턴</h4>
              <ul className="space-y-1.5">
                {dataPatterns.map((pattern, idx) => (
                  <li key={idx} className="text-sm text-zinc-300 flex items-start gap-2">
                    <span className="text-purple-400 mt-1">•</span>
                    <span>{pattern}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      )}

      {/* 관련 분석 제안 */}
      {relatedAnalyses.length > 0 && (
        <Card className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border-blue-500/20 p-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center flex-shrink-0">
              <BarChart3 className="h-4 w-4 text-blue-400" />
            </div>
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-blue-300 mb-2">🔍 관련 분석 제안</h4>
              <ul className="space-y-1.5">
                {relatedAnalyses.map((analysis, idx) => (
                  <li key={idx} className="text-sm text-zinc-300 flex items-start gap-2">
                    <span className="text-blue-400 mt-1">•</span>
                    <span>{analysis}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      )}

      {/* 추가 질문 제안 */}
      {suggestedQuestions.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="h-4 w-4 text-red-400" />
            <h4 className="text-sm font-semibold text-zinc-300">다음 질문 제안</h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {suggestedQuestions.map((question, idx) => (
              <Button
                key={idx}
                variant="outline"
                size="sm"
                className="bg-zinc-900/50 border-zinc-700/50 text-zinc-300 hover:bg-zinc-800 hover:text-white hover:border-red-500/50 transition-all text-xs h-auto py-2 px-3"
                onClick={() => onQuestionClick?.(question)}
              >
                <span className="mr-1.5">💬</span>
                {question}
                <ChevronRight className="h-3 w-3 ml-1.5 opacity-50" />
              </Button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

