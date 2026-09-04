"""지원 대상 20개 종목과 OpenDART corp_code를 전용 DB에 동기화한다.

실행 전 ``python scripts/init_db.py``를 먼저 수행한다.
실행: ``python scripts/sync_companies.py``
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any


MCP_ROOT = Path(__file__).resolve().parents[1]
if str(MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(MCP_ROOT))

import psycopg

from app.clients.dart import DartClient
from app.core.config import get_config
from app.core.errors import ConfigurationError


REPOSITORY_ROOT = MCP_ROOT.parents[1]
SUPPORTED_COMPANIES_PATH = REPOSITORY_ROOT / "shared" / "supported_companies.json"


def load_supported_companies() -> list[dict[str, Any]]:
    """공용 종목 목록 파일에서 동기화 대상만 읽는다."""

    payload = json.loads(SUPPORTED_COMPANIES_PATH.read_text(encoding="utf-8"))
    companies = payload.get("companies")
    if not isinstance(companies, list) or not companies:
        raise ValueError("supported_companies.json에 companies 목록이 없습니다.")
    return companies


def main() -> None:
    config = get_config()
    if not config.database_url:
        raise ConfigurationError("DATABASE_URL is required to sync Disclosure MCP companies.")

    supported = load_supported_companies()
    supported_by_stock = {str(item["stock_code"]): item for item in supported}

    with DartClient(config) as dart_client:
        corp_codes = dart_client.get_corp_codes()
    corp_by_stock = {
        record["stock_code"]: record
        for record in corp_codes
        if record["stock_code"] in supported_by_stock
    }

    missing = sorted(set(supported_by_stock) - set(corp_by_stock))
    if missing:
        raise RuntimeError(
            "DART corpCode.xml에서 지원 종목을 찾지 못했습니다: " + ", ".join(missing)
        )

    rows = [
        (
            stock_code,
            str(supported_by_stock[stock_code]["company_name"]),
            corp_by_stock[stock_code]["corp_code"],
            str(supported_by_stock[stock_code].get("market") or ""),
        )
        for stock_code in sorted(supported_by_stock)
    ]
    query = """
        INSERT INTO companies (stock_code, company_name, corp_code, market, is_supported)
        VALUES (%s, %s, %s, %s, TRUE)
        ON CONFLICT (stock_code) DO UPDATE
        SET company_name = EXCLUDED.company_name,
            corp_code = EXCLUDED.corp_code,
            market = EXCLUDED.market,
            is_supported = TRUE,
            updated_at = now()
    """
    with psycopg.connect(config.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(query, rows)

    print(f"Synced {len(rows)} supported companies.")


if __name__ == "__main__":
    main()
