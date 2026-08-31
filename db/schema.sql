-- stock_insight 스키마 (PostgreSQL + pgvector)
-- 원칙: 숫자·시계열·포트폴리오 원장 = 정형 테이블 / 긴 텍스트 근거 = rag_chunks(벡터)

CREATE EXTENSION IF NOT EXISTS vector;

-- ── 정형: 사용자/포트폴리오 ──────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          BIGSERIAL PRIMARY KEY,
    username    TEXT NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS positions (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id),
    stock_code  TEXT NOT NULL,              -- 종목코드 (예: 005930)
    stock_name  TEXT NOT NULL,
    quantity    NUMERIC NOT NULL,
    avg_price   NUMERIC NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (user_id, stock_code)
);

CREATE TABLE IF NOT EXISTS transactions (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id),
    stock_code  TEXT NOT NULL,
    side        TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
    quantity    NUMERIC NOT NULL,
    price       NUMERIC NOT NULL,
    traded_at   TIMESTAMPTZ NOT NULL
);

-- ── 정형: 커뮤니티 공포탐욕 시계열 (추이/전일대비는 SQL로) ──
CREATE TABLE IF NOT EXISTS fear_greed_daily (
    id           BIGSERIAL PRIMARY KEY,
    stock_code   TEXT NOT NULL,
    summary_date DATE NOT NULL,
    score        NUMERIC NOT NULL,          -- 0(공포)~100(탐욕)
    post_count   INT NOT NULL DEFAULT 0,
    UNIQUE (stock_code, summary_date)
);

-- ── 벡터: 긴 텍스트 근거 저장소 ─────────────────────────
-- doc_type: user_note | news | disclosure | community_summary | report
-- 임베딩 모델 통일 필수 — text-embedding-3-small(1536) 기준. 바꾸면 전체 재임베딩.
CREATE TABLE IF NOT EXISTS rag_chunks (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT REFERENCES users(id),   -- user_note만 채움, 공용 자료는 NULL
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

-- 검색은 항상 SQL 선필터(stock_code/user_id/doc_type) → 그 안에서 벡터 top-k
CREATE INDEX IF NOT EXISTS idx_rag_chunks_filter
    ON rag_chunks (stock_code, doc_type, user_id);

-- ANN 인덱스(HNSW)는 데이터 커지기 전엔 불필요 — 풀스캔이 정확함
