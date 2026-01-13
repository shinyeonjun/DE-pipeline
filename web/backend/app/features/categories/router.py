"""
Categories Router - 카테고리 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from .service import CategoryService
from .schemas import CategoryStats

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("/stats", response_model=List[CategoryStats])
async def get_category_stats():
    """카테고리별 통계"""
    try:
        stats = await CategoryService.get_category_stats()
        return stats
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/distribution")
async def get_category_distribution() -> Dict[str, int]:
    """카테고리별 분포 (파이 차트용)"""
    try:
        distribution = await CategoryService.get_category_distribution()
        return distribution
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

