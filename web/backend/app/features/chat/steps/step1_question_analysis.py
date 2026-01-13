"""
Step 1: 질문 분석 (Question Analysis)
사용자 질문을 분석하여 의도(Intent), 엔티티(Entities), 필터(Filters), 정렬(Sort) 정보를 추출합니다.
Chain of Thought (Thinking) 및 재시도 로직을 적용하여 정확도를 높입니다.
"""
import json
from typing import Dict, Any
from ..prompts import get_step1_prompt
from ..utils.llm import call_llm_with_retry
from ..utils.text import extract_json, extract_thinking


# ==========================================
# 헬퍼 함수 (Pure Functions)
# ==========================================

def validate_analysis_json(content: str) -> bool:
    """LLM 응답이 유효한 JSON을 포함하고 필수 필드를 가지고 있는지 검증합니다."""
    try:
        json_str = extract_json(content)
        if not json_str:
            return False
            
        data = json.loads(json_str)
        # 필수 키 확인 (최소한 intent는 있어야 함)
        if "intent" not in data:
            return False
            
        return True
    except Exception:
        return False


def fallback_analyze(user_message: str, error_msg: str = "") -> Dict[str, Any]:
    """LLM 분석 실패 시 사용할 폴백 분석."""
    intent = "search"
    if any(kw in user_message.lower() for kw in ["안녕", "반가워", "누구", "소개"]):
        intent = "conversation"
    
    return {
        "intent": intent,
        "entities": {},
        "filters": [],
        "sort": {"field": "순위", "order": "asc"},
        "limit": 20,
        "required_views": ["ai_current_trending"],
        "thinking": f"폴백 분석 사용 (이유: {error_msg})"
    }


# ==========================================
# 메인 함수 (Async Function)
# ==========================================

async def analyze_question(
    user_message: str,
    ollama_host: str,
    model: str,
    view_schema: str = "",
    last_turn_summary: str = ""
) -> Dict[str, Any]:
    """
    사용자 질문을 분석하여 구조화된 정보를 반환합니다. (Unified Version)
    의도 분석, 엔티티 추출, View 선택을 한 번에 수행합니다.
    """
    print(f"[Step1] 통합 질문 분석 시작 (Zero-Latency): {user_message[:50]}...")

    from datetime import datetime
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 통합 프롬프트 사용
    from ..prompts import get_unified_analysis_prompt
    prompt = get_unified_analysis_prompt(user_message, view_schema, last_turn_summary)
    
    messages = [
        {"role": "system", "content": f"당신은 데이터 분석 전문가입니다. 현재 시각은 {current_time_str}입니다. <thinking> 후 JSON만 출력하세요."},
        {"role": "user", "content": prompt}
    ]

    try:
        content = await call_llm_with_retry(
            ollama_host,
            model,
            messages,
            validator=validate_analysis_json,
            max_retries=2
        )

        thinking_log = extract_thinking(content)
        json_str = extract_json(content)
        result = json.loads(json_str)

        # 기본값 및 후처리
        result.setdefault("intent", "search")
        result.setdefault("entities", {})
        result.setdefault("filters", [])
        result.setdefault("sort", {"field": "순위", "order": "asc"})
        result.setdefault("limit", 20)
        result.setdefault("required_views", [])
        result["thinking"] = thinking_log

        # [Logic] Entity -> Filter 보정
        entities = result.get("entities", {})
        filters = result.get("filters", [])
        
        if entities.get("category"):
            has_cat = any(f.get("field") == "카테고리" for f in filters)
            if not has_cat:
                filters.append({"field": "카테고리", "operator": "=", "value": entities["category"]})
        
        if entities.get("channel"):
            has_ch = any(f.get("field") == "채널명" for f in filters)
            if not has_ch:
                filters.append({"field": "채널명", "operator": "contains", "value": entities["channel"]})

        result["filters"] = filters

        print(f"[Step1] 통합 분석 완료: Intent={result.get('intent')}, Views={len(result.get('required_views', []))}")
        return result

    except Exception as e:
        print(f"[Step1] 통합 질문 분석 실패: {e}")
        return fallback_analyze(user_message, str(e))

