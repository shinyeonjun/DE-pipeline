"""
텍스트 유틸리티 모듈
문자열 처리, JSON 추출, Thinking 로그 추출 등 공통 기능을 정의합니다.
"""
import re

def extract_json(content: str) -> str:
    """
    LLM 응답 텍스트에서 JSON 부분만 추출합니다.
    Markdown 코드 블록(```json ... ```) 또는 중괄호 매칭을 처리합니다.
    """
    original_content = content
    
    # ```json ... ``` 처리
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        parts = content.split("```")
        if len(parts) >= 2:
            content = parts[1].strip()
            if content.startswith("json"):
                content = content[4:].strip()

    # 중괄호 균형 맞추기
    if "{" in content:
        start = content.find("{")
        brace_count = 0
        end = start
        for i in range(start, len(content)):
            if content[i] == "{":
                brace_count += 1
            elif content[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    end = i + 1
                    break
        if end > start:
            content = content[start:end]
            return content
            
    # JSON 추출 실패 시, 혹시 원본이 이미 JSON일 수 있음 (하지만 보통 텍스트 섞여옴)
    # 일단 안전하게 원본 반환 시도 안함 (빈 문자열이 나을 수도, 호출측에서 에러 처리)
    return content


def extract_thinking(content: str) -> str:
    """
    LLM 응답에서 <thinking>...</thinking> 태그 사이의 내용을 추출합니다.
    태그가 없으면 빈 문자열을 반환합니다.
    """
    # 대소문자 무시, .은 개행 포함
    match = re.search(r"<thinking>(.*?)</thinking>", content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""
