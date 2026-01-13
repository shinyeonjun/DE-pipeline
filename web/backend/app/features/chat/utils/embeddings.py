"""
Embeddings 유틸리티 - Ollama nomic-embed-text 모델을 사용한 텍스트 임베딩 생성
RAG 파이프라인에서 사용됩니다.
"""
import httpx
from typing import List, Optional
from app.core import settings


async def generate_embedding(
    text: str,
    model: str = "nomic-embed-text",
    ollama_host: Optional[str] = None
) -> List[float]:
    """
    텍스트를 벡터로 변환합니다.
    
    Args:
        text: 임베딩할 텍스트
        model: Ollama 임베딩 모델명 (기본: nomic-embed-text)
        ollama_host: Ollama 서버 주소
        
    Returns:
        768차원 float 리스트
    """
    host = ollama_host or settings.ollama_host
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 최신 Ollama API: /api/embed
        response = await client.post(
            f"{host}/api/embed",
            json={
                "model": model,
                "input": text  # 최신 API는 'input' 사용
            }
        )
        response.raise_for_status()
        result = response.json()
        
        # 최신 API는 'embeddings' 배열 반환
        embeddings = result.get("embeddings", [])
        return embeddings[0] if embeddings else result.get("embedding", [])


async def generate_embeddings_batch(
    texts: List[str],
    model: str = "nomic-embed-text",
    ollama_host: Optional[str] = None
) -> List[List[float]]:
    """
    여러 텍스트를 일괄 임베딩합니다.
    
    Args:
        texts: 임베딩할 텍스트 리스트
        model: Ollama 임베딩 모델명
        ollama_host: Ollama 서버 주소
        
    Returns:
        임베딩 벡터 리스트
    """
    embeddings = []
    for text in texts:
        embedding = await generate_embedding(text, model, ollama_host)
        embeddings.append(embedding)
    return embeddings


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[str]:
    """
    긴 텍스트를 청크로 분할합니다.
    
    Args:
        text: 분할할 텍스트
        chunk_size: 청크당 최대 문자 수
        overlap: 청크 간 겹침 문자 수
        
    Returns:
        청크 리스트
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # 단어 중간에서 자르지 않도록 조정
        if end < len(text):
            # 마지막 공백 위치 찾기
            last_space = text.rfind(' ', start, end)
            if last_space > start:
                end = last_space
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
    
    return chunks


def chunk_markdown(
    content: str,
    max_chunk_size: int = 800
) -> List[dict]:
    """
    마크다운 문서를 섹션 단위로 분할합니다.
    
    Args:
        content: 마크다운 텍스트
        max_chunk_size: 청크당 최대 문자 수
        
    Returns:
        [{"content": str, "heading": str}, ...] 형태의 리스트
    """
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_heading = ""
    
    for line in lines:
        # 헤딩 감지
        if line.startswith('#'):
            # 이전 청크 저장
            if current_chunk:
                chunk_text = '\n'.join(current_chunk).strip()
                if chunk_text:
                    # 청크가 너무 크면 추가 분할
                    if len(chunk_text) > max_chunk_size:
                        sub_chunks = chunk_text(chunk_text, max_chunk_size, 50)
                        for i, sc in enumerate(sub_chunks):
                            chunks.append({
                                "content": sc,
                                "heading": f"{current_heading} (Part {i+1})" if i > 0 else current_heading
                            })
                    else:
                        chunks.append({
                            "content": chunk_text,
                            "heading": current_heading
                        })
            
            current_heading = line.strip('#').strip()
            current_chunk = [line]
        else:
            current_chunk.append(line)
    
    # 마지막 청크 저장
    if current_chunk:
        chunk_text_final = '\n'.join(current_chunk).strip()
        if chunk_text_final:
            chunks.append({
                "content": chunk_text_final,
                "heading": current_heading
            })
    
    return chunks
