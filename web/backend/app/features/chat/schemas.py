"""
Chat Schemas - AI 챗봇 관련 데이터 모델
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal


class ChatRequest(BaseModel):
    """채팅 요청"""
    message: str = Field(..., min_length=1, max_length=2000, description="사용자 메시지")
    session_id: Optional[str] = Field(None, description="세션 ID (대화 유지용)")


class ChatResponse(BaseModel):
    """채팅 응답"""
    response: str = Field(..., description="AI 응답")
    tools_used: List[str] = Field(default=[], description="사용된 데이터 조회 함수")
    session_id: Optional[str] = Field(None, description="세션 ID")
    error: Optional[str] = Field(None, description="에러 메시지")
    # 시각화를 위한 추가 필드
    response_type: Optional[Literal["table", "list", "stats", "comparison", "text", "cards", "pie", "bar", "line"]] = Field(
        None, description="답변 타입 (표, 리스트, 통계, 비교, 텍스트, 카드, 파이, 바, 라인)"
    )
    structured_data: Optional[Dict[str, Any]] = Field(
        None, description="구조화된 데이터 (표, 카드 등에 사용)"
    )
    # 능동적 제안 필드
    suggested_questions: Optional[List[str]] = Field(
        default=[], description="추가 질문 제안"
    )
    insights: Optional[List[str]] = Field(
        default=[], description="데이터 인사이트"
    )
    related_analyses: Optional[List[str]] = Field(
        default=[], description="관련 분석 제안"
    )
    data_patterns: Optional[List[str]] = Field(
        default=[], description="발견된 데이터 패턴"
    )


class ViewInfo(BaseModel):
    """View 정보"""
    name: str
    description: str
    columns: List[str]

