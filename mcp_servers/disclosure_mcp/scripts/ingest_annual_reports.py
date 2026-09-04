"""사업보고서를 DART에서 받아 파싱·임베딩·pgvector 색인한다.

예: ``python scripts/ingest_annual_reports.py --stock 005930 --years 2025 --types annual semi_annual quarterly``
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


MCP_ROOT = Path(__file__).resolve().parents[1]
if str(MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(MCP_ROOT))

from app.clients.dart import DartClient
from app.clients.embedding import OpenAIEmbeddingClient
from app.clients.repository import DisclosureRepository
from app.core.config import get_config
from app.rag import ReportStore
from app.services.annual_report_service import AnnualReportService
from app.services.company_resolver import CompanyResolver


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock", required=True, help="6자리 종목코드")
    parser.add_argument("--years", required=True, nargs="+", type=int)
    parser.add_argument(
        "--types",
        nargs="+",
        choices=["annual", "semi_annual", "quarterly"],
        default=["annual"],
    )
    args = parser.parse_args()

    config = get_config()
    config.validate_for_annual_report_search()
    assert config.database_url is not None
    dart_client = DartClient(config)
    service = AnnualReportService(
        company_resolver=CompanyResolver(DisclosureRepository(config.database_url)),
        dart_client=dart_client,
        embedding_client=OpenAIEmbeddingClient(config),
        report_store=ReportStore(config.database_url),
    )
    try:
        for year in args.years:
            for report_type in args.types:
                service.ingest_periodic_report(
                    stock_code=args.stock,
                    report_year=year,
                    report_type=report_type,
                )
                print(f"Indexed {args.stock} {report_type} report for {year}.")
    finally:
        dart_client.close()


if __name__ == "__main__":
    main()
