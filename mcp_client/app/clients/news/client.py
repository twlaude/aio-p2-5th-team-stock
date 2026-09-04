from typing import Any

from app.clients.base import MCPToolClient


class NewsMCPClient:
    def __init__(self, client: MCPToolClient) -> None:
        self.client = client

    async def search_news(self, company_name: str, stock_code: str) -> dict[str, Any]:
        return await self.client.call_tool(
            "search_news",
            {
                "company_name": company_name,
                "stock_code": stock_code,
                "lookback_days": 7,
                "limit": 100,
            },
        )
