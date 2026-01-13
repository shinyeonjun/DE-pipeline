# YouTube Analytics AI - Frontend

AI 기반 데이터 분석 플랫폼 프론트엔드

## 🚀 기술 스택

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **UI Components**: shadcn/ui

## 📁 프로젝트 구조

```
src/
├── app/                    # Next.js App Router 페이지
│   ├── page.tsx           # 홈 (AI 분석)
│   ├── trending/          # 트렌딩 분석
│   └── layout.tsx         # 루트 레이아웃
├── components/            # 재사용 가능한 컴포넌트
│   ├── common/           # 공통 컴포넌트 (Header, Sidebar)
│   ├── skeletons/        # 로딩 스켈레톤
│   └── ui/               # shadcn/ui 컴포넌트
├── hooks/                # 커스텀 훅
│   ├── use-loading.ts    # 로딩 상태 관리
│   └── use-sidebar-state.ts  # 사이드바 상태 관리
├── lib/                  # 유틸리티 함수
│   ├── formatters.ts     # 숫자, 날짜 포맷팅
│   ├── constants.ts      # 상수 (카테고리 매핑 등)
│   ├── performance.ts    # 성능 최적화 유틸
│   └── utils.ts          # 기타 유틸리티
├── data/                 # Mock 데이터 (API 연결 전)
│   ├── mock-videos.ts
│   ├── mock-analytics.ts
│   └── mock-insights.ts
└── types/                # TypeScript 타입 정의
    └── index.ts
```

## 🎯 주요 기능

### 1. AI 분석 센터 (`/`)
- 자연어 기반 데이터 쿼리
- 시계열 차트 시각화
- 자동 인사이트 생성
- 실시간 대시보드

### 2. 트렌딩 분석 (`/trending`)
- 영상 순위 & 성장 추이
- 카테고리별 필터링
- Velocity 추적
- 24시간 예측

## ⚡ 최적화

### 빌드 최적화
- **Gzip/Brotli 압축** 활성화
- **코드 스플리팅**: 차트 라이브러리, UI 컴포넌트 분리
- **Tree Shaking**: 사용하지 않는 코드 제거
- **이미지 최적화**: AVIF, WebP 포맷

### 런타임 최적화
- **스켈레톤 UI**: 로딩 상태 표시
- **Lazy Loading**: 페이지별 동적 로딩
- **localStorage**: 사용자 설정 캐싱
- **Debounce/Throttle**: 이벤트 핸들러 최적화

## 🛠️ 개발

### 설치
```bash
npm install
```

### 개발 서버 실행
```bash
npm run dev
```

### 빌드
```bash
npm run build
```

### 프로덕션 실행
```bash
npm start
```

### 번들 분석
```bash
npm run build
# 번들 크기 확인: .next/analyze/
```

## 📊 성능 지표

### 목표
- **LCP** (Largest Contentful Paint): < 2.5s
- **FID** (First Input Delay): < 100ms
- **CLS** (Cumulative Layout Shift): < 0.1
- **First Load JS**: < 200KB

### 최적화 기법
1. **이미지 최적화**: Next.js Image 컴포넌트 사용
2. **폰트 최적화**: next/font 사용
3. **CSS 최적화**: Tailwind CSS JIT 모드
4. **JS 최적화**: Code splitting, Tree shaking

## 🔄 API 연결

현재는 Mock 데이터를 사용하고 있습니다. 실제 API 연결 시:

1. `.env.production` 파일에 API URL 설정
2. `src/data/` 폴더의 Mock 데이터를 API 호출로 교체
3. `src/hooks/use-loading.ts`를 실제 데이터 fetching 훅으로 교체

```typescript
// 예시: useVideos.ts
export function useVideos() {
  const [data, setData] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetch('/api/videos')
      .then(res => res.json())
      .then(setData)
      .finally(() => setIsLoading(false));
  }, []);

  return { data, isLoading };
}
```

## 📝 코드 스타일

- **ESLint**: 코드 품질 검사
- **Prettier**: 코드 포맷팅 (자동)
- **TypeScript**: 타입 안전성

## 🚀 배포

### Vercel (권장)
```bash
vercel deploy
```

### Docker
```bash
docker build -t youtube-analytics-ai .
docker run -p 3000:3000 youtube-analytics-ai
```

## 📄 라이선스

MIT License
