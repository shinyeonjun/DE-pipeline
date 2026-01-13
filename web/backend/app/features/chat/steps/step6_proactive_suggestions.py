"""
Step 6: 능동적 제안 생성 (Proactive Suggestions)
사용자의 질문과 답변을 바탕으로, 다음에 물어볼 만한 후속 질문이나 추가 분석을 제안합니다.
하드코딩된 제안 목록을 제거하고 LLM의 창의성에 기반하여 동적으로 생성합니다.
"""
import json
from typing import Dict, Any, List
from ..prompts import STEP6_SUGGESTION_PROMPT
from ..utils.llm import call_llm
from ..utils.text import extract_json

# ==========================================
# 헬퍼 함수 (Pure Functions)
# ==========================================

def fallback_suggestions() -> Dict[str, Any]:
    """
    LLM 호출 실패 시 사용할 최소한의 기본 제안.
    """
    return {
        "suggested_questions": [
            "현재 인기 동영상 TOP 10은?",
            "가장 성과가 좋은 채널은?",
            "카테고리별 현황 알려줘"
        ],
        "insights": [],
        "related_analyses": [
            "트렌딩 동영상 심층 분석",
            "카테고리별 비교 분석"
        ]
    }


# ==========================================
# 메인 함수 (Async Function)
# ==========================================

async def generate_suggestions(
    user_message: str,
    ai_response: str,
    all_data: Dict[str, Any],
    question_analysis: Dict[str, Any],
    ollama_host: str,
    model: str
) -> Dict[str, Any]:
    """
    사용자에게 유용한 후속 질문과 인사이트를 제안합니다.

    Args:
        user_message: 사용자 질문
        ai_response: AI 답변 내용
        all_data: 조회된 데이터
        question_analysis: Step 1 분석 결과
        ollama_host: Ollama 호스트 URL
        model: 모델명

    Returns:
        Dict: {suggested_questions, insights, related_analyses}
    """
    print(f"[Step6] 능동적 제안 생성 시작 (AI Driven)...")

    try:
        # 조회된 View 목록
        views_used = ", ".join(all_data.keys()) if all_data else "없음"

        # 응답 요약 (토큰 제한 고려)
        response_summary = ai_response[:300] + "..." if len(ai_response) > 300 else ai_response

        # 프롬프트 생성
        prompt = STEP6_SUGGESTION_PROMPT.format(
            question=user_message,
            response_summary=response_summary,
            views_used=views_used
        )

        messages = [
            {"role": "system", "content": "당신은 데이터 분석 제안 전문가입니다. JSON만 출력하세요."},
            {"role": "user", "content": prompt}
        ]

        # LLM 호출
        response = await call_llm(ollama_host, model, messages, temperature=0.5, num_predict=512)
        content = response.get("message", {}).get("content", "")

        # JSON 파싱
        json_str = extract_json(content)
        result = json.loads(json_str)

        # 결과 구성
        suggestions = {
            "suggested_questions": result.get("suggested_questions", [])[:5],
            "insights": result.get("insights", [])[:3],
            "related_analyses": result.get("related_analyses", [])[:3]
        }

        # 결과가 너무 비어있으면 폴백 사용
        if not suggestions["suggested_questions"]:
            print("[Step6] LLM 결과가 비어있어 폴백 제안 추가")
            fallback = fallback_suggestions()
            suggestions["suggested_questions"] = fallback["suggested_questions"]
            if not suggestions["related_analyses"]:
                suggestions["related_analyses"] = fallback["related_analyses"]

        print(f"[Step6] 제안 생성 완료: 질문 {len(suggestions['suggested_questions'])}개")
        return suggestions

    except Exception as e:
        print(f"[Step6] 제안 생성 실패: {e}, 기본 제안 사용")
        return fallback_suggestions()
