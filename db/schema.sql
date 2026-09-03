-- stock_insight 스키마 (PostgreSQL + pgvector)
-- 원칙: 숫자·상태·관계 = 정형 테이블 / 긴 텍스트 근거 = rag_chunks(벡터)
--
-- Backend가 소유하는 영역: users, user_profiles, analysis_runs.
-- rag_chunks는 News·Disclosure·Community MCP가 공용으로 쓰는 벡터 저장소다.
-- 종목 마스터·가격·수급은 Price MCP 쪽 설계가 정해지면 별도로 추가한다.

CREATE EXTENSION IF NOT EXISTS vector;

-- ── 회원과 투자 성향 ─────────────────────────────────────
-- user_id는 Backend가 발급하는 문자열 식별자를 그대로 쓴다(예: demo-001).
CREATE TABLE IF NOT EXISTS users (
    user_id         TEXT PRIMARY KEY,
    username        TEXT NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    display_name    TEXT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 장기 Memory. 초기 허용 항목 네 개만 저장한다(backend/MEMORY_GUIDE.md).
-- 회원가입 때 항상 함께 만들어지므로 users와 1:1이다.
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id             TEXT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    experience_level    TEXT NOT NULL CHECK (experience_level IN ('beginner', 'intermediate', 'experienced')),
    risk_profile        TEXT NOT NULL CHECK (risk_profile IN ('conservative', 'balanced', 'aggressive')),
    investment_horizon  TEXT NOT NULL CHECK (investment_horizon IN ('short', 'medium', 'long')),
    preferred_evidence  TEXT NOT NULL CHECK (preferred_evidence IN ('market', 'news', 'financial', 'risk')),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ── 분석 기록과 근거 ─────────────────────────────────────
-- shared/contracts/analysis, frontend_backend 계약의 응답을 그대로 남긴다.
-- sources·partial_failures·personalized_checkpoints는 MCP Client가 만드는
-- 가변 구조라 강제 정규화 대신 JSONB로 둔다.
CREATE TABLE IF NOT EXISTS analysis_runs (
    id                          BIGSERIAL PRIMARY KEY,
    request_id                  TEXT NOT NULL UNIQUE,
    user_id                     TEXT REFERENCES users(user_id),   -- 비회원이면 NULL
    company_name                TEXT NOT NULL,
    stock_code                  TEXT NOT NULL,
    access_level                TEXT NOT NULL CHECK (access_level IN ('guest', 'member')),
    status                      TEXT NOT NULL,
    one_line_summary            TEXT NOT NULL,
    sources                     JSONB NOT NULL DEFAULT '[]',
    partial_failures            JSONB NOT NULL DEFAULT '[]',
    personalized_checkpoints    JSONB,                             -- 회원만 채움
    requested_at                TIMESTAMPTZ NOT NULL,
    collected_at                TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_user
    ON analysis_runs (user_id, requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_stock
    ON analysis_runs (stock_code, requested_at DESC);

-- ── 벡터: 긴 텍스트 근거 저장소 (News·Disclosure·Community 공용) ──
-- doc_type: news | disclosure | community_summary | report
-- 임베딩 모델 통일 필수 — text-embedding-3-small(1536) 기준. 바꾸면 전체 재임베딩.
CREATE TABLE IF NOT EXISTS rag_chunks (
    id              BIGSERIAL PRIMARY KEY,
    stock_code      TEXT NOT NULL,
    doc_type        TEXT NOT NULL,
    document_id     TEXT,                          -- 원문 식별자 (기사 URL, 공시 접수번호 등)
    chunk_index     INT NOT NULL DEFAULT 0,
    title           TEXT,
    content         TEXT NOT NULL,
    content_hash    TEXT NOT NULL,                 -- 중복 삽입/재임베딩 방지
    published_at    TIMESTAMPTZ,                   -- 원문 기준일
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    source          TEXT,
    embedding       vector(1536),
    embedding_model TEXT NOT NULL DEFAULT 'text-embedding-3-small',
    metadata        JSONB NOT NULL DEFAULT '{}',
    UNIQUE (doc_type, content_hash)
);

-- 검색은 항상 SQL 선필터(stock_code/doc_type) → 그 안에서 벡터 top-k
CREATE INDEX IF NOT EXISTS idx_rag_chunks_filter
    ON rag_chunks (stock_code, doc_type);

-- ANN 인덱스(HNSW)는 데이터 커지기 전엔 불필요 — 풀스캔이 정확함
