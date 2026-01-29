"""
Step 5: 답변 생성 (Response Generation)
질문을 정확히 이해하고, 데이터를 바탕으로 논리적이고 사실에 입각한 답변을 생성합니다.
Structured Data를 함께 생성하여 프론트엔드에서 리치한 UI를 렌더링할 수 있도록 지원합니다.
"""
import json
import traceback
from typing import Dict, Any, List, Optional, Union
from ..views import ViewType, VIEW_CATALOG
from ..utils.llm import call_llm


# ==========================================
# 헬퍼 함수 (Pure Functions)
# ==========================================

def format_number(num: Any) -> str:
    """숫자를 읽기 쉬운 문자열(K, M 접미사 등)로 변환합니다."""
    try:
        if num is None:
            return "-"
        if isinstance(num, (int, float)):
            if num >= 1000000:
                return f"{num/1000000:.1f}M"
            if num >= 1000:
                return f"{num/1000:.1f}K"
            return f"{int(num):,}"
        return str(num)
    except Exception:
        return str(num)


def strip_markdown_tables(text: str) -> str:
    """텍스트에서 마크다운 테이블을 제거합니다."""
    lines = text.splitlines()
    cleaned = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # 테이블 헤더 및 구분선 감지
        if line.startswith("|") and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line.startswith("|") and set(next_line) <= set("|:- "):
                i += 2
                while i < len(lines) and lines[i].strip().startswith("|"):
                    i += 1
                continue
        cleaned.append(lines[i])
        i += 1
    return "\n".join(cleaned).strip()


def prepare_data_context(all_data: Dict[str, Any]) -> str:
    """LLM 프롬프트에 제공할 데이터 컨텍스트를 구성합니다."""
    context_parts = []

    for view_name, view_data in all_data.items():
        data_list = view_data.get("data", [])
        if not data_list:
            continue

        filters_applied = view_data.get("filters_applied", [])

        # View 설명 가져오기
        view_desc = view_name
        for vt in ViewType:
            if vt.value == view_name:
                info = VIEW_CATALOG.get(vt)
                if info:
                    view_desc = info.description
                break

        # 필터 정보
        filter_info = ""
        if filters_applied:
            filter_strs = [f"{f['field']}={f['value']}" for f in filters_applied if f.get('field') and f.get('value')]
            if filter_strs:
                filter_info = f" [필터: {', '.join(filter_strs)}]"

        # 데이터 샘플링 (최대 20개)
        sample_data = data_list[:20]

        # 메타데이터 (Fallback 여부 등)
        meta = view_data.get("_meta", {})
        fallback_warning = ""
        if meta.get("fallback_applied"):
             fallback_warning = f"\n> [시스템 경고] 사용자가 요청한 필터 조건({meta.get('original_filters')})에 해당하는 데이터가 없어서, 전체 데이터(GLOBAL)를 대신 보여줍니다. 반드시 답변에서 이 사실을 언급하고 전체 기준으로 설명하세요.\n"

        context_parts.append(f"""{fallback_warning}
### {view_name}{filter_info}
설명: {view_desc}
총 {len(data_list)}개 데이터

**실제 데이터:**
```json
{json.dumps(sample_data, ensure_ascii=False, indent=2, default=str)}
```
""")

    return "\n".join(context_parts)


def detect_chart_type(view_name: str, columns: List[str], data: List[Dict[str, Any]]) -> str:
    """데이터 특성을 기반으로 최적의 차트 타입을 결정합니다."""
    if not data:
        return "text"
    
    col_str = " ".join(columns).lower()
    view_str = view_name.lower()
    
    # 1. 시계열/추세 데이터 (Line Chart)
    # 컬럼: 시간, 날짜, 성장률, 추이
    if any(k in col_str for k in ["시간", "날짜", "growth", "trend", "date", "time", "hour"]):
        return "line"
    if "growth" in view_str or "trend" in view_str or "hourly" in view_str:
        return "line"
        
    # 2. 비중/분포 데이터 (Pie Chart)
    # 컬럼: 비율, 점유율, 퍼센트 / 데이터 개수가 적을 때
    if len(data) <= 12 and any(k in col_str for k in ["비율", "점유율", "share", "percent", "ratio"]):
        return "pie"
    if "category" in view_str and "stats" in view_str: # 카테고리 통계는 파이가 국룰
        return "pie"
        
    # 3. 비교 데이터 (Comparison/Bar)
    # 비교, vs, 콘텐츠 유형 등 작은 그룹 간 비교
    if len(data) <= 10 and ("vs" in view_str or "comparison" in view_str or "type" in view_str):
        return "comparison"
        
    # 4. 랭킹/순위/통계 데이터 (Bar Chart)
    # 기본적으로 범주형 + 수치형 데이터는 Bar
    if len(data) <= 25:
        return "bar"
        
    # 데이터가 너무 많거나 복잡하면 테이블
    return "table"


def standardize_chart_data(data: List[Dict[str, Any]], chart_type: str) -> Dict[str, Any]:
    """
    프론트엔드가 '알아서' 그릴 수 있도록 데이터를 표준화합니다.
    Deep Insight Engine이 발견한 중요 지표들을 우선적으로 매핑합니다.
    """
    if not data:
        return {"data": [], "columns": []}
        
    sample = data[0]
    columns = list(sample.keys())
    
    # [Name 컬럼 찾기] 문자열이면서 고유값이 많은 것
    name_col = None
    priority_name_keywords = ["제목", "채널", "카테고리", "날짜", "시간", "type", "name"]
    for kw in priority_name_keywords:
        for key in columns:
            if kw in key and isinstance(sample[key], str):
                name_col = key
                break
        if name_col: break
    
    if not name_col:
        for key in columns:
            if isinstance(sample[key], str):
                name_col = key
                break
                
    # [Value 컬럼 찾기] 수치형 지표들 탐색
    value_map = {} # 실제 필드명 -> 프론트엔드 표준 필드명 매핑
    keywords = ["조회수", "구독자", "참여율", "성장률", "좋아요", "댓글", "영상수", "count", "views", "subs", "rate"]
    
    found_metrics = []
    for key in columns:
        if any(kw in key for kw in keywords) and isinstance(sample[key], (int, float)):
             if "순위" not in key and "id" not in key:
                 found_metrics.append(key)
    
    # 우선순위 정렬 및 상위 3개 선택
    found_metrics.sort(key=lambda x: next((i for i, kw in enumerate(keywords) if kw in x), 99))
    main_metrics = found_metrics[:3]

    # 데이터 매핑
    standardized = []
    stats_total = 0
    
    for item in data:
        new_item = item.copy()
        new_item["name"] = str(item.get(name_col, "Unknown"))
        
        # 메인 지표 매핑 (프론트엔드 호환용 'value' 키 유지)
        if main_metrics:
            main_val = item.get(main_metrics[0], 0)
            new_item["value"] = main_val if main_val is not None else 0
            
            # 추가 지표 매핑 (Comparison 차트 등에서 사용)
            for i, metric in enumerate(main_metrics):
                val = item.get(metric, 0)
                new_item[metric] = val if val is not None else 0
        
        standardized.append(new_item)
        if main_metrics:
            val = item.get(main_metrics[0], 0)
            if isinstance(val, (int, float)):
                stats_total += val
            
    return {
        "data": standardized,
        "columns": columns,
        "main_metric": main_metrics[0] if main_metrics else None,
        "additional_metrics": main_metrics[1:] if len(main_metrics) > 1 else [],
        "label_col": name_col,
        "stats": {
            "total": stats_total,
            "count": len(data)
        }
    }


def build_structured_data(
    all_data: Dict[str, Any],
    question_analysis: Optional[Dict[str, Any]] = None
) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
    """
    동적 시각화 데이터를 생성합니다. (Dashboard 지원)
    """
    # 가장 데이터가 많은(혹은 중요한) View 하나를 선택해서 시각화
    target_view = None
    max_count = -1
    
    for name, info in all_data.items():
        if info.get("count", 0) > max_count and info.get("data"):
            max_count = info.get("count", 0)
            target_view = name
            
    if not target_view:
        return None
        
    view_info = all_data[target_view]
    raw_data = view_info.get("data", [])
    
    if not raw_data:
        return None
        
    # 1. 차트 타입 결정
    columns = list(raw_data[0].keys())
    
    # 뷰 이름 보정 (renamed)
    display_view_name = target_view
    if target_view == "ai_hourly_pattern":
        display_view_name = "ai_hourly_trends" # 프론트엔드 호환용 (필요시)
        
    chart_type = detect_chart_type(target_view, columns, raw_data)
    
    # 2. Comparison(비교) 타입인 경우 -> 대시보드 모드 (여러 차트 생성)
    # 예: 쇼츠 vs 일반 -> 개수(파이), 조회수(바), 참여율(바) 3개 생성
    # 2. 딥 인사이트 기반 대시보드 모드 (2개 이상의 지표가 중요할 때)
    processed = standardize_chart_data(raw_data, chart_type)
    
    if processed["additional_metrics"] and chart_type in ["bar", "line"]:
        # 여러 지표가 있으면 'comparison' 타입으로 승격
        chart_type = "comparison"
        
    # 비교 차트인 경우 타이틀 보정
    title = target_view
    for vt in VIEW_CATALOG.values():
        if vt.name == target_view:
            title = vt.description.split("(")[0].strip()
            break
            
    filters = view_info.get("filters_applied", [])
    if filters:
         filter_strs = [f"{f.get('value')}" for f in filters if f.get('value')]
         if filter_strs: title += f" ({', '.join(filter_strs)})"

    return {
        "type": chart_type,
        "chart_type": chart_type,
        "title": title,
        "columns": processed["columns"],
        "data": processed["data"],
        "stats": processed["stats"],
        "meta": {
             "x_label": processed["label_col"],
             "y_label": processed["main_metric"],
             "metrics": [processed["main_metric"]] + processed["additional_metrics"]
        }
    }
    



def generate_data_summary(all_data: Dict[str, Any], question: str) -> str:
    """폴백용 간단 데이터 요약 텍스트를 생성합니다."""
    lines = [f"'{question}'에 대한 조회 결과입니다:\n"]

    for view_name, view_data in all_data.items():
        data_list = view_data.get("data", [])
        filters = view_data.get("filters_applied", [])

        if not data_list:
            continue

        filter_info = ""
        if filters:
            filter_strs = [f"{f['field']}={f['value']}" for f in filters if f.get('field')]
            if filter_strs:
                filter_info = f" (필터: {', '.join(filter_strs)})"

        lines.append(f"\n**{view_name}**{filter_info}: {len(data_list)}개 데이터\n")

        # 데이터 미리보기
        if view_name == "ai_current_trending":
            lines.append("| 순위 | 채널 | 제목 | 조회수 | 카테고리 |")
            lines.append("|:---:|------|------|------:|:------:|")
            for item in data_list[:5]:
                rank = item.get("순위", "-")
                channel = str(item.get("채널명", ""))[:15]
                title = str(item.get("제목", item.get("동영상_제목", "")))[:25]
                views = format_number(item.get("조회수", 0))
                cat = item.get("카테고리", "-")

                lines.append(f"| {rank} | {channel} | {title}... | {views} | {cat} |")

        elif view_name == "ai_channel_stats":
            lines.append("| 채널 | 구독자수 | 트렌딩영상 | 최고순위 |")
            lines.append("|------|------:|:---:|:---:|")
            for item in data_list[:5]:
                channel = str(item.get("채널명", ""))[:15]
                subs = format_number(item.get("구독자수", 0))
                trending = item.get("트렌딩_영상수", 0)
                best = item.get("최고_순위", "-")
                lines.append(f"| {channel} | {subs} | {trending} | {best} |")

        elif view_name == "ai_category_stats":
            for item in data_list[:5]:
                cat = item.get("카테고리", "-")
                count = item.get("영상수", item.get("동영상수", 0))
                lines.append(f"- {cat}: {count}개 동영상")


    return "\n".join(lines)


# ==========================================
# 메인 함수 (Async Function)
# ==========================================

async def generate_response(
    user_message: str,
    all_data: Dict[str, Any],
    comprehensive_analysis: str,
    conversation_history: List[Dict[str, Any]],
    ollama_host: str,
    model: str,
    question_analysis: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    최종 답변을 생성합니다.

    Args:
        user_message: 사용자 질문
        all_data: 조회된 데이터
        comprehensive_analysis: 종합 분석 텍스트
        conversation_history: 대화 이력
        ollama_host: Ollama 호스트 URL
        model: 모델명
        question_analysis: Step 1 분석 결과

    Returns:
        Dict: {response, response_type, structured_data, thinking}
    """
    print(f"[Step5] 답변 생성 시작: {user_message[:50]}...")

    # 데이터 컨텍스트 준비
    data_context = prepare_data_context(all_data)

    # 데이터가 아예 없는 경우
    if not data_context.strip():
        from ..prompts import get_no_data_system_prompt
        no_data_prompt = get_no_data_system_prompt(question_analysis or {})
        
        messages = [
            {"role": "system", "content": no_data_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response = await call_llm(ollama_host, model, messages, temperature=0.3)
            return {
                "response": response.get("message", {}).get("content", "죄송합니다. 현재 요청하신 내용을 분석할 수 있는 데이터가 없습니다."),
                "response_type": "text",
                "structured_data": None,
                "thinking": "조회된 데이터 없음 -> LLM 설명 생성"
            }
        except Exception as e:
            return {
                "response": "죄송합니다. 현재 요청하신 내용을 분석할 수 있는 데이터가 없습니다.",
                "response_type": "text",
                "structured_data": None,
                "thinking": f"조회된 데이터 없음, LLM 호출 실패: {e}"
            }

    # 필터 정보 수집
    applied_filters = []
    skipped_filters = []
    for view_data in all_data.values():
        filters = view_data.get("filters_applied", [])
        for f in filters:
            if f.get("field") and f.get("value"):
                applied_filters.append(f"{f['field']}={f['value']}")
        skipped = view_data.get("filters_skipped", [])
        for f in skipped:
            if f.get("field") and f.get("value"):
                skipped_filters.append(f"{f['field']}={f['value']}")

    # 현재 시간 구하기
    from datetime import datetime
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 시스템 프롬프트 구성 - 텍스트 요약 기계 (centralized prompt 사용)
    from ..prompts import get_step5_system_prompt
    system_prompt = get_step5_system_prompt(data_context, current_time_str)

    try:
        # 사용자 메시지 원본 전달 (강제 변환 로직 제거)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        # LLM 호출
        print(f"[Step5] LLM 호출 중...")
        response = await call_llm(ollama_host, model, messages, temperature=0.1, num_predict=2048)
        answer = response.get("message", {}).get("content", "")

        if not answer:
            answer = "죄송합니다. 응답을 생성할 수 없습니다."
        
        print(f"[Step5] 응답 생성 완료: {len(answer)} 문자")

        # Structured Data 생성
        structured_data = build_structured_data(all_data, question_analysis)

        # 응답 타입 및 마크다운 테이블 제거 처리
        response_type = "text"
        if structured_data:
            if isinstance(structured_data, list):
                response_type = "dashboard"
                # 대시보드인 경우 텍스트 테이블 제거 (차트가 풍부하므로)
                answer = strip_markdown_tables(answer)
            elif structured_data.get("data"):
                chart_type = structured_data.get("chart_type", "table")
                if chart_type in ["bar", "pie", "line", "comparison"]:
                    response_type = chart_type
                else:
                    response_type = "table"

                # 프론트에서 차트/테이블을 렌더링하므로 텍스트 답변의 마크다운 테이블은 제거
                answer = strip_markdown_tables(answer)

        # Thinking 로그 구성
        thinking_msg = "LLM 데이터 기반 응답 생성"
        if applied_filters:
            thinking_msg += f", 적용된 필터: {applied_filters}"
        if skipped_filters:
            thinking_msg += f", 스킵된 필터: {skipped_filters}"

        return {
            "response": answer,
            "response_type": response_type,
            "structured_data": structured_data,
            "thinking": thinking_msg
        }

    except Exception as e:
        print(f"[Step5] 답변 생성 실패: {e}")
        traceback.print_exc()

        fallback = generate_data_summary(all_data, user_message)
        return {
            "response": fallback,
            "response_type": "text",
            "structured_data": None,
            "thinking": f"폴백 응답: {str(e)}"
        }
