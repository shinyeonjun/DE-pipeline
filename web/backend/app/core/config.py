"""
Application Configuration
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # Supabase
    supabase_url: str
    supabase_service_key: str
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]
    
    # Ollama (Optional)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:7b-instruct"  # AI 챗봇 모델
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

