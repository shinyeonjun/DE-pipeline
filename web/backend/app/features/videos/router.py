"""
Videos Router - 비디오 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from .service import VideoService
from .schemas import VideoHistory

router = APIRouter(prefix="/api/videos", tags=["Videos"])


@router.get("/{video_id}/history", response_model=VideoHistory)
async def get_video_history(video_id: str):
    """비디오 성장 히스토리 (시계열)"""
    try:
        history = await VideoService.get_video_history(video_id)
        
        if not history:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return history
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

