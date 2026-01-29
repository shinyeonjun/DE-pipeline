"""
Pytest 설정 및 공통 Fixtures
"""
import pytest
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_ollama_host() -> str:
    """테스트용 Ollama 호스트 URL"""
    return "http://localhost:11434"


@pytest.fixture
def mock_model() -> str:
    """테스트용 모델명"""
    return "qwen2.5-coder:7b-instruct"
