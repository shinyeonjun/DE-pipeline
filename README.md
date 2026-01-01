# 데이터 엔지니어링 파이프라인 (GDELT + EIA)

뉴스(GDELT)와 에너지(EIA) 데이터를 수집/정제/저장하는 운영 가능한 데이터 파이프라인 프로젝트입니다.

## 🎯 프로젝트 목표

**"API 수집 스크립트" 수준이 아니라, 운영 가능한 데이터 파이프라인(재실행/중복방지/품질검사/백필/로그)을 클라우드 환경에서 완주하는 것**

---

## 1. 왜 이 프로젝트인가?

실무 데이터 인프라/데이터 엔지니어 포지션에서 자주 다루는 형태는 아래와 같습니다.

- **외부/내부 시스템에서 발생하는 시계열 데이터**
- **주기적 수집(near real-time) + 배치 집계(batch)**
- **누락/지연/중복/이상치 등 데이터 품질 이슈**
- **분석/대시보드를 위해 마트(Mart) 테이블 제공**
- **실패 대응(재시도/로깅/알림) 및 재처리(Backfill)**

GDELT와 EIA 데이터는 도메인만 다를 뿐, 위 패턴을 그대로 연습/증명하기에 좋은 데이터입니다.

---

## 2. 핵심 기능

### 2.1 뉴스 데이터 (GDELT)

- **데이터 소스**: BigQuery Public Dataset 활용
- **정제/변환**: BigQuery Scheduled Query로 clean/mart 생성
- **저장**: Cloud Run Job으로 주기적으로 mart를 Supabase에 upsert

### 2.2 에너지 데이터 (EIA)

- **데이터 수집**: Cloud Run Job으로 API 호출
- **RAW 저장**: GCS에 원문 JSON 보존
- **정제/적재**: Python으로 시계열 데이터 정제 후 Supabase clean 테이블에 upsert

---

## 3. 데이터 파이프라인 아키텍처

### 3.1 뉴스(GDELT) 파이프라인

- BigQuery에서 데이터 조회/변환
- Supabase에 mart 테이블로 저장

### 3.2 에너지(EIA) 파이프라인

- Cloud Run Job으로 API 호출
- RAW 데이터를 GCS에 저장
- Python 스크립트로 clean 데이터 생성

### 3.3 Job 실행 방식

- **방식 A (단일 Job, 통합)**
  - EIA API 호출 → GCS raw 저장 → Python 변환 → Supabase upsert

- **방식 B (2 Job 분리)**
  - `eia_ingest_job`: API 호출 → GCS raw 저장
  - `eia_transform_load_job`: GCS raw 읽기 → 변환 → Supabase upsert

---

## 4. 기술 스택

- **언어**: Python
- **스케줄링**: Cloud Scheduler로 Cloud Run Job 주기 실행
- **컨테이너**: Cloud Run Job 사용
- **원시 데이터 저장**: GCS (Google Cloud Storage)
- **정제 데이터 저장**: Supabase (PostgreSQL)
- **빅데이터 쿼리**: BigQuery (GDELT)
- **워크플로우**: Workflows (Job 오케스트레이션, 선택사항)

---

## 5. Supabase 테이블 구조

- **clean**: 시계열 clean 테이블
- **mart**: 분석용 7~14일 롤링 mart 테이블
- 참고: Supabase는 PostgreSQL 기반, 필요시 BigQuery와 동기화

---

## 6. RAW 데이터 보존 정책

- **GCS 라이프사이클 규칙**으로 RAW 데이터 30일 보관

---

## 7. 환경 설정 (EIA 수집)

### 7.1 환경 변수 설정

`.env` 파일에 다음 내용을 설정:

```env
API_URL=https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/
API_KEY=your_eia_key
API_PARAMS=frequency=hourly&data[0]=value&facets[respondent][]=ERCO&facets[fueltype][]=NG&facets[fueltype][]=WND&facets[fueltype][]=SUN&facets[fueltype][]=COL&facets[fueltype][]=NUC&sort[0][column]=period&sort[0][direction]=desc&offset=0&length=1
TIMEOUT_SECONDS=90
```

### 7.2 실행

```bash
python data_collect.py --key-param api_key
```

RAW 데이터 저장 경로:
- `data/raw/eia/NG/12-31/05.json`

---

## 8. 클라우드 아키텍처

### 8.1 EIA 데이터 수집 (Cloud Run Job)

- **수집 Job**: EIA API 호출 → GCS RAW 저장
- **정제 Job**: GCS RAW 읽기 → Python 정제 → Supabase clean 저장
- **스케줄러**: Cloud Scheduler로 주기 실행

### 8.2 GDELT 뉴스 데이터 (BigQuery + Cloud Run Job)

- **정제**: BigQuery Scheduled Query
- **저장**: Cloud Run Job으로 Supabase mart 테이블 upsert

---

## 9. 데이터 레이어 설계

### 9.1 RAW Layer (원본 보존)

- **목적**: 재현 가능성(재처리/백필), 스키마 변경 대응, 원본 감사(Audit)
- **저장 위치**: GCS
- **형식**: JSON 원문 파일
- **보존 기간**: 30일 (GCS 라이프사이클 규칙)

### 9.2 CLEAN Layer (정제/표준화)

- **목적**: 분석/조인을 위한 "신뢰 가능한 단일 소스"
- **저장 위치**: Supabase (PostgreSQL)
- **특징**:
  - 고유키(예: 기준시각) 기반 중복 방지
  - 타입 정리, 컬럼 표준화
  - idempotent upsert

### 9.3 MART Layer (대시보드/리포트 최적화)

- **목적**: 대시보드가 복잡한 계산 없이 바로 조회 가능
- **저장 위치**: Supabase (PostgreSQL)
- **특징**: 7~14일 롤링 윈도우로 최근 데이터 집계

---

## 10. 프로젝트 구조

```
data_collect/
  src/
    collector.py      # EIA API 수집 로직
    config.py         # 설정 관리
    data_collect.py   # 메인 실행 스크립트
    http_client.py    # HTTP 클라이언트
    storage.py        # 로컬/GCS 저장 로직
    gcs_storage.py    # GCS 업로드 유틸
  cloudbuild.yaml     # Cloud Build 설정
  Dockerfile          # 컨테이너 이미지 빌드
  requirements.txt    # Python 의존성
  .dockerignore       # Docker 빌드 제외 파일

README.md
```

---

## 11. 포트폴리오에서 강조할 포인트(면접/자소서용)

이 프로젝트는 아래 항목을 증명합니다.

1. ✅ **RAW 원문 보존을 통한 재현 가능성** (GCS 보존)
2. ✅ **idempotent upsert로 중복/재실행 안정성** (Supabase)
3. ✅ **클라우드 네이티브 아키텍처** (Cloud Run Job, GCS, BigQuery)
4. ✅ **clean → mart 분리로 분석/대시보드 친화적 모델링**
5. ✅ **스케줄링/로깅으로 운영 가능한 파이프라인 구성**

---

## 12. 로드맵

### v1 (현재)

- [x] EIA API 수집 및 GCS RAW 저장
- [x] Cloud Run Job으로 수집 자동화
- [ ] Python으로 시계열 데이터 정제 및 Supabase clean 저장
- [ ] GDELT BigQuery 쿼리 및 Supabase mart 저장
- [ ] 데이터 품질 체크 (DQ) 규칙 구현

### v2 (운영 안정화)

- [ ] Cloud Scheduler 통합
- [ ] 에러 알림 및 모니터링
- [ ] 데이터 품질 대시보드
- [ ] 백필(Backfill) 기능

### v3 (확장)

- [ ] 실시간 스트리밍 파이프라인 (Pub/Sub + Dataflow)
- [ ] 머신러닝 피처 스토어 통합
- [ ] 자동 데이터 품질 검증

---

## 13. 주의사항

- 본 프로젝트는 학습/포트폴리오 목적입니다.
- 공공 API 정책(호출 제한/약관)을 준수합니다.
- GCS와 Supabase 사용 비용을 고려해야 합니다.

---

## 14. 참고 자료

- **EIA API**: https://www.eia.gov/opendata/
- **GDELT Project**: https://www.gdeltproject.org/
- **BigQuery Public Datasets**: https://cloud.google.com/bigquery/public-data
- **Supabase**: https://supabase.com/
- **Cloud Run Jobs**: https://cloud.google.com/run/docs/create-jobs

---
