"""Disclosure MCP 전용 PostgreSQL 조회 클라이언트."""

from __future__ import annotations

from datetime import datetime
from typing import TypedDict

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class CompanyRow(TypedDict):
    stock_code: str
    company_name: str
    corp_code: str


class DisclosureCacheRow(TypedDict):
    receipt_number: str
    stock_code: str
    report_name: str
    published_at: str
    filed_at: str
    category: str
    is_major: bool
    is_correction: bool
    source_url: str
    raw_payload: dict[str, object]


class DisclosureMetadataRow(TypedDict):
    receipt_number: str
    report_name: str
    published_at: datetime | None
    source_url: str


class DisclosureRepository:
    """DB 접근만 담당한다. 기업 식별 정책은 service 계층에 둔다."""

    def __init__(self, database_url: str) -> None:
        if not database_url:
            raise ValueError("database_url is required.")
        self._database_url = database_url

    def find_supported_company(self, stock_code: str) -> CompanyRow | None:
        """지원 종목이면 내부 식별에 필요한 최소 필드만 반환한다."""

        query = """
            SELECT stock_code, company_name, corp_code
            FROM companies
            WHERE stock_code = %s AND is_supported = TRUE
        """
        with psycopg.connect(self._database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (stock_code,))
                row = cursor.fetchone()
        return row

    def upsert_disclosures(self, disclosures: list[DisclosureCacheRow]) -> None:
        """DART 공시 목록을 접수번호 기준으로 캐시한다."""

        if not disclosures:
            return
        query = """
            INSERT INTO disclosures (
                receipt_number, stock_code, report_name, published_at, filed_at,
                category, is_major, is_correction, source_url, raw_payload
            ) VALUES (
                %(receipt_number)s, %(stock_code)s, %(report_name)s,
                %(published_at)s, %(filed_at)s, %(category)s, %(is_major)s,
                %(is_correction)s, %(source_url)s, %(raw_payload)s
            )
            ON CONFLICT (receipt_number) DO UPDATE
            SET report_name = EXCLUDED.report_name,
                published_at = EXCLUDED.published_at,
                filed_at = EXCLUDED.filed_at,
                category = EXCLUDED.category,
                is_major = EXCLUDED.is_major,
                is_correction = EXCLUDED.is_correction,
                source_url = EXCLUDED.source_url,
                raw_payload = EXCLUDED.raw_payload,
                collected_at = now(),
                updated_at = now()
        """
        rows = [
            {**disclosure, "raw_payload": Jsonb(disclosure["raw_payload"])}
            for disclosure in disclosures
        ]
        with psycopg.connect(self._database_url) as connection:
            with connection.cursor() as cursor:
                cursor.executemany(query, rows)

    def find_disclosure_metadata(
        self, receipt_number: str
    ) -> DisclosureMetadataRow | None:
        """목록 조회 때 캐시한 공시의 MCP 반환용 메타데이터를 찾는다."""

        query = """
            SELECT receipt_number, report_name, published_at, source_url
            FROM disclosures
            WHERE receipt_number = %s
        """
        with psycopg.connect(self._database_url, row_factory=dict_row) as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (receipt_number,))
                row = cursor.fetchone()
        return row
