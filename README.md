# KPX 전력수급 데이터 파이프라인 (Data Engineering Portfolio)

공공데이터(OpenAPI)로 제공되는 전력 수급(수요/공급/예비 등) 시계열 데이터를 주기적으로 수집하고, 원본(RAW)을 보존한 뒤 정제(CLEAN) 및 집계(MART)까지 자동으로 생성하는 데이터 엔지니어링 파이프라인 프로젝트입니다.

## 🎯 프로젝트 목표

**"API 수집 스크립트" 수준이 아니라, 운영 가능한 데이터 파이프라인(재실행/중복방지/품질검사/백필/로그)을 최소 구성으로 완주하는 것**

---

## 1. 왜 이 프로젝트인가?

실무 데이터 인프라/데이터 엔지니어 포지션에서 자주 다루는 형태는 아래와 같습니다.

- **외부/내부 시스템에서 발생하는 시계열 데이터**
- **주기적 수집(near real-time) + 배치 집계(batch)**
- **누락/지연/중복/이상치 등 데이터 품질 이슈**
- **분석/대시보드를 위해 마트(Mart) 테이블 제공**
- **실패 대응(재시도/로깅/알림) 및 재처리(Backfill)**

전력수급 데이터는 도메인만 다를 뿐, 위 패턴을 그대로 연습/증명하기에 좋은 데이터입니다.

---

## 2. 핵심 기능

### 2.1 수집(Extract)

- KPX 전력수급 OpenAPI 호출
- 호출 결과 원문(XML) 그대로 저장(RAW Layer)

### 2.2 정제/표준화(Transform)

- XML 파싱 → 정형 레코드로 변환
- 타입 변환(문자→숫자/시간), 단위/컬럼 표준화
- 중복 실행해도 데이터가 깨지지 않도록 고유키 기반 업서트(idempotent upsert)

### 2.3 적재(Load)

- 정제본을 DB의 clean 테이블에 적재
- 분석/대시보드용 mart_hourly, mart_daily 생성

### 2.4 데이터 품질(Data Quality)

최소 3종 룰을 적용합니다.

1. **Freshness(신선도)**: 최신 데이터가 일정 시간 이상 지연되면 경고
2. **Missing interval(누락)**: 5분/15분 간격이 끊긴 구간 탐지
3. **Range check(범위)**: 주요 지표가 비정상 범위면 경고/실패

### 2.5 운영/재처리

- 실행 로그(성공/실패/처리량/지연시간) 기록
- 특정 기간 백필(Backfill) 가능(예: 어제/지난주 데이터를 다시 수집·적재)

---

## 3. 기술 스택 (v1)

- **Language**: Python
- **Storage (RAW)**: 파일 저장소(Local)
  - `data/raw/...`에 날짜 파티션 형태로 저장
- **Database (CLEAN/MART)**: PostgreSQL (Docker 기반 권장)
- **Scheduling**: 로컬 스케줄러(Windows 작업 스케줄러 / Linux cron)
  - 추후 Airflow/Prefect로 확장 가능
- **Visualization (Optional)**: Metabase / Grafana / Redash 중 택1

**v2 확장**: BigQuery(GCP) / S3+Glue+Athena(AWS) / Azure Blob+ADF(Function)로 이식

### 3.1 기술 스택 라이선스 정보

본 프로젝트에서 사용하는 주요 기술 스택의 라이선스 및 비용 정보입니다.

#### 3.1.1 Apache Kafka

- **무료 (자체 구축)**: Apache Kafka는 오픈소스(Apache License 2.0)로 직접 설치/운영 시 무료
  - 공식 사이트: https://kafka.apache.org
- **유료가 생기는 경우**:
  - Confluent Cloud 같은 Kafka 매니지드 서비스
  - AWS MSK / Azure Event Hubs(Kafka 호환) / GCP 매니지드 스트리밍 등 클라우드에서 "운영까지 맡기는" 형태

#### 3.1.2 Apache Spark

- **무료 (자체 구축)**: Apache Spark는 Apache License 2.0 기반 오픈소스로 직접 운영 시 무료
  - 공식 사이트: https://spark.apache.org
- **유료가 생기는 경우**:
  - Databricks 같은 Spark 기반 매니지드 플랫폼
  - AWS EMR / GCP Dataproc 같은 클라우드 매니지드 실행 환경

#### 3.1.3 MinIO

- **무료 (자체 구축)**: MinIO는 오픈소스(AGPLv3)로 사용 가능
  - 공식 사이트: https://min.io
- **주의사항**: MinIO는 듀얼 라이선스(AGPL + Commercial) 모델
  - 포트폴리오/개인 프로젝트로 로컬에서 사용하는 것은 보통 문제 없음
  - 서비스 형태로 외부에 제공 + 수정/결합 시 AGPL 의무(소스 공개 등) 이슈 발생 가능
  - 상업용/엔터프라이즈 요구사항에 따라 유료 구독(서포트/상용 라이선스) 필요

#### 3.1.4 PostgreSQL

- **무료 (자체 구축)**: PostgreSQL은 PostgreSQL License(퍼미시브)로 직접 운영 시 무료
  - 공식 사이트: https://www.postgresql.org
- **유료가 생기는 경우**:
  - AWS RDS / GCP Cloud SQL / Azure Database for PostgreSQL 같은 매니지드 DB 서비스

#### 3.1.5 Metabase

- **무료 (자체 구축)**: Metabase는 오픈소스 에디션이 있고 AGPLv3 기반
  - GitHub: https://github.com/metabase/metabase
- **유료가 생기는 경우**:
  - Metabase Cloud / Pro / Enterprise 같은 유료 플랜(운영/고급 기능/관리)

#### 3.1.6 Apache Airflow

- **무료 (자체 구축)**: Apache Airflow는 Apache License 2.0 오픈소스로 자체 운영 시 무료
  - 공식 사이트: https://airflow.apache.org
- **유료가 생기는 경우**:
  - AWS MWAA (Managed Workflows for Apache Airflow) / GCP Cloud Composer / Azure 매니지드 워크플로우 같은 매니지드 오케스트레이션 서비스

**요약**: "내가 서버에 직접 띄우면 무료", "클라우드로 편하게 쓰면 유료" 형태입니다.

---

## 4. 데이터 레이어 설계

### 4.1 RAW Layer (원본 보존)

- **목적**: 재현 가능성(재처리/백필), 스키마 변경 대응, 원본 감사(Audit)
- **저장 형태**: XML 원문 파일
- **예시 경로**: `data/raw/kpx/dt=YYYY-MM-DD/HHMM.xml`

### 4.2 CLEAN Layer (정제/표준화)

- **목적**: 분석/조인을 위한 "신뢰 가능한 단일 소스"
- **특징**:
  - 고유키(예: 기준시각) 기반 중복 방지
  - 타입 정리, 컬럼 표준화
  - 주요 파생값(예: 예비력, 부하율)은 view 또는 mart에서 생성

### 4.3 MART Layer (대시보드/리포트 최적화)

- **목적**: 대시보드가 복잡한 계산 없이 바로 조회 가능
- **예시**:
  - `mart_power_hourly`: 시간 단위 집계
  - `mart_power_daily`: 일 단위 요약

---

## 5. DB 모델(개념)

실제 컬럼명은 KPX 응답 XML 필드에 맞춰 매핑합니다.  
아래는 "전력수급 시계열"에서 일반적으로 쓰는 최소 컬럼 세트입니다.

### 5.1 clean 테이블 예시

**테이블**: `clean_power_supply`

**핵심 키**:
- `base_datetime` (기준 시각) — UNIQUE 또는 PK 권장

**주요 지표(예시)**:
- `demand_mw` (수요)
- `supply_mw` (공급 또는 공급능력)
- `reserve_mw` (예비력)
- `reserve_rate` (예비율)
- `raw_file_path` (원문 파일 경로, 추적용)
- `ingested_at` (적재 시각)

### 5.2 mart_hourly 예시

시간 기준(hour)으로 집계

**지표 예시**:
- 평균 수요/공급
- 최대 수요(피크)
- 최저 예비율
- 위험 구간 카운트(예: 예비율 임계치 미만 횟수)

### 5.3 mart_daily 예시

일 기준(day)으로 요약

**지표 예시**:
- 일 피크 수요
- 일 최저 예비율
- 위험 구간 총합
- 데이터 누락/지연 요약(품질 리포트용)

---

## 6. View는 왜 쓰나?

View는 "테이블이 아니라 자주 쓰는 SQL 로직을 이름 붙여 표준화"한 것입니다.

- **예**: `v_power_supply_features`
- 예비력, 부하율 같은 파생값 계산을 한 곳에서 통일
- 사용자/대시보드가 매번 계산 실수하지 않게 방지

데이터량이 작으면 view만으로도 충분하고, 대시보드가 느려지면 mart로 굳히는 방식이 일반적입니다.

---

## 7. 데이터 품질 규칙 (v1 최소 셋)

### 7.1 Freshness(신선도)

- 최신 `base_datetime`이 현재 시각 대비 일정 시간 이상 뒤처지면 경고

### 7.2 Missing interval(누락)

- 기대 간격(5분/15분)이 끊긴 구간 탐지
- "누락이 0이 되게"가 아니라, 누락을 탐지하고 리포트/알림하는 것이 목표

### 7.3 Range check(범위)

- 예: 예비율/수요/공급이 비정상 범위면 경고 또는 실패 처리

---

## 8. 실행 흐름 (로컬 v1)

### 8.1 환경 준비

1. 공공데이터 API 키 발급/승인 확인
2. 로컬 DB(Postgres) 준비(권장: Docker)
3. 프로젝트 환경변수 설정(API Key, DB 접속 정보 등)

#### 8.1.1 API 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 내용을 입력하세요:

```env
# KPX 전력수급 API 설정
API_URL=https://openapi.kpx.or.kr/openapi/sukub5mMaxDatetime/getSukub5mMaxDatetime
API_KEY=your_api_key_here
```

**설정 가이드:**
- `API_URL`: KPX API 엔드포인트 전체 URL (프로토콜 포함)
  - 예: `https://openapi.kpx.or.kr/openapi/sukub5mMaxDatetime/getSukub5mMaxDatetime`
- `API_KEY`: 공공데이터포털(https://www.data.go.kr)에서 발급받은 인증키
  - 포털에서 제공하는 Encoding/Decoding 키 사용 권장
  - 코드는 자동으로 `?serviceKey=` 쿼리 파라미터로 추가합니다

**참고:** `.env.example` 파일을 참고하여 복사 후 사용할 수 있습니다.

### 8.1.2 Docker로 RAW 수집 실행

`.env` 파일 설정 후 아래 명령으로 15분 주기 수집을 실행합니다. 수집 결과는 `data_collect/data/raw/kpx/dt=YYYY-MM-DD/HHMM.xml`에 저장됩니다.

```
docker compose up -d --build
```

중지:

```
docker compose down
```

### 8.2 1회 수동 실행으로 end-to-end 확인

```
API 호출 → RAW 저장 → 파싱 → CLEAN 적재 → MART 생성 → 품질 체크 로그 확인
```

### 8.3 스케줄링 적용

- 5분/15분마다 ingest 작업 실행
- 실패 시 재시도 정책과 로그 확인

---

## 9. 프로젝트 구조(권장)

```
src/
  ingest/      : API 호출, 원문 저장
  transform/   : XML 파싱, 정제 규칙
  load/        : DB 적재(업서트), mart 생성
  dq/          : 데이터 품질 체크
  utils/       : 공통 유틸, 로깅

data/
  raw/         : XML 원문 저장
  logs/        : 실행 로그

docs/
  아키텍처 설명, 테이블 정의, 품질 규칙 문서

README.md
```

---

## 10. 포트폴리오에서 강조할 포인트(면접/자소서용)

이 프로젝트는 아래 항목을 증명합니다.

1. ✅ **RAW 원문 보존을 통한 재현 가능성**
2. ✅ **idempotent upsert로 중복/재실행 안정성**
3. ✅ **누락/지연/범위 체크 기반 데이터 품질 관리**
4. ✅ **clean → mart 분리로 분석/대시보드 친화적 모델링**
5. ✅ **스케줄링/로깅으로 운영 가능한 파이프라인 구성**

---

## 11. 로드맵

### v1 (현재)

- [x] 로컬 환경에서 end-to-end 파이프라인 완주
- [ ] Postgres 기반 clean/mart
- [ ] DQ 최소 3종 + 로그

### v2 (운영형 수집 아키텍처)

백필이 불가능한 OpenAPI 특성상, 수집 가용성을 확보하는 것이 가장 중요합니다.

- **Scheduler**: GCP Cloud Scheduler로 24/7 주기 실행
- **Collector**: Cloud Run (또는 Cloud Functions)에서 수집 실행
- **RAW**: GCS(또는 MinIO)로 원문 XML 보존
- **CLEAN**: PostgreSQL 적재 (기준시각 unique + idempotent upsert)
- **MART**: Airflow에서 하루 1회 정제/집계 잡 실행
- **BI**: Metabase에서 mart 테이블 대시보드 연결

효과:

- 컴퓨터가 꺼져도 수집 지속
- 파싱 실패/장애에도 원본 보존
- 중복/재시도에도 데이터 안정성 확보
- 누락 감지 및 기록 가능
- **보존정책**: GCS 라이프사이클 규칙으로 RAW 30일 보관

### v3 (실시간/스트리밍 확장)

- [ ] Producer/Consumer 분리(큐 기반)
- [ ] Kafka/Flink/Spark 중 1개 도입(선택)

---

## 12. 주의사항

- 본 프로젝트는 학습/포트폴리오 목적입니다.
- 공공 API 정책(호출 제한/약관)을 준수합니다.

---

## 13. 다음 단계

다음 정보를 제공해주시면 스키마를 "확정"하여 완성본으로 업데이트하겠습니다.

1. **샘플 응답 XML 일부(20~40줄)**
2. **실제 주기가 5분인지** (설명에 5분 단위라 되어 있었음)
3. **핵심 지표로 어떤 걸 대시보드에 보여주고 싶은지**
   - 예: 예비율, 피크 수요, 위험구간

이 3개 정보를 바탕으로 README의 "테이블/지표/품질룰"을 실제 필드명 기반으로 완성본으로 업데이트하겠습니다.

---
