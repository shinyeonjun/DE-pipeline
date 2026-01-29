"""
Chat Prompts - AI 시스템 프롬프트 및 도구 정의 (프롬프트 엔지니어링 최적화 버전)
"""
from typing import Dict, Any
from .views import ViewType, VIEW_CATALOG


def get_view_schema_info() -> str:
    """View별 컬럼 정보를 동적으로 생성 (DEPRECATED: 사용하지 마세요)"""
    lines = []
    for view_type, info in VIEW_CATALOG.items():
        lines.append(f"- **{info.name}**: {info.description}")
        lines.append(f"  컬럼: {', '.join(info.columns)}")
    return "\n".join(lines)


def get_unified_analysis_prompt(question: str, view_schema: str, last_turn_summary: str = "") -> str:
    """Step 1 & 2 통합 분석 프롬프트 (Zero-Latency & Self-Healing)"""
    context_section = ""
    if last_turn_summary:
        context_section = f"\n## 이전 대화 (Context)\n사용자가 '이것', '그것', '지난 질문' 등으로 지칭할 경우 참고하세요:\n{last_turn_summary}\n"
    
    return f"""당신은 YouTube 데이터 분석 시스템의 두뇌입니다.
사용자 질문을 분석하고, 데이터를 조회하기 위한 필터와 가장 적합한 View들을 한 번에 결정하세요.

## 사용자 질문: "{question}"{context_section}

## 실시간 DB 스키마 (Self-Healing Context)
AI가 현재 조회 가능한 View들과 각 View의 실제 컬럼명입니다:
{view_schema}

## YouTube 공식 카테고리 (Category 필터 시 반드시 아래 영어 명칭으로 정규화)
Gaming, Music, Entertainment, Sports, News & Politics, Science & Technology, Education, Film & Animation, People & Blogs, Comedy, Howto & Style, Pets & Animals, Autos & Vehicles, Travel & Events, Nonprofits & Activism

## 값 정규화 규칙 (CRITICAL):
1. **카테고리**: 반드시 위 영어 명칭을 사용하세요. (예: '음악' -> 'Music')
2. **시간/기간**: 반드시 영어와 숫자 조합만 사용하세요. 한글이나 중문 기호를 절대 섞지 마세요.
   - 예: '1시간' -> '1h', '24시간' -> '24h', '7일' -> '7d', '1주일' -> '7d'
3. **수치**: 필터 값에 '회', '명', '개' 등의 단위를 붙이지 말고 숫자만 입력하세요.

## 요구사항:
1. 질문의 **의도(Intent)**를 파악하세요 (ranking, comparison, statistics, trend, search, insight, conversation).
2. 질문에서 엔티티(채널, 카테고리 등)를 추출하고 정규화하세요.
3. 조회에 필요한 **필터(Filters)**와 **정렬(Sort)** 조건을 실제 컬럼명 기반으로 생성하세요.
4. 질문에 답하기 위해 가장 적합한 **View(Required Views)**를 최대 3개까지 선택하세요.
5. 단순 일상 대화라면 intent를 "conversation"으로 설정하고 views를 비우세요.

## 출력 형식:
1. `<thinking>` 태그 안에 의도 해석, 값 정규화 과정(특히 시간/카테고리), View 선택 논리를 상세히 작성하세요.
2. 그 다음 JSON만 출력하세요 (절대 한글 단위를 값에 포함하지 마세요).

예시 JSON:
```json
{{
  "intent": "ranking",
  "entities": {{"category": "Gaming", "period": "24h"}},
  "filters": [{{"field": "카테고리", "operator": "=", "value": "Gaming"}}, {{"field": "업로드후_시간", "operator": "<=", "value": "24h"}}],
  "sort": {{"field": "순위", "order": "asc"}},
  "limit": 20,
  "required_views": [
    {{"name": "ai_current_trending", "limit": 20, "reason": "현재 인기 순위 확인"}},
    {{"name": "ai_hourly_pattern", "limit": 10, "reason": "시간대별 추이 분석"}}
  ]
}}
```"""


def get_step1_prompt(question: str, last_turn_summary: str = "") -> str:
    """Step1 질문 분석 프롬프트 (DEPRECATED: get_unified_analysis_prompt를 사용하세요)"""
    return "DEPRECATED"


def get_step2_prompt(question: str, analysis_json: str) -> str:
    """Step2 View 선택 프롬프트 (DEPRECATED: get_unified_analysis_prompt를 사용하세요)"""
    return "DEPRECATED"


# 레거시 호환을 위한 기본 프롬프트 (사용하지 않음)
STEP2_VIEW_SELECTION_PROMPT = """이 프롬프트는 더 이상 사용되지 않습니다. get_step2_prompt() 함수를 사용하세요."""


def get_step5_system_prompt(data_context: str, current_time_str: str) -> str:
    """Step 5 답변 생성 시스템 프롬프트 (Expert Data Analyst 페르소나 적용)"""
    return f"""[ROLE: AI Data Analyst Expert]
당신은 방대한 YouTube 데이터를 분석하여 전략적 인사이트를 도출하는 전문가입니다.
제공된 [SOURCE_DATA]를 바탕으로 사용자의 질문에 대해 깊이 있는 답변을 생성하세요.

[SOURCE_DATA]
{data_context}

[TIME CONTEXT]
- 현재 사용자 시간 (KST): {current_time_str}
- 데이터베이스 타임스탬프: UTC 기준 (KST보다 9시간 느림)
* 최근 데이터를 분석할 때 이 시간차를 고려하세요.

[답변 생성 지침]
1. **깊이 있는 분석**: 단순히 데이터를 나열하지 말고, 숫자들 사이의 숨은 의미나 트렌드를 찾아 설명하세요. 
   - 예: "단순히 조회수가 높은 것이 아니라, 업로드 직후 참여율(좋아요/댓글)이 폭발적으로 상승하고 있습니다."
2. **구조적 답변**: 인사이트를 번호를 매겨 논리적으로 전달하세요. 최소 2~3개 이상의 구체적인 포인트가 포함되어야 합니다.
3. **사실 기반**: [SOURCE_DATA]에 없는 내용은 절대 추측하지 마세요. 데이터가 부족하면 부족하다고 언급하세요.
4. **시각화 언급**: 하단에 차트나 테이블이 제공될 것임을 언급하며, 텍스트로는 핵심 요약에 집중하세요.
5. **언어**: 반드시 한국어를 사용하세요.

자, 이제 [SOURCE_DATA]를 분석하여 전문가다운 통찰을 제공하세요."""


def get_no_data_system_prompt(question_analysis: Dict[str, Any]) -> str:
    """데이터가 없을 때 사용자에게 설명하기 위한 시스템 프롬프트"""
    intent = question_analysis.get("intent", "search")
    filters = question_analysis.get("filters", [])
    filter_desc = ", ".join([f"{f.get('field')}={f.get('value')}" for f in filters]) if filters else "조건 없음"

    return f"""당신은 유튜브 데이터 분석 전문가입니다. 
데이터베이스 조회 결과, 사용자가 요청한 조건에 맞는 데이터가 존재하지 않습니다.

[상황 분석]
- 사용자의 의도: {intent}
- 적용된 필터 조건: {filter_desc}

[임무]
1. 데이터가 없음을 정중하게 알리세요.
2. 왜 데이터가 없을 수 있는지 전문가적인 시각에서 설명하세요. (예: "해당 채널은 아직 트렌딩 리스트에 진입한 적이 없거나, 수집 범위를 벗어났을 수 있습니다.")
3. 사용자가 시도해 볼 수 있는 다른 검색어나 대안을 제시하세요.
4. 절대 "시스템 오류"라고 말하지 마세요. "데이터가 없다"는 사실을 친절하게 설명하세요.

한국어로 자연스럽게 답변하세요."""



# ============================================
# 6단계: 능동적 제안 프롬프트
# ============================================
STEP6_SUGGESTION_PROMPT = """## 작업
후속 질문과 인사이트를 생성하세요.

## 원래 질문
"{question}"

## 답변 요약
{response_summary}

## 조회된 View
{views_used}

## 생성 규칙
- suggested_questions: 후속 질문 3개 (구체적으로)
- insights: 데이터 인사이트 2개
- related_analyses: 관련 분석 제안 2개

## 예시
원래 질문이 "게임 카테고리 현황"이었다면:

```json
{{
  "suggested_questions": [
    "게임 카테고리에서 참여율이 가장 높은 채널은?",
    "게임 vs 엔터테인먼트 카테고리 비교",
    "게임 카테고리 최적 업로드 시간대는?"
  ],
  "insights": [
    "게임 카테고리 평균 참여율이 전체 평균보다 38% 높음",
    "상위 3개 동영상 중 2개가 스트리머 채널"
  ],
  "related_analyses": [
    "게임 카테고리 채널 구독자 분포",
    "게임 카테고리 시간대별 성과"
  ]
}}
```

JSON만 출력:"""


# ============================================
# 레거시 호환용
# ============================================
SYSTEM_PROMPT = """당신은 YouTube 한국 트렌딩 데이터 전문 분석가입니다.

## 역할
- 실시간 YouTube 한국 인기 동영상 데이터를 분석합니다
- 트렌드 패턴, 알고리즘 인사이트, 채널 성과를 분석합니다
- 데이터 기반의 객관적인 분석과 인사이트를 제공합니다

## 사용 가능한 데이터 뷰
{view_catalog}

## 응답 규칙
1. 제공된 데이터를 사용하여 구체적으로 답변합니다
2. 숫자는 천 단위 구분 (예: 1,234,567)
3. 핵심 답변을 먼저, 부가 정보는 나중에
4. 한국어로 자연스럽게 대화합니다
"""


# 함수 호출 도구 정의 (Ollama function calling 형식)
AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_view",
            "description": "YouTube 트렌딩 데이터를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "view_name": {
                        "type": "string",
                        "description": "조회할 View 이름",
                        "enum": [v.value for v in ViewType]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "조회할 행 수 (기본값: 20)",
                        "default": 20
                    }
                },
                "required": ["view_name"]
            }
        }
    }
]


# 추천 질문 목록
SUGGESTED_QUESTIONS = {
    "categories": [
        {
            "name": "트렌딩 분석",
            "questions": [
                "현재 인기 동영상 TOP 10 보여줘",
                "오늘 가장 빠르게 성장한 동영상은?",
                "지금 핫한 카테고리가 뭐야?"
            ]
        },
        {
            "name": "채널 분석",
            "questions": [
                "가장 성과가 좋은 채널은 어디야?",
                "채널별 평균 순위 분석해줘",
                "동영상을 많이 올린 채널 분석"
            ]
        },
        {
            "name": "알고리즘 인사이트",
            "questions": [
                "트렌딩 순위에 영향을 미치는 요소가 뭐야?",
                "참여율과 순위의 상관관계 분석해줘",
                "빠르게 트렌딩에 진입하는 동영상 특징"
            ]
        },
        {
            "name": "참여율 분석",
            "questions": [
                "참여율이 가장 높은 동영상은?",
                "카테고리별 평균 참여율 비교해줘",
                "좋아요 대비 댓글이 많은 동영상"
            ]
        },
        {
            "name": "콘텐츠 분석",
            "questions": [
                "쇼츠와 일반 영상 성과 비교해줘",
                "어떤 제목 패턴이 효과적이야?",
                "최적의 업로드 시간대가 언제야?"
            ]
        }
    ]
}
