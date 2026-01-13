"""
Step 3 RAG: Knowledge Retrieval (AI 기반 하이브리드 검색)
- AI 키워드 추출
- 벡터 유사도 + 키워드 매칭 + 텍스트 검색 병렬
"""
import json
from typing import Dict, Any, List
from app.core import supabase
from ..utils.llm import call_llm
from ..utils.embeddings import generate_embedding


async def extract_keywords_ai(
    question: str,
    ollama_host: str,
    model: str
) -> List[str]:
    """
    AI를 사용하여 질문에서 핵심 검색 키워드를 추출합니다.
    하드코딩 없이 LLM이 동적으로 판단합니다.
    """
    system_prompt = """질문에서 검색에 사용할 핵심 키워드를 추출해주세요.

규칙:
1. 불용어(이, 가, 은, 는, 뭐야, 어떻게 등)는 제외
2. 약어(CTR, RPM, SEO)는 풀네임도 함께 추출
3. 동의어나 관련 용어도 포함
4. JSON 배열만 출력

예시:
Q: "CTR이 뭐야?"
A: ["CTR", "클릭률", "Click Through Rate"]

Q: "트렌딩 진입하려면?"
A: ["트렌딩", "진입", "인기 급상승", "바이럴"]

Q: "쇼츠 vs 일반 영상"
A: ["쇼츠", "Shorts", "일반 영상", "롱폼"]"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question}
    ]
    
    try:
        response = await call_llm(ollama_host, model, messages, temperature=0.1, num_predict=100)
        answer = response.get("message", {}).get("content", "[]")
        
        # JSON 배열 추출
        if "[" in answer and "]" in answer:
            start = answer.index("[")
            end = answer.rindex("]") + 1
            keywords = json.loads(answer[start:end])
            print(f"[Step3-RAG] AI 키워드: {keywords}")
            return keywords
    except Exception as e:
        print(f"[Step3-RAG] AI 키워드 추출 실패: {e}")
    
    return []


async def text_search_fallback(keywords: List[str], limit: int = 10) -> List[Dict]:
    """
    키워드 기반 텍스트 검색 (벡터 검색 보완용)
    """
    if not keywords:
        return []
    
    try:
        # ILIKE 검색으로 키워드 포함 문서 찾기
        query = supabase.table("knowledge_embeddings").select("*")
        
        # OR 조건으로 키워드 검색
        or_conditions = []
        for kw in keywords[:5]:  # 상위 5개 키워드만
            or_conditions.append(f"content.ilike.%{kw}%")
            or_conditions.append(f"metadata->>heading.ilike.%{kw}%")
        
        result = query.or_(",".join(or_conditions)).limit(limit).execute()
        
        docs = []
        for row in result.data or []:
            docs.append({
                "content": row.get("content", ""),
                "metadata": row.get("metadata", {}),
                "similarity": 0.9,  # 텍스트 매치는 높은 관련성
                "source": "text_search"
            })
        
        print(f"[Step3-RAG] 텍스트 검색: {len(docs)}개 문서")
        return docs
        
    except Exception as e:
        print(f"[Step3-RAG] 텍스트 검색 실패: {e}")
        return []


async def retrieve_knowledge(
    question: str,
    ollama_host: str,
    model: str = "qwen2.5-coder:7b-instruct",
    top_k: int = 5,
    threshold: float = 0.5
) -> Dict[str, Any]:
    """
    AI 기반 하이브리드 검색:
    1. AI로 키워드 추출
    2. 벡터 검색 + 텍스트 검색 병렬 실행
    3. 결과 병합 및 중복 제거
    """
    print(f"[Step3-RAG] AI 하이브리드 검색 시작: {question[:50]}...")
    
    try:
        # 1. AI 키워드 추출
        keywords = await extract_keywords_ai(question, ollama_host, model)
        
        # 2. 임베딩 생성
        print(f"[Step3-RAG] 질문 임베딩 생성 중...")
        query_embedding = await generate_embedding(question, ollama_host=ollama_host)
        
        if not query_embedding:
            # 임베딩 실패 시 텍스트 검색만
            print(f"[Step3-RAG] 임베딩 실패, 텍스트 검색만 사용")
            text_docs = await text_search_fallback(keywords, top_k)
            return {"documents": text_docs, "count": len(text_docs), "thinking": "텍스트 검색 only"}
        
        # 3. 벡터 검색
        print(f"[Step3-RAG] 벡터 유사도 검색 중...")
        vector_result = supabase.rpc(
            "match_knowledge",
            {
                "query_embedding": query_embedding,
                "match_threshold": threshold,
                "match_count": top_k * 2
            }
        ).execute()
        
        vector_docs = []
        for doc in vector_result.data or []:
            vector_docs.append({
                "content": doc.get("content", ""),
                "metadata": doc.get("metadata", {}),
                "similarity": doc.get("similarity", 0),
                "source": "vector"
            })
        
        # 4. 텍스트 검색 (병렬)
        text_docs = await text_search_fallback(keywords, top_k)
        
        # 5. 결과 병합 (중복 제거, 텍스트 매치 우선)
        seen_content = set()
        merged_docs = []
        
        # 텍스트 검색 결과 먼저 (키워드 직접 매치)
        for doc in text_docs:
            content_key = doc["content"][:100]
            if content_key not in seen_content:
                seen_content.add(content_key)
                merged_docs.append(doc)
        
        # 벡터 검색 결과 추가
        for doc in vector_docs:
            content_key = doc["content"][:100]
            if content_key not in seen_content:
                seen_content.add(content_key)
                merged_docs.append(doc)
        
        # 유사도 순 정렬 후 상위 선택
        merged_docs.sort(key=lambda x: x["similarity"], reverse=True)
        final_docs = merged_docs[:top_k]
        
        # 6. 로깅
        print(f"[Step3-RAG] 최종 결과: {len(final_docs)}개 문서")
        for doc in final_docs:
            heading = doc.get("metadata", {}).get("heading", "N/A")[:30]
            source = doc.get("source", "unknown")
            print(f"   - {heading}... ({source}, 유사도: {doc['similarity']:.2f})")
        
        return {
            "documents": final_docs,
            "count": len(final_docs),
            "thinking": f"AI 키워드: {keywords}, 벡터: {len(vector_docs)}개, 텍스트: {len(text_docs)}개"
        }
        
    except Exception as e:
        print(f"[Step3-RAG] 검색 실패: {e}")
        return {"documents": [], "count": 0, "thinking": f"오류: {str(e)}"}


def format_rag_context(documents: List[Dict[str, Any]]) -> str:
    """검색된 문서들을 LLM 컨텍스트용 텍스트로 포맷팅합니다."""
    if not documents:
        return ""
    
    context_parts = []
    for i, doc in enumerate(documents, 1):
        source = doc.get("metadata", {}).get("source", "unknown")
        heading = doc.get("metadata", {}).get("heading", "")
        content = doc.get("content", "")
        
        context_parts.append(f"""
### 참고 문서 {i} (출처: {source})
{f"**{heading}**" if heading else ""}

{content}
""")
    
    return "\n---\n".join(context_parts)


