"""
Transformers Package - 데이터 유형별 변환기
"""
from .videos import transform_videos
from .categories import transform_categories
from .comments import transform_comments
from .channels import transform_channels


def get_transformer_for_path(blob_path: str):
    """
    blob 경로를 기반으로 적절한 트랜스포머 함수와 데이터 타입을 반환합니다.
    
    Returns:
        tuple: (transformer_function, data_type) or (None, None)
    """
    if "videos_list" in blob_path:
        return transform_videos, "videos_list"
    elif "comment_threads" in blob_path:
        return transform_comments, "comment_threads"
    elif "video_categories" in blob_path:
        return transform_categories, "video_categories"
    elif "channels" in blob_path:
        return transform_channels, "channels"
    
    return None, None
