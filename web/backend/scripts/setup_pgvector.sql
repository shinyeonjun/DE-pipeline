-- =========================================
-- RAG를 위한 Supabase pgvector 설정 스크립트
-- Supabase Dashboard > SQL Editor에서 실행하세요
-- =========================================

-- 1. pgvector 확장 활성화
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Knowledge Embeddings 테이블 생성
-- 768차원: nomic-embed-text 모델 사용
CREATE TABLE IF NOT EXISTS knowledge_embeddings (
    id BIGSERIAL PRIMARY KEY,
    
    -- 원본 텍스트 내용
    content TEXT NOT NULL,
    
    -- 메타데이터 (문서 출처, 카테고리 등)
    metadata JSONB DEFAULT '{}',
    
    -- 768차원 벡터 (Ollama nomic-embed-text)
    embedding vector(768),
    
    -- 타임스탬프
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()    
);

-- 3. 벡터 유사도 검색을 위한 인덱스 생성
-- IVFFlat: 대규모 벡터에서 빠른 근사 검색
CREATE INDEX IF NOT EXISTS knowledge_embeddings_embedding_idx 
ON knowledge_embeddings 
USING ivfflat (embedding vector_cosine_ops) 
WITH (lists = 100);

-- 4. 메타데이터 검색을 위한 GIN 인덱스
CREATE INDEX IF NOT EXISTS knowledge_embeddings_metadata_idx 
ON knowledge_embeddings 
USING GIN (metadata);

-- 5. 유사도 검색 함수 생성
CREATE OR REPLACE FUNCTION match_knowledge(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id bigint,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ke.id,
        ke.content,
        ke.metadata,
        1 - (ke.embedding <=> query_embedding) as similarity
    FROM knowledge_embeddings ke
    WHERE 1 - (ke.embedding <=> query_embedding) > match_threshold
    ORDER BY ke.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- 6. RLS(Row Level Security) 설정 (선택사항)
-- 공개 읽기 허용
ALTER TABLE knowledge_embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access" ON knowledge_embeddings
    FOR SELECT USING (true);

-- 인증된 사용자만 쓰기 허용 (필요시)
-- CREATE POLICY "Allow authenticated insert" ON knowledge_embeddings
--     FOR INSERT TO authenticated WITH CHECK (true);

-- =========================================
-- 확인 쿼리
-- =========================================
-- SELECT * FROM knowledge_embeddings LIMIT 5;
-- SELECT count(*) FROM knowledge_embeddings;
