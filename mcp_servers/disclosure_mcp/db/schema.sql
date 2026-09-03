-- Disclosure MCP 전용 데이터베이스 스키마 (PostgreSQL + pgvector)
-- 공용 backend/db/schema.sql과 독립적으로 DATABASE_URL이 가리키는 DB에 적용한다.
-- 임베딩 차원은 text-embedding-3-small(1536) 기준이다. 모델을 바꾸면
-- report_chunks를 비운 뒤 같은 차원의 모델로 전체 재색인해야 한다.

CREATE EXTENSION IF NOT EXISTS vector;

-- 지원 대상 기업과 OpenDART 내부 식별자를 연결한다.
CREATE TABLE IF NOT EXISTS companies (
    stock_code      VARCHAR(6) PRIMARY KEY,
    company_name    TEXT NOT NULL,
    corp_code       VARCHAR(8) NOT NULL UNIQUE,
    market          TEXT,
    is_supported    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (stock_code ~ '^[0-9]{6}$'),
    CHECK (corp_code ~ '^[0-9]{8}$')
);

CREATE INDEX IF NOT EXISTS idx_companies_name
    ON companies (company_name);

-- 최근 공시 목록의 캐시다. 공시 상세 원문은 DART에서 실시간으로 가져온다.
CREATE TABLE IF NOT EXISTS disclosures (
    receipt_number  VARCHAR(14) PRIMARY KEY,
    stock_code      VARCHAR(6) NOT NULL REFERENCES companies(stock_code),
    report_name     TEXT NOT NULL,
    published_at    TIMESTAMPTZ,
    filed_at        DATE,
    category        TEXT,
    is_major        BOOLEAN NOT NULL DEFAULT FALSE,
    is_correction   BOOLEAN NOT NULL DEFAULT FALSE,
    source_url      TEXT NOT NULL,
    raw_payload     JSONB NOT NULL DEFAULT '{}'::jsonb,
    collected_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (receipt_number ~ '^[0-9]{14}$')
);

CREATE INDEX IF NOT EXISTS idx_disclosures_stock_published
    ON disclosures (stock_code, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_disclosures_stock_major_published
    ON disclosures (stock_code, is_major, published_at DESC);

-- 사업보고서 1건의 메타데이터. 동일 기업/연도에 정정본이 있으면 수집기는
-- 최신 접수번호 행을 upsert하고 그 보고서의 청크를 다시 만든다.
CREATE TABLE IF NOT EXISTS annual_reports (
    id              BIGSERIAL PRIMARY KEY,
    stock_code      VARCHAR(6) NOT NULL REFERENCES companies(stock_code),
    report_year     SMALLINT NOT NULL,
    report_type     TEXT NOT NULL DEFAULT 'annual'
                    CHECK (report_type IN ('annual', 'semi_annual', 'quarterly')),
    report_name     TEXT NOT NULL,
    receipt_number  VARCHAR(14) NOT NULL UNIQUE,
    published_at    TIMESTAMPTZ,
    source_url      TEXT NOT NULL,
    chunk_count     INTEGER NOT NULL DEFAULT 0 CHECK (chunk_count >= 0),
    content_hash    CHAR(64),
    indexed_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (stock_code, report_year, report_type),
    CHECK (receipt_number ~ '^[0-9]{14}$'),
    CHECK (report_year BETWEEN 2000 AND 2100)
);

CREATE INDEX IF NOT EXISTS idx_annual_reports_stock_year
    ON annual_reports (stock_code, report_year DESC);

-- RAG 검색의 최소 단위. 표는 parser/chunker가 하나의 의미 단위로 평탄화한 뒤
-- 저장하고, has_table로 검색 결과의 성격을 알 수 있게 한다.
CREATE TABLE IF NOT EXISTS report_chunks (
    id              BIGSERIAL PRIMARY KEY,
    annual_report_id BIGINT NOT NULL REFERENCES annual_reports(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL CHECK (chunk_index >= 0),
    section_title   TEXT NOT NULL,
    content         TEXT NOT NULL CHECK (length(btrim(content)) > 0),
    content_hash    CHAR(64) NOT NULL,
    has_table       BOOLEAN NOT NULL DEFAULT FALSE,
    embedding       vector(1536) NOT NULL,
    embedding_model TEXT NOT NULL DEFAULT 'text-embedding-3-small',
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (annual_report_id, chunk_index),
    UNIQUE (annual_report_id, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_report_chunks_report
    ON report_chunks (annual_report_id, chunk_index);

-- 데이터가 늘어난 뒤에만 HNSW 인덱스를 고려한다. 현재 20개사 기준에서는
-- 기업/연도 선필터 후 정확한 cosine 검색이 더 예측 가능하다.
