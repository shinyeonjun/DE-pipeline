"""
Step 0: Query Router
사용자 질문을 분류하여 데이터 분석(SQL) 경로 또는 지식 검색(RAG) 경로로 라우팅합니다.
LLM 기반 동적 분류 - 하드코딩 없음
"""
from typing import Literal, Dict, Any
from ..utils.llm import call_llm

# 라우팅 결과 타입
RouteType = Literal["data", "knowledge"]


async def route_query(
    question: str,
    ollama_host: str,
    model: str
) -> Dict[str, Any]:
    """
    LLM을 사용하여 질문을 분석하고 적절한 처리 경로를 결정합니다.
    
    Args:
        question: 사용자 질문
        ollama_host: Ollama 호스트 URL
        model: 모델명
        
    Returns:
        {
            "route": "data" | "knowledge",
            "confidence": float,
            "thinking": str
        }
    """
    print(f"[Step0] Query Router 시작: {question[:50]}...")
    
    # LLM 기반 분류 (하드코딩 없이 AI가 판단)
    system_prompt = """당신은 질문 분류 전문가입니다.
사용자 질문을 분석하여 두 가지 유형 중 하나로 분류하세요.

## DATA (데이터 분석 질문)
실시간 데이터 조회가 필요한 질문:
- 순위, 랭킹, TOP N 조회
- 통계, 수치, 비교 분석
- 특정 채널/카테고리/기간 필터링
- 현재 트렌딩, 오늘/어제 데이터

## KNOWLEDGE (지식/개념 질문)
사전 지식으로 답할 수 있는 질문:
- 개념, 용어, 정의 설명
- 방법론, 전략, 팁, 가이드
- "왜", "어떻게", "무엇" 유형 질문
- 알고리즘 원리, 플랫폼 사용법

## 출력 규칙
반드시 아래 형식으로만 출력하세요:
ROUTE: DATA 또는 ROUTE: KNOWLEDGE
다른 설명 없이 위 형식만 출력하세요."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    
    try:
        response = await call_llm(ollama_host, model, messages, temperature=0.1, num_predict=20)
        answer = response.get("message", {}).get("content", "").strip().upper()
        
        # 응답에서 라우팅 결과 추출
        if "KNOWLEDGE" in answer:
            route = "knowledge"
        else:
            route = "data"  # 기본값은 데이터 (안전한 방향)
        
        print(f"[Step0] LLM 분류 결과: {route}")
        return {
            "route": route,
            "confidence": 0.85,
            "thinking": f"LLM 동적 분류: {route}"
        }
        
    except Exception as e:
        print(f"[Step0] LLM 호출 실패, 기본값(data) 사용: {e}")
        return {
            "route": "data",
            "confidence": 0.5,
            "thinking": f"분류 실패, 기본값 data 사용: {str(e)}"
        }

