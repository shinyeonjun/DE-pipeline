FROM python:3.11-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY src/ ./src/

# 환경변수 기본값 (Cloud Run에서 오버라이드)
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 진입점
ENTRYPOINT ["python", "-m", "src.main"]
