"""
YouTube Analytics API - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core import settings, supabase
from app.features.trending import router as trending_router
from app.features.analytics import router as analytics_router
from app.features.categories import router as categories_router
from app.features.videos import router as videos_router
from app.features.chat import router as chat_router

# FastAPI 앱 생성
app = FastAPI(
    title="YouTube Analytics API",
    description="YouTube 트렌딩 데이터 분석 API",
    version="1.0.0",
    debug=settings.debug
)

# CORS 설정 (allow_credentials=True일 때는 "*" 사용 불가)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 라우터 등록
app.include_router(trending_router)
app.include_router(analytics_router)
app.include_router(categories_router)
app.include_router(videos_router)
app.include_router(chat_router)


@app.get("/")
async def root():
    """헬스 체크"""
    return {
        "status": "healthy",
        "message": "YouTube Analytics API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """상세 헬스 체크"""
    try:
        # Supabase 연결 테스트
        result = supabase.table('fact_video_snapshots')\
            .select('*')\
            .limit(1)\
            .execute()
        
        data_count = len(result.data) if result.data else 0
        
        return {
            "status": "healthy",
            "database": "connected",
            "data_count": data_count
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
