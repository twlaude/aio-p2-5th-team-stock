"""실행 중인 Disclosure MCP 서버의 세 Tool을 지원 종목 전체에 대해 점검한다.

예: ``python scripts/smoke.py --server http://127.0.0.1:8022/mcp``
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys


MCP_ROOT = Path(__file__).resolve().parents[1]
if str(MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(MCP_ROOT))

from fastmcp import Client


REPOSITORY_ROOT = MCP_ROOT.parents[1]
SUPPORTED_COMPANIES_PATH = REPOSITORY_ROOT / "shared" / "supported_companies.json"


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", default="http://127.0.0.1:8022/mcp")
    parser.add_argument("--skip-search", action="store_true")
    args = parser.parse_args()
    companies = json.loads(SUPPORTED_COMPANIES_PATH.read_text(encoding="utf-8"))["companies"]
    failures = 0

    async with Client(args.server) as client:
        tool_names = [tool.name for tool in await client.list_tools()]
        expected = {"get_recent_disclosures", "get_disclosure_detail", "search_annual_report"}
        if not expected.issubset(tool_names):
            raise RuntimeError(f"필수 Tool이 없습니다: {sorted(expected - set(tool_names))}")

        for company in companies:
            result = await client.call_tool(
                "get_recent_disclosures",
                {
                    "stock_code": company["stock_code"],
                    "company_name": company["company_name"],
                },
            )
            payload = json.loads(result.content[0].text)
            ok = payload.get("status") in {"success", "no_data"}
            print(company["stock_code"], "recent", payload.get("status"))
            failures += 0 if ok else 1

            disclosures = payload.get("disclosures", [])
            if disclosures:
                detail = await client.call_tool(
                    "get_disclosure_detail",
                    {"receipt_number": disclosures[0]["receipt_number"]},
                )
                detail_payload = json.loads(detail.content[0].text)
                print(company["stock_code"], "detail", detail_payload.get("status"))
                failures += 0 if detail_payload.get("status") == "success" else 1

            if not args.skip_search:
                search = await client.call_tool(
                    "search_annual_report",
                    {
                        "stock_code": company["stock_code"],
                        "company_name": company["company_name"],
                        "query": "사업의 주요 위험과 성장 계획",
                        "top_k": 3,
                    },
                )
                search_payload = json.loads(search.content[0].text)
                print(company["stock_code"], "search", search_payload.get("status"))
                failures += 0 if search_payload.get("status") == "success" else 1

    if failures:
        raise SystemExit(f"Smoke failed: {failures} checks")
    print("Smoke passed.")


if __name__ == "__main__":
    asyncio.run(main())
