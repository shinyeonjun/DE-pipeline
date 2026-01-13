"""
Step 1.5: 엔티티 정규화 (Entity Normalization)
사용자 입력값(한국어 등)을 DB에서 사용하는 정확한 값(영어)으로 변환합니다.
LLM을 사용하여 동적으로 매핑을 수행합니다.
"""
import json
from typing import Dict, Any, List
from ..utils.llm import call_llm

# ==========================================
# 상수 정의 (Constants)
# ==========================================

VALID_CATEGORIES = [
    "Gaming", "Music", "Entertainment", "Sports", "News & Politics",
    "Science & Technology", "Education", "Film & Animation",
    "People & Blogs", "Comedy", "Howto & Style", "Pets & Animals",
    "Autos & Vehicles", "Travel & Events", "Nonprofits & Activism"
]

# ==========================================
# 헬퍼 함수 (Pure Functions)
# ==========================================

def is_english(text: str) -> bool:
    """
    텍스트가 영어인지 확인합니다. (간단한 휴리스틱)
    
    Args:
        text: 확인할 텍스트

    Returns:
        bool: 영어 여부 (True/False)
    """
    if not text:
        return True
    
    # ASCII 범위 내 알파벳 비중 확인
    english_chars = sum(1 for c in text if c.isascii() and c.isalpha())
    return english_chars / max(len(text.replace(" ", "")), 1) > 0.7


def needs_normalization(analysis: Dict[str, Any]) -> bool:
    """
    정규화가 필요한지 확인합니다.
    
    Args:
        analysis: Step 1 분석 결과
    
    Returns:
        bool: 정규화 필요 여부
    """
    entities = analysis.get("entities", {})
    filters = analysis.get("filters", [])
    
    # 카테고리 엔티티가 있고 영어가 아닌 경우
    category = entities.get("category", "")
    if category and not is_english(category):
        return True
    
    # 필터 중 카테고리 필터가 있고 영어가 아닌 경우
    for f in filters:
        if f.get("field") == "카테고리":
            value = f.get("value", "")
            if value and not is_english(value):
                return True
    
    return False


# ==========================================
# 메인 함수 (Async Function)
# ==========================================

async def normalize_entities(
    analysis: Dict[str, Any],
    ollama_host: str,
    model: str
) -> Dict[str, Any]:
    """
    엔티티와 필터 값을 DB 호환 형식으로 정규화합니다.

    Args:
        analysis: Step 1 분석 결과
        ollama_host: Ollama 호스트 URL
        model: 사용할 모델명

    Returns:
        Dict[str, Any]: 정규화된 분석 결과
    """
    # 정규화 필요 여부 확인
    if not needs_normalization(analysis):
        print("[Step1.5] 정규화 불필요 - 스킵")
        return analysis

    print("[Step1.5] 엔티티 정규화 시작...")

    entities = analysis.get("entities", {})
    filters = analysis.get("filters", [])

    # 정규화할 값 수집
    values_to_normalize = []
    
    if entities.get("category"):
        values_to_normalize.append({
            "type": "category",
            "original": entities["category"]
        })
    
    for i, f in enumerate(filters):
        if f.get("field") == "카테고리" and f.get("value"):
            values_to_normalize.append({
                "type": "filter_category",
                "index": i,
                "original": f["value"]
            })

    if not values_to_normalize:
        return analysis

    # LLM 프롬프트 구성
    prompt = f"""당신은 YouTube 카테고리 이름을 정규화하는 전문가입니다.

사용자가 입력한 값을 YouTube API가 사용하는 정확한 영어 카테고리명으로 변환해주세요.

## 사용 가능한 YouTube 카테고리 목록:
{json.dumps(VALID_CATEGORIES, ensure_ascii=False)}

## 변환이 필요한 값:
{json.dumps([v['original'] for v in values_to_normalize], ensure_ascii=False)}

## 응답 형식 (JSON):
{{
    "mappings": [
        {{"original": "게임", "normalized": "Gaming"}},
        {{"original": "음악", "normalized": "Music"}}
    ]
}}

위 형식으로 각 입력값에 대한 정규화된 값을 JSON으로 반환하세요.
목록에 없는 카테고리는 가장 유사한 것으로 매핑하세요."""

    try:
        messages = [
            {"role": "system", "content": "JSON만 출력하세요. 설명 없이 JSON만 반환하세요."},
            {"role": "user", "content": prompt}
        ]

        # LLM 호출
        response = await call_llm(ollama_host, model, messages, temperature=0.1)
        content = response.get("message", {}).get("content", "")

        # JSON 추출
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)
        mappings = {m["original"]: m["normalized"] for m in result.get("mappings", [])}

        print(f"[Step1.5] 매핑 결과: {mappings}")

        # 매핑 적용
        for item in values_to_normalize:
            original = item["original"]
            normalized = mappings.get(original, original)

            if item["type"] == "category":
                analysis["entities"]["category"] = normalized
                print(f"[Step1.5] Entity 변환: {original} -> {normalized}")
                
            elif item["type"] == "filter_category":
                idx = item["index"]
                analysis["filters"][idx]["value"] = normalized
                print(f"[Step1.5] Filter 변환: {original} -> {normalized}")

        return analysis

    except Exception as e:
        print(f"[Step1.5] 정규화 실패, 원본 유지: {e}")
        return analysis
