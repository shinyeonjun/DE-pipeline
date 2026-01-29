"""
Chat Router - AI 챗봇 API 엔드포인트
"""
import httpx
from fastapi import APIRouter
from typing import List
from app.core import settings
from .service import get_chat_service
from .schemas import ChatRequest, ChatResponse, ViewInfo
from .prompts import SUGGESTED_QUESTIONS

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
    except Exception as e:
        import traceback
        traceback.print_exc()
        # 에러 메시지에서 인코딩 문제가 있는 문자 제거
        error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
        return ChatResponse(
            response=f"서버 오류가 발생했습니다: {error_msg}",
            tools_used=[],
            session_id=request.session_id,
            error=error_msg
        )


@router.post("/clear")
async def clear_history():
    """
    대화 히스토리 초기화

    새로운 대화를 시작합니다.
    """
    service = get_chat_service()
    service.clear_history()
    return {"message": "대화 히스토리가 초기화되었습니다."}


@router.get("/views", response_model=List[ViewInfo])
async def get_available_views():
    """
    사용 가능한 데이터 View 목록

    AI가 조회할 수 있는 데이터 View 목록을 반환합니다.
    """
    service = get_chat_service()
    views = await service.get_available_views()
    return views


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
    except Exception as e:
        return {
            "status": "unhealthy",
            "ollama_connected": False,
            "error": str(e)
        }


@router.get("/suggested-questions")
async def get_suggested_questions():
    """
    추천 질문 목록

    AI에게 물어볼 수 있는 예시 질문들을 반환합니다.
    """
    return SUGGESTED_QUESTIONS

