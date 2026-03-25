# DE-pipeline

[![Data](https://img.shields.io/badge/data-YouTube%20API-red)](#)
[![Backend](https://img.shields.io/badge/backend-FastAPI-009688)](#)
[![Frontend](https://img.shields.io/badge/frontend-Next.js-111827)](#)
[![Infra](https://img.shields.io/badge/infra-GCP%20%C2%B7%20Supabase-2563eb)](#)

YouTube 데이터를 수집, 정제, 적재하고 분석 API와 대시보드, 챗봇까지 연결한 데이터 파이프라인 프로젝트입니다.

![DE-pipeline 대시보드](docs/assets/dashboard.png)

## 한눈에 보기

- Raw -> Clean -> Mart -> API -> Dashboard 흐름
- YouTube API 기반 videos, comments, categories, channels 수집
- GCS Raw 적재, Supabase/PostgreSQL 정제
- FastAPI 분석 API
- Next.js 대시보드와 챗봇

## 내가 한 것

- 데이터 수집 파이프라인 설계
- GCS 적재 구조와 메타데이터 규칙 정리
- Transform 레이어 구현
- FastAPI 기반 분석 API 구현
- Next.js 대시보드와 챗봇 흐름 연결

## 구조

- `youtube_collector/`: 수집기
- `transform/`: 정제 및 적재
- `web/backend/`: 분석 API
- `web/frontend/`: 대시보드와 채팅 UI

## 실행

### Collector

```powershell
cd youtube_collector
pip install -r requirements.txt
python -m src.main --job videos
```

### Backend

```powershell
cd web\backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```powershell
cd web\frontend
npm install
npm run dev
```
