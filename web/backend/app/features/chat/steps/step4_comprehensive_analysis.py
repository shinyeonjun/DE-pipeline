"""
Step 4: 종합 분석 (Comprehensive Analysis) - [Refactored: Dynamic Engine]
모든 View에서 조회된 데이터를 메타데이터 기반으로 자동 분석하여 인사이트를 도출합니다.
하드코딩된 View 분기 로직을 제거하여 확장성을 확보했습니다.
"""
import statistics
from typing import Dict, Any, List, Tuple
import math

# ==========================================
# 헬퍼 함수 (Deep Insight Functions)
# ==========================================

def get_basic_stats(data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
    """데이터 리스트에서 수치적/범주적 통계를 자동으로 추출합니다."""
    if not data_list:
        return {}
    
    keys = data_list[0].keys()
    stats = {"numeric": {}, "categorical": {}}
    
    for key in keys:
        values = [item.get(key) for item in data_list if item.get(key) is not None]
        if not values: continue
            
        # 수치형 데이터 분석
        if isinstance(values[0], (int, float)):
            stats["numeric"][key] = {
                "values": values,
                "total": sum(values),
                "avg": sum(values) / len(values),
                "max": max(values),
                "min": min(values),
                "std": statistics.stdev(values) if len(values) > 1 else 0
            }
        # 범주형 데이터 분석
        elif isinstance(values[0], str) and "id" not in key.lower() and "url" not in key.lower():
            counts = {}
            for v in values: counts[v] = counts.get(v, 0) + 1
            top_val = max(counts, key=counts.get)
            stats["categorical"][key] = {"top": top_val, "unique_count": len(set(values))}
                
    return stats

def calculate_correlations(num_stats: Dict[str, Any]) -> List[str]:
    """수치형 지표 간의 상관관계를 계산하여 인사이트를 도출합니다."""
    insights = []
    keys = list(num_stats.keys())
    
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            k1, k2 = keys[i], keys[j]
            v1, v2 = num_stats[k1]["values"], num_stats[k2]["values"]
            
            if len(v1) > 2 and len(v2) > 2:
                try:
                    # 상관계수 계산 (비율이 비슷한지 확인)
                    corr = statistics.correlation(v1, v2)
                    if abs(corr) > 0.7:
                        direction = "강한 양의 상관관계" if corr > 0 else "강한 음의 상관관계"
                        insights.append(f"  * [인사이트] {k1}와 {k2} 사이의 {direction} 발견 (r={corr:.2f})")
                except: pass
    return insights

def detect_anomalies(num_stats: Dict[str, Any], data_list: List[Dict[str, Any]]) -> List[str]:
    """Z-Score를 사용하여 눈에 띄는 이상치(아웃라이어)를 포착합니다."""
    anomalies = []
    for key, s in num_stats.items():
        if s["std"] > 0:
            for item in data_list:
                val = item.get(key)
                if val is not None and isinstance(val, (int, float)):
                    z_score = (val - s["avg"]) / s["std"]
                    if abs(z_score) > 2.5: # 99% 범위를 벗어남
                        name = item.get("제목") or item.get("채널명") or "특정 항목"
                        status = "현저히 높음" if z_score > 0 else "현저히 낮음"
                        anomalies.append(f"  * [이상 탐지] '{name}'의 {key}가 {status} (Z-Score: {z_score:.1f})")
                        if len(anomalies) >= 3: break # 너무 많으면 중단
    return anomalies

# ==========================================
# 메인 함수 (Pure Function)
# ==========================================

def analyze_data(
    all_data: Dict[str, Any], 
    user_message: str, 
    question_analysis: Dict[str, Any]
) -> Tuple[str, str]:
    """
    모든 View의 데이터를 딥 러닝 분석가 수준으로 깊게 분석합니다.
    """
    print(f"[Step4] 딥 인사이트 분석 시작: {len(all_data)}개 View")
    
    analysis_parts = []
    thinking_parts = []
    
    for view_name, view_data in all_data.items():
        data_list = view_data.get("data", [])
        if not data_list: continue
            
        # 1. 자동 통계 계산
        stats = get_basic_stats(data_list)
        num_stats = stats.get("numeric", {})
        
        view_summary = [f"**{view_name}** 분석 (데이터 {len(data_list)}건)"]
        
        # 2. 수치형 요약
        priority_keys = ["조회수", "구독자수", "좋아요", "댓글", "참여율", "성장률", "순위", "영상수", "시간당_조회수"]
        added_keys = set()
        for p_key in priority_keys:
            for actual_key in num_stats.keys():
                if p_key in actual_key and actual_key not in added_keys:
                    s = num_stats[actual_key]
                    view_summary.append(f"  * {actual_key}: 평균 {s['avg']:,.1f} (최대 {s['max']:,})")
                    added_keys.add(actual_key)
                    break
        
        # 3. 딥 인사이트 (상관관계 & 이상치)
        if len(data_list) > 3:
            # 상관관계 분석
            correlations = calculate_correlations(num_stats)
            view_summary.extend(correlations[:2])
            
            # 이상 탐지
            anomalies = detect_anomalies(num_stats, data_list)
            view_summary.extend(anomalies[:2])

        analysis_parts.append("\n".join(view_summary))
        thinking_parts.append(f"View '{view_name}' 분석 완료 ({len(num_stats)}개 수치 지표 추출)")
    
    comprehensive_analysis = "\n\n".join(analysis_parts)
    thinking = "\n".join(thinking_parts)
    
    print(f"[Step4] 딥 인사이트 분석 완료")
    return comprehensive_analysis, thinking
