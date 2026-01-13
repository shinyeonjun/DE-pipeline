"""
Step 2: View 선택 (View Selection)
질문 분석 결과를 바탕으로 데이터 조회에 필요한 View를 선택합니다.
Chain of Thought (Thinking) 및 재시도 로직을 적용하여 판단의 정확성을 높입니다.
"""
import json
from typing import List, Tuple, Dict, Any, Optional

from ..views import ViewType
from ..prompts import get_step2_prompt
from ..utils.llm import call_llm_with_retry
from ..utils.text import extract_json, extract_thinking


# ==========================================
# 상수 정의 (Constants)
# ==========================================

DEFAULT_LIMIT = 20
MIN_LIMIT = 1
MAX_LIMIT = 100
MAX_SELECTED_VIEWS = 3
VALID_VIEW_NAMES = {v.value for v in ViewType}


# ==========================================
# 헬퍼 함수 (Pure Functions)
# ==========================================

def coerce_limit(value: Any, fallback: int) -> int:
    """Limit 값을 정수로 변환하고 범위를 제한합니다."""
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = fallback
    
    if limit < MIN_LIMIT:
        return MIN_LIMIT
    if limit > MAX_LIMIT:
        return MAX_LIMIT
    return limit


def fallback_selection(
    user_message: str,
    question_analysis: Optional[Dict[str, Any]] = None,
    error_msg: str = ""
) -> Tuple[List[Tuple[str, int]], str]:
    """LLM 분석 실패 시 사용할 간단한 폴백 로직."""
    selected = []
    msg_lower = user_message.lower()

    # 간단한 휴리스틱
    if any(kw in msg_lower for kw in ["채널", "channel", "유튜버"]):
        selected.append("ai_channel_stats")
    if any(kw in msg_lower for kw in ["카테고리", "category", "분류"]):
        selected.append("ai_category_stats")
    if any(kw in msg_lower for kw in ["쇼츠", "shorts"]):
        selected.append("ai_content_type_analysis")

    # 기본값
    if not selected:
        selected.append("ai_current_trending")
    
    # 중복 제거
    unique = list(dict.fromkeys(selected))
    
    raw_limit = question_analysis.get("limit", DEFAULT_LIMIT) if question_analysis else DEFAULT_LIMIT
    limit = coerce_limit(raw_limit, DEFAULT_LIMIT)
    
    return [(v, limit) for v in unique[:MAX_SELECTED_VIEWS]], f"폴백 선택 (이유: {error_msg})"


def validate_view_selection_json(content: str) -> bool:
    """View 선택 응답이 유효한지 검증합니다."""
    try:
        json_str = extract_json(content)
        if not json_str:
            return False
            
        data = json.loads(json_str)
        # views 키가 있거나 리스트여야 함
        if isinstance(data, dict):
            return "views" in data
        return isinstance(data, list)
    except Exception:
        return False


# ==========================================
# 메인 함수 (Async Function)
# ==========================================

async def select_views(
    user_message: str,
    question_analysis: Optional[Dict[str, Any]],
    ollama_host: str,
    model: str
) -> Tuple[List[Tuple[str, int]], str]:
    """
    사용자 질문에 적합한 데이터 View 목록을 선택합니다.
    (AI Retry & Thinking 적용)
    """
    print(f"[Step2] View 선택 시작 (AI Retry & Thinking)...")

    analysis_json = json.dumps(question_analysis, ensure_ascii=False) if question_analysis else "{}"
    prompt = get_step2_prompt(user_message, analysis_json)

    messages = [
        {"role": "system", "content": "당신은 View 선택 전문가입니다. <thinking> 후 JSON을 출력하세요."},
        {"role": "user", "content": prompt}
    ]

    try:
        # 재시도 로직 호출
        content = await call_llm_with_retry(
            ollama_host,
            model,
            messages,
            validator=validate_view_selection_json,
            max_retries=2
        )

        # Thinking 추출
        thinking_log = extract_thinking(content) or "Thinking 없음"
        print(f"[Step2] Thinking: {thinking_log[:100]}...")

        # JSON 파싱
        json_str = extract_json(content)
        result = json.loads(json_str)
        
        # 결과 표준화
        if isinstance(result, dict):
            views_list = result.get("views", [])
        elif isinstance(result, list):
            views_list = result
        else:
            views_list = []

        # View 유효성 검증
        selected_views = []
        seen_views = set()
        fallback_limit = coerce_limit(
            question_analysis.get("limit", DEFAULT_LIMIT) if question_analysis else DEFAULT_LIMIT,
            DEFAULT_LIMIT
        )

        for v in views_list if isinstance(views_list, list) else []:
            if isinstance(v, str):
                view_name = v
                limit = fallback_limit
            elif isinstance(v, dict):
                view_name = v.get("name", "")
                limit = v.get("limit", fallback_limit)
            else:
                continue

            if view_name in VALID_VIEW_NAMES and view_name not in seen_views:
                limit = coerce_limit(limit, fallback_limit)
                selected_views.append((view_name, limit))
                seen_views.add(view_name)
            else:
                print(f"  [WARN] 잘못된 View 이름: {view_name}")

        # 선택된 View가 없으면 폴백
        if not selected_views:
            print("[Step2] 선택된 View 없음, 기본값 사용")
            return fallback_selection(user_message, question_analysis, "AI 미선택")

        if len(selected_views) > MAX_SELECTED_VIEWS:
            selected_views = selected_views[:MAX_SELECTED_VIEWS]

        print(f"[Step2] 최종 선택: {[v[0] for v in selected_views]}")
        return selected_views, thinking_log

    except Exception as e:
        print(f"[Step2] View 선택 최종 실패: {e}")
        return fallback_selection(user_message, question_analysis, str(e))
