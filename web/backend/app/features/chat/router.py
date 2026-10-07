"""
Chat Router - AI 챗봇 API 엔드포인트
"""
import logging

import httpx
from fastapi import APIRouter
from typing import List, Optional
from app.core import settings
from app.core.errors import INTERNAL_ERROR_CODE
from .service import get_chat_service
from .schemas import ChatRequest, ChatResponse, ViewInfo
from .prompts import SUGGESTED_QUESTIONS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    AI 챗봇과 대화

    YouTube 트렌딩 데이터를 분석하는 AI와 대화할 수 있습니다.

    예시 질문:
    - "현재 인기 동영상 TOP 10 보여줘"
    - "음악 카테고리 분석해줘"
    - "알고리즘에 영향을 미치는 요소가 뭐야?"
    - "참여율이 높은 채널은?"
    """
    try:
        service = get_chat_service()
        result = await service.chat(request.message, request.session_id)
        return ChatResponse(**result)
    except Exception:
        # 내부 예외 메시지(DB 주소, 쿼리 등)는 로그에만 남기고 사용자에게는 노출하지 않는다.
        logger.exception("Chat request failed (session_id=%s)", request.session_id)
        return ChatResponse(
            response="죄송합니다. 답변을 만드는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.",
            tools_used=[],
            session_id=request.session_id,
            error=INTERNAL_ERROR_CODE
        )


@router.post("/clear")
async def clear_history(session_id: Optional[str] = None):
    """
    대화 히스토리 초기화

    새로운 대화를 시작합니다. session_id를 주면 해당 세션만, 없으면 전체 기록을 지웁니다.
    """
    service = get_chat_service()
    service.clear_history(session_id)
    return {"message": "대화 히스토리가 초기화되었습니다."}


@router.get("/views", response_model=List[ViewInfo])
async def get_available_views():
    """
    사용 가능한 데이터 View 목록

    AI가 조회할 수 있는 데이터 View 목록을 반환합니다.
    """
    service = get_chat_service()
    return service.get_available_views()


@router.get("/health")
async def chat_health():
    """
    AI 챗봇 서비스 상태 확인

    Ollama 연결 상태를 확인합니다.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.ollama_host}/api/tags")

            if response.status_code == 200:
                data = response.json()
                models = [m.get("name") for m in data.get("models", [])]
                return {
                    "status": "healthy",
                    "ollama_connected": True,
                    "available_models": models
                }
            else:
                return {
                    "status": "degraded",
                    "ollama_connected": False,
                    "error": f"Ollama returned status {response.status_code}"
                }
    except httpx.ConnectError:
        return {
            "status": "unhealthy",
            "ollama_connected": False,
            "error": "Cannot connect to Ollama server"
        }
    except Exception:
        logger.exception("Ollama health check failed")
        return {
            "status": "unhealthy",
            "ollama_connected": False,
            "error": INTERNAL_ERROR_CODE
        }


@router.get("/suggested-questions")
async def get_suggested_questions():
    """
    추천 질문 목록

    AI에게 물어볼 수 있는 예시 질문들을 반환합니다.
    """
    return SUGGESTED_QUESTIONS

