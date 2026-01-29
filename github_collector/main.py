"""GitHub Collector (Root Wrapper)"""
import sys
import os

# src 폴더를 path에 추가하여 모듈 참조 가능하게 설정
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.main import main
except ImportError:
    # 패키지 구조로 실행될 때를 대비
    from github_collector.src.main import main

if __name__ == "__main__":
    main()
