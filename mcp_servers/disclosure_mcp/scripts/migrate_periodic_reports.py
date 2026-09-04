"""기존 사업보고서 전용 테이블을 정기보고서(사업·반기·분기)용으로 확장한다."""

from __future__ import annotations

from pathlib import Path
import sys


MCP_ROOT = Path(__file__).resolve().parents[1]
if str(MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(MCP_ROOT))

import psycopg

from app.core.config import get_config
from app.core.errors import ConfigurationError


MIGRATION_SQL = """
ALTER TABLE annual_reports
    ADD COLUMN IF NOT EXISTS report_type TEXT NOT NULL DEFAULT 'annual';

ALTER TABLE annual_reports
    DROP CONSTRAINT IF EXISTS annual_reports_report_type_check;
ALTER TABLE annual_reports
    ADD CONSTRAINT annual_reports_report_type_check
    CHECK (report_type IN ('annual', 'semi_annual', 'quarterly'));

ALTER TABLE annual_reports
    DROP CONSTRAINT IF EXISTS annual_reports_stock_code_report_year_key;
ALTER TABLE annual_reports
    ADD CONSTRAINT annual_reports_stock_code_report_year_report_type_key
    UNIQUE (stock_code, report_year, report_type);
"""


def main() -> None:
    config = get_config()
    if not config.database_url:
        raise ConfigurationError("DATABASE_URL is required to migrate reports.")
    with psycopg.connect(config.database_url) as connection:
        connection.execute(MIGRATION_SQL)
    print("Periodic report migration applied.")


if __name__ == "__main__":
    main()
