"""
Trending Router - 트렌딩 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from typing import List
from .service import TrendingService
from .schemas import VideoSnapshot, TrendingResponse

router = APIRouter(prefix="/api/trending", tags=["Trending"])


@router.get("/current", response_model=TrendingResponse)
async def get_current_trending():
    """현재 트렌딩 TOP 50"""
    try:
        videos, snapshot_at = await TrendingService.get_current_trending()
        
        if not videos:
            raise HTTPException(status_code=404, detail="No trending data available")
        
        return TrendingResponse(
            total=len(videos),
            snapshot_at=snapshot_at,
            videos=videos
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/video/{video_id}", response_model=VideoSnapshot)
async def get_video_latest(video_id: str):
    """특정 비디오의 최신 스냅샷"""
    try:
        video = await TrendingService.get_video_by_id(video_id)
        
        if not video:
            raise HTTPException(status_code=404, detail="Video not found")
        
        return video
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/velocity", response_model=List[VideoSnapshot])
async def get_rising_videos(limit: int = 10):
    """급상승 영상 (view_velocity 기준)"""
    try:
        videos = await TrendingService.get_rising_videos(limit)
        return videos
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

