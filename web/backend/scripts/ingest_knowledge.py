"""
Knowledge Base 인덱싱 스크립트
마크다운 문서들을 읽어서 청크로 분할하고, Supabase pgvector에 저장합니다.

사용법:
    cd web/backend
    python -m scripts.ingest_knowledge
"""
import os
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv

# .env 파일 경로 명시적 지정 (scripts 폴더의 상위 = backend 폴더)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Supabase 클라이언트 설정 (환경 변수 이름은 config.py와 동일)
SUPABASE_URL = os.getenv("supabase_url") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("supabase_service_key") or os.getenv("SUPABASE_KEY")
OLLAMA_HOST = os.getenv("ollama_host") or os.getenv("OLLAMA_HOST") or "http://localhost:11434"

if not SUPABASE_URL or not SUPABASE_KEY:
    print(f"[DEBUG] env_path: {env_path}")
    print(f"[DEBUG] env_path exists: {env_path.exists()}")
    raise ValueError("supabase_url and supabase_service_key must be set in .env")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Knowledge Base 경로
KNOWLEDGE_BASE_DIR = Path(__file__).parent.parent / "knowledge_base"


async def generate_embedding(text: str) -> list[float]:
    """Ollama nomic-embed-text로 임베딩 생성"""
    import httpx
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        # 최신 Ollama API: /api/embed (구버전: /api/embeddings)
        response = await client.post(
            f"{OLLAMA_HOST}/api/embed",
            json={
                "model": "nomic-embed-text",
                "input": text  # 최신 API는 'input' 사용
            }
        )
        response.raise_for_status()
        result = response.json()
        # 최신 API는 'embeddings' 배열 반환
        embeddings = result.get("embeddings", [])
        return embeddings[0] if embeddings else result.get("embedding", [])


def chunk_markdown(content: str, max_chunk_size: int = 800) -> list[dict]:
    """마크다운을 섹션 단위로 청크 분할"""
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_heading = ""
    
    for line in lines:
        if line.startswith('#'):
            # 이전 청크 저장
            if current_chunk:
                chunk_text = '\n'.join(current_chunk).strip()
                if chunk_text and len(chunk_text) > 50:  # 너무 짧은 청크 제외
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
        chunk_text = '\n'.join(current_chunk).strip()
        if chunk_text and len(chunk_text) > 50:
            chunks.append({
                "content": chunk_text,
                "heading": current_heading
            })
    
    return chunks


async def process_document(file_path: Path) -> int:
    """단일 문서 처리 및 저장"""
    print(f"\n📄 처리 중: {file_path.name}")
    
    content = file_path.read_text(encoding='utf-8')
    chunks = chunk_markdown(content)
    
    print(f"   청크 수: {len(chunks)}")
    
    inserted = 0
    for i, chunk in enumerate(chunks):
        print(f"   [{i+1}/{len(chunks)}] 임베딩 생성 중... ({len(chunk['content'])} chars)")
        
        try:
            embedding = await generate_embedding(chunk['content'])
            
            if not embedding:
                print(f"   ⚠️ 임베딩 생성 실패 (빈 결과)")
                continue
            
            # Supabase에 저장
            result = supabase.table("knowledge_embeddings").insert({
                "content": chunk['content'],
                "metadata": {
                    "source": file_path.name,
                    "heading": chunk['heading'],
                    "chunk_index": i
                },
                "embedding": embedding
            }).execute()
            
            inserted += 1
            print(f"   ✅ 저장 완료: {chunk['heading'][:30]}...")
            
        except Exception as e:
            print(f"   ❌ 오류: {e}")
    
    return inserted


async def clear_existing_embeddings():
    """기존 임베딩 삭제 (재인덱싱용)"""
    print("🗑️ 기존 임베딩 삭제 중...")
    try:
        supabase.table("knowledge_embeddings").delete().neq("id", 0).execute()
        print("   ✅ 삭제 완료")
    except Exception as e:
        print(f"   ⚠️ 삭제 실패 (테이블이 비어있을 수 있음): {e}")


async def main():
    """메인 실행 함수"""
    print("=" * 50)
    print("🚀 Knowledge Base 인덱싱 시작")
    print("=" * 50)
    
    # 기존 데이터 삭제 (옵션)
    await clear_existing_embeddings()
    
    # 마크다운 파일 목록
    md_files = list(KNOWLEDGE_BASE_DIR.glob("*.md"))
    
    if not md_files:
        print(f"⚠️ {KNOWLEDGE_BASE_DIR}에 마크다운 파일이 없습니다.")
        return
    
    print(f"\n📚 발견된 문서: {len(md_files)}개")
    for f in md_files:
        print(f"   - {f.name}")
    
    # 각 문서 처리
    total_inserted = 0
    for file_path in md_files:
        count = await process_document(file_path)
        total_inserted += count
    
    print("\n" + "=" * 50)
    print(f"✅ 인덱싱 완료! 총 {total_inserted}개 청크 저장됨")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
