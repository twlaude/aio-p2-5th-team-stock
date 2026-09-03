-- 살래? 말래? MVP 스키마 (PostgreSQL + pgvector)
-- 포함: 사용자 성향·Memory, 지원 기업, 기업보고서 RAG, 분석 결과
-- 제외: 포트폴리오, 매매내역, 실제 주문

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS users (
    user_id       TEXT PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    display_name  TEXT NOT NULL,
    password_hash TEXT,
    is_demo       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS investment_profiles (
    user_id             TEXT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    experience_level    TEXT NOT NULL CHECK (experience_level IN ('beginner', 'intermediate', 'experienced')),
    risk_profile        TEXT NOT NULL CHECK (risk_profile IN ('conservative', 'balanced', 'aggressive')),
    investment_horizon  TEXT NOT NULL CHECK (investment_horizon IN ('short', 'medium', 'long')),
    preferred_evidence  TEXT NOT NULL CHECK (preferred_evidence IN ('market', 'news', 'financial', 'risk')),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS user_memories (
    memory_id    BIGSERIAL PRIMARY KEY,
    user_id      TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    memory_key   TEXT NOT NULL,
    memory_value JSONB NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, memory_key)
);

CREATE TABLE IF NOT EXISTS supported_companies (
    stock_code              CHAR(6) PRIMARY KEY,
    rank                    INTEGER NOT NULL,
    company_name            TEXT NOT NULL UNIQUE,
    market                  TEXT NOT NULL DEFAULT 'KOSPI',
    snapshot_date           DATE NOT NULL,
    market_cap_trillion_krw NUMERIC,
    UNIQUE (snapshot_date, rank)
);

CREATE TABLE IF NOT EXISTS source_documents (
    document_id   BIGSERIAL PRIMARY KEY,
    stock_code    CHAR(6) NOT NULL REFERENCES supported_companies(stock_code),
    document_type TEXT NOT NULL CHECK (document_type IN ('annual_report', 'disclosure')),
    external_id   TEXT NOT NULL,
    title         TEXT NOT NULL,
    source_url    TEXT,
    published_at  TIMESTAMPTZ,
    collected_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    metadata      JSONB NOT NULL DEFAULT '{}',
    UNIQUE (document_type, external_id)
);

CREATE TABLE IF NOT EXISTS rag_chunks (
    chunk_id        BIGSERIAL PRIMARY KEY,
    document_id     BIGINT NOT NULL REFERENCES source_documents(document_id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    content_hash    TEXT NOT NULL,
    embedding       vector(1536),
    embedding_model TEXT NOT NULL DEFAULT 'text-embedding-3-small',
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index),
    UNIQUE (document_id, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_source_documents_stock_type
    ON source_documents (stock_code, document_type, published_at DESC);

CREATE INDEX IF NOT EXISTS idx_rag_chunks_document
    ON rag_chunks (document_id);

CREATE TABLE IF NOT EXISTS analysis_runs (
    request_id               UUID PRIMARY KEY,
    run_id                   UUID,
    user_id                  TEXT REFERENCES users(user_id) ON DELETE SET NULL,
    stock_code               CHAR(6) NOT NULL REFERENCES supported_companies(stock_code),
    status                   TEXT NOT NULL,
    common_analysis          JSONB,
    personalized_checkpoints JSONB,
    partial_failures         JSONB NOT NULL DEFAULT '[]',
    created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
);
