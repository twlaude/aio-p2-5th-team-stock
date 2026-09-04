from typing import Any

from app.clients.base import MCPToolClient


REPORT_QUERY = "최근 사업 현황, 성장 계획, 주요 위험 요인, 실적에 영향을 줄 수 있는 요인"


class DisclosureMCPClient:
    def __init__(self, client: MCPToolClient) -> None:
        self.client = client

    async def get_recent_disclosures(self, company_name: str, stock_code: str) -> dict[str, Any]:
        return await self.client.call_tool(
            "get_recent_disclosures",
            {
                "company_name": company_name,
                "stock_code": stock_code,
                "lookback_days": 30,
                "limit": 20,
            },
        )

    async def search_annual_report(self, company_name: str, stock_code: str) -> dict[str, Any]:
        return await self.client.call_tool(
            "search_annual_report",
            {
                "company_name": company_name,
                "stock_code": stock_code,
                "query": REPORT_QUERY,
                "top_k": 5,
            },
        )

    async def get_disclosure_detail(self, receipt_number: str) -> dict[str, Any]:
        return await self.client.call_tool(
            "get_disclosure_detail",
            {"receipt_number": receipt_number},
        )
