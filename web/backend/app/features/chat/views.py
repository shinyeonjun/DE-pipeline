"""
Chat Views - AI가 접근할 수 있는 View 정의
"""
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict


class ViewType(str, Enum):
    """사용 가능한 AI View 목록"""
    CURRENT_TRENDING = "ai_current_trending"
    CATEGORY_STATS = "ai_category_stats"
    CHANNEL_STATS = "ai_channel_stats"
    CONTENT_TYPE_ANALYSIS = "ai_shorts_vs_regular"
    TRENDING_VELOCITY = "ai_trending_velocity"
    ALGORITHM_FACTORS = "ai_algorithm_factors"
    ENGAGEMENT_CORRELATION = "ai_engagement_correlation"
    RANK_MOVEMENT = "ai_rank_movement"
    HOURLY_PATTERN = "ai_hourly_pattern"
    DAILY_SUMMARY = "ai_daily_summary"


@dataclass
class ViewInfo:
    """View 정보"""
    name: str
    description: str
    columns: List[str]


# AI가 접근할 수 있는 View 정보 (DB 스키마 정합성 패치 완료)
VIEW_CATALOG: Dict[ViewType, ViewInfo] = {
    ViewType.CURRENT_TRENDING: ViewInfo(
        name="ai_current_trending",
        description="현재 TOP 50 인기 동영상 (순위, 제목, 채널, 조회수, 좋아요, 참여율 등)",
        columns=["순위", "제목", "채널명", "카테고리", "조회수", "좋아요", "댓글수", "참여율_퍼센트", "쇼츠여부", "업로드후_시간", "시간당_조회수", "영상길이_초", "video_id", "channel_id", "thumbnail_url", "수집시점"]
    ),
    ViewType.CATEGORY_STATS: ViewInfo(
        name="ai_category_stats",
        description="카테고리별 통계 (영상수, 평균 조회수, 평균 참여율, 점유율)",
        columns=["카테고리", "영상수", "비율_퍼센트", "평균_조회수", "평균_좋아요", "평균_댓글", "평균_참여율_퍼센트", "평균_시간당조회수", "쇼츠_수", "쇼츠_비율_퍼센트", "평균_업로드후_시간"]
    ),
    ViewType.CHANNEL_STATS: ViewInfo(
        name="ai_channel_stats",
        description="채널별 트렌딩 성과 (구독자수, 트렌딩 횟수, 순위, 조회수)",
        columns=["채널명", "구독자수", "트렌딩_영상수", "트렌딩_일수", "최고_순위", "평균_조회수", "평균_좋아요", "평균_참여율_퍼센트", "최고_조회수", "채널_총영상수", "국가", "channel_id"]
    ),
    ViewType.CONTENT_TYPE_ANALYSIS: ViewInfo(
        name="ai_shorts_vs_regular",
        description="콘텐츠 유형별 분석 (쇼츠 vs 일반)",
        columns=["콘텐츠_유형", "영상수", "평균_조회수", "평균_좋아요", "평균_댓글", "평균_참여율_퍼센트", "평균_순위", "평균_업로드후_시간"]
    ),
    ViewType.TRENDING_VELOCITY: ViewInfo(
        name="ai_trending_velocity",
        description="트렌딩 진입 속도 분석",
        columns=["속도_구간", "영상수", "평균_조회수", "평균_참여율_퍼센트", "평균_순위", "쇼츠_비율"]
    ),
    ViewType.ALGORITHM_FACTORS: ViewInfo(
        name="ai_algorithm_factors",
        description="알고리즘 영향 요인 분석",
        columns=["순위_구간", "영상수", "평균_업로드후_시간", "평균_시간당조회수", "평균_참여율_퍼센트", "평균_좋아요율_퍼센트", "평균_댓글율_퍼센트", "평균_조회수", "중앙값_조회수", "평균_구독자수", "쇼츠_비율"]
    ),
    ViewType.ENGAGEMENT_CORRELATION: ViewInfo(
        name="ai_engagement_correlation",
        description="참여율과 순위 상관관계",
        columns=["참여율_구간", "평균_순위", "영상수", "평균_조회수", "최고_순위", "최저_순위"]
    ),
    ViewType.RANK_MOVEMENT: ViewInfo(
        name="ai_rank_movement",
        description="순위 변동 패턴 분석",
        columns=["변동_유형", "평균_이전순위", "평균_현재순위", "평균_변동폭", "영상수"]
    ),
    ViewType.HOURLY_PATTERN: ViewInfo(
        name="ai_hourly_pattern",
        description="시간별 트렌드 변화 패턴",
        columns=["시간", "평균_순위", "영상수", "평균_조회수", "평균_참여율_퍼센트", "신규_진입수"]
    ),
    ViewType.DAILY_SUMMARY: ViewInfo(
        name="ai_daily_summary",
        description="일별 요약 통계",
        columns=["날짜", "고유_영상수", "고유_채널수", "평균_조회수", "평균_참여율_퍼센트", "최다_카테고리"]
    ),
}



def get_view_catalog_text() -> str:
    """View 카탈로그를 텍스트로 변환"""
    lines = []
    for view_type, info in VIEW_CATALOG.items():
        lines.append(f"- {view_type.value}: {info.description}")
        lines.append(f"  컬럼: {', '.join(info.columns)}")
    return "\n".join(lines)

