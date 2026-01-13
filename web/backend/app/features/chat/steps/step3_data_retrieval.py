"""
Step 3: 데이터 조회 (Data Retrieval)
선택된 View에서 실제 데이터를 조회하고 필터를 적용합니다.
Supabase DB와 직접 상호작용하는 계층입니다.
"""
import json
from typing import Dict, Any, List, Tuple, Optional
from app.core import supabase
from ..views import VIEW_CATALOG

# ==========================================
# 헬퍼 함수 (Pure Functions)
# ==========================================

def summarize_view_data(view_name: str, data_list: List[Dict]) -> str:
    """
    조회된 데이터를 사용자에게 보여주기 위한 요약 텍스트를 생성합니다.

    Args:
        view_name: View 이름
        data_list: 데이터 목록

    Returns:
        요약 텍스트
    """
    if not data_list:
        return f"{view_name}: 데이터 없음"
    
    try:
        if view_name == "ai_current_trending":
            top_item = data_list[0] if data_list else {}
            return f"{view_name}: {len(data_list)}개 동영상, 1위={top_item.get('채널명', '')} - {top_item.get('제목', '')[:30]}"
        elif view_name == "ai_channel_stats":
            top_channel = data_list[0] if data_list else {}
            return f"{view_name}: {len(data_list)}개 채널, 최고 구독자={top_channel.get('채널명', '')} ({top_channel.get('구독자수', 0):,}명)"
        elif view_name == "ai_category_stats":
            top_category = data_list[0] if data_list else {}
            return f"{view_name}: {len(data_list)}개 카테고리, 최다={top_category.get('카테고리', '')} ({top_category.get('영상수', 0)}개)"
        elif view_name == "ai_growth_rate":
            top_growth = data_list[0] if data_list else {}
            return f"{view_name}: {len(data_list)}개 동영상, 최고 성장률={top_growth.get('성장률_퍼센트', 0):.2f}%"

        else:
            return f"{view_name}: {len(data_list)}개 항목"
    except Exception as e:
        return f"{view_name}: {len(data_list)}개 항목 (요약 실패: {e})"


def apply_memory_filter(
    data: List[Dict],
    filters: List[Dict[str, Any]]
) -> Tuple[List[Dict], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    메모리 상에서 데이터를 필터링합니다. (이중 검증용)

    Args:
        data: 원본 데이터 목록
        filters: 적용할 필터 목록

    Returns:
        (필터링된_데이터, 적용된_필터, 스킵된_필터)
    """
    if not filters or not data:
        return data, [], []

    # 데이터의 첫 번째 항목에서 사용 가능한 필드 확인
    available_fields = set(data[0].keys()) if data else set()

    filtered = data
    applied_filters = []
    skipped_filters = []

    for f in filters:
        field = f.get("field", "")
        operator = f.get("operator", "=")
        value = f.get("value")

        if not field or value is None:
            continue

        # 필드가 데이터에 존재하는지 확인
        if field not in available_fields:
            # print(f"    [필터 스킵] '{field}' 필드가 데이터에 없음")
            skipped_filters.append(f)
            continue

        new_filtered = []
        for item in filtered:
            item_value = item.get(field)
            if item_value is None:
                continue

            try:
                if operator == "=":
                    if str(item_value).lower() == str(value).lower():
                        new_filtered.append(item)
                elif operator == ">":
                    if float(item_value) > float(value):
                        new_filtered.append(item)
                elif operator == ">=":
                    if float(item_value) >= float(value):
                        new_filtered.append(item)
                elif operator == "<":
                    if float(item_value) < float(value):
                        new_filtered.append(item)
                elif operator == "<=":
                    if float(item_value) <= float(value):
                        new_filtered.append(item)
                elif operator == "contains":
                    if str(value).lower() in str(item_value).lower():
                        new_filtered.append(item)
            except (ValueError, TypeError):
                continue

        filtered = new_filtered
        applied_filters.append(f)

    return filtered, applied_filters, skipped_filters


# ==========================================
# DB 조회 함수
# ==========================================

async def query_view(
    view_name: str,
    limit: int = 20,
    filters: Optional[List[Dict[str, Any]]] = None,
    sort: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Supabase View에서 데이터를 직접 조회합니다.

    Args:
        view_name: View 이름
        limit: 조회할 데이터 개수
        filters: 필터 목록
        sort: 정렬 옵션

    Returns:
        조회 결과 딕셔너리 {"data": ..., "count": ...}
    """
    try:
        query = supabase.table(view_name).select("*")

        # DB 레벨 필터 적용
        if filters:
            for f in filters:
                field = f.get("field", "")
                operator = f.get("operator", "=")
                value = f.get("value")

                if not field or value is None:
                    continue

                if operator == "=":
                    query = query.eq(field, value)
                elif operator == ">":
                    query = query.gt(field, value)
                elif operator == ">=":
                    query = query.gte(field, value)
                elif operator == "<":
                    query = query.lt(field, value)
                elif operator == "<=":
                    query = query.lte(field, value)
                elif operator == "contains":
                    query = query.ilike(field, f"%{value}%")
                
                print(f"    [DB 필터] {field} {operator} {value}")

        # 정렬 적용
        if sort and sort.get("field"):
            order_field = sort.get("field")
            ascending = sort.get("order", "asc") == "asc"
            query = query.order(order_field, desc=not ascending)
            print(f"    [DB 정렬] {order_field} {'ASC' if ascending else 'DESC'}")

        # Limit 적용 및 실행
        result = query.limit(limit).execute()

        return {
            "data": result.data,
            "count": len(result.data),
            "view_name": view_name
        }
    except Exception as e:
        return {
            "error": str(e),
            "view_name": view_name
        }


async def _fetch_single_view(
    view_name: str,
    limit: int,
    filters: Optional[List[Dict[str, Any]]] = None,
    sort: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """개별 View에 대해 분석 및 조회를 수행하는 내부 함수"""
    try:
        # DB 필터 적용을 위해 넉넉하게 조회 (In-Memory 필터링 예비)
        fetch_limit = limit * 3 if filters else limit

        # View 정보 확인 및 Sort 컬럼 검증
        view_info = None
        for vt_info in VIEW_CATALOG.values():
            if vt_info.name == view_name:
                view_info = vt_info
                break
        
        # Sort 컬럼 보정 로직
        final_sort = sort
        if sort and view_info:
            req_col = sort.get("field")
            if req_col and req_col not in view_info.columns:
                # 보정 규칙
                correction = None
                if req_col == "순위":
                    if "평균_순위" in view_info.columns: correction = "평균_순위"
                    elif "최고_순위" in view_info.columns: correction = "최고_순위"
                elif req_col == "조회수":
                    if "평균_조회수" in view_info.columns: correction = "평균_조회수"
                    elif "총_조회수" in view_info.columns: correction = "총_조회수"
                
                if correction:
                    final_sort = {"field": correction, "order": sort.get("order", "desc")}
                else:
                    final_sort = None

        result_obj = await query_view(
            view_name,
            fetch_limit,
            filters=filters,
            sort=final_sort
        )

        if "error" in result_obj:
            return {"error": result_obj["error"], "view_name": view_name}

        data_list = result_obj.get("data", [])
        if not data_list:
            # Fallback (필터 무시)
            if filters:
                result_obj = await query_view(view_name, limit, filters=None, sort=final_sort)
                data_list = result_obj.get("data", [])
                if data_list:
                    return {
                        "view_name": view_name,
                        "data": data_list,
                        "fallback": True
                    }
            return {"error": "데이터 없음", "view_name": view_name}

        # 메모리 필터 재적용
        if filters:
            data_list, _, _ = apply_memory_filter(data_list, filters)
        
        data_list = data_list[:limit]
        if not data_list:
            return {"error": "필터링 후 데이터 없음", "view_name": view_name}
            
        return {
            "view_name": view_name,
            "data": data_list,
            "fallback": False
        }

    except Exception as e:
        return {"error": str(e), "view_name": view_name}

async def retrieve_data(
    selected_views: List[Tuple[str, int]],
    filters: Optional[List[Dict[str, Any]]] = None,
    sort: Optional[Dict[str, str]] = None
) -> Tuple[Dict[str, Any], List[str], List[str], str]:
    """선택된 여러 View에서 데이터를 병렬적으로 조회합니다."""
    import asyncio
    print(f"[Step3] 데이터 병렬 조회 시작: {len(selected_views)}개 View")

    # 병렬 태스크 생성
    tasks = [
        _fetch_single_view(view_name, limit, filters, sort)
        for view_name, limit in selected_views
    ]
    
    # 병렬 실행
    results = await asyncio.gather(*tasks)

    all_data = {}
    tools_used = []
    view_summaries = []
    thinking_parts = []
    
    for res in results:
        view_name = res.get("view_name")
        if "error" in res:
            thinking_parts.append(f"실패: {view_name} - {res['error']}")
            continue
            
        data = res.get("data", [])
        all_data[view_name] = {"data": data, "count": len(data)}
        tools_used.append(view_name)
        
        summary = summarize_view_data(view_name, data)
        if res.get("fallback"):
            view_summaries.append(f"[Fallback] {summary}")
            thinking_parts.append(f"성공(Fallback): {view_name}")
        else:
            view_summaries.append(summary)
            thinking_parts.append(f"성공: {view_name}")

    thinking = "\n".join(thinking_parts)
    return all_data, tools_used, view_summaries, thinking

