"""
LLM 유틸리티 모듈
Ollama API 호출을 위한 공통 함수들을 정의합니다.
재시도 로직과 Chain of Thought (Thinking) 지원이 추가되었습니다.
"""
import httpx
import json
import asyncio
from typing import List, Dict, Any, Optional, Callable


async def call_llm(
    ollama_host: str,
    model: str,
    messages: List[Dict[str, Any]],
    temperature: float = 0.1,
    num_predict: int = 1024,
    timeout: float = 60.0
) -> Dict[str, Any]:
    """
    Ollama LLM API를 호출하여 응답을 받아옵니다. (기본 호출)
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": num_predict
                }
            }

            response = await client.post(
                f"{ollama_host}/api/chat",
                json=payload
            )
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        print(f"[LLM] API 호출 실패: {e}")
        raise


async def call_llm_with_retry(
    ollama_host: str,
    model: str,
    messages: List[Dict[str, Any]],
    validator: Callable[[str], bool],
    max_retries: int = 2,
    temperature: float = 0.1
) -> str:
    """
    Ollama API를 호출하되, 검증 실패 시 재시도합니다.
    검증 로직(validator)을 통과할 때까지 최대 max_retries만큼 반복합니다.
    
    Args:
        ollama_host: 호스트 URL
        model: 모델명
        messages: 메시지 목록
        validator: 응답 텍스트를 입력받아 유효성(True/False)을 반환하는 함수
        max_retries: 최대 재시도 횟수
        temperature: 초기 온도값 (재시도 시 약간씩 증가)

    Returns:
        str: 최종 응답 텍스트 (실패 시 마지막 응답 반환)
    """
    last_response = ""
    current_temp = temperature

    for attempt in range(max_retries + 1):
        try:
            print(f"[LLM] 시도 {attempt + 1}/{max_retries + 1} (Temp: {current_temp})")
            
            response_json = await call_llm(
                ollama_host, 
                model, 
                messages, 
                temperature=current_temp
            )
            content = response_json.get("message", {}).get("content", "")
            last_response = content

            if validator(content):
                return content
            
            print(f"[LLM] 검증 실패. 재시도합니다...")
            
            # 재시도 시 Temperature를 약간 높여서 다른 응답 유도
            current_temp = min(current_temp + 0.2, 1.0)
            
            # 이전 실패 내용을 컨텍스트에 추가하여 수정 유도 (선택적 구현)
            # 여기서는 단순히 다시 시도만 함.
            
            await asyncio.sleep(1) # API 부하 방지

        except Exception as e:
            print(f"[LLM] 호출 중 에러: {e}")
            await asyncio.sleep(1)

    print("[LLM] 최대 재시도 횟수 초과. 마지막 응답을 반환합니다.")
    return last_response
