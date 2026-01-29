"""
Core Module - 공통 핵심 모듈
"""
from .config import settings
from .database import supabase, get_supabase
from .base_service import BaseService

__all__ = ['settings', 'supabase', 'get_supabase', 'BaseService']

