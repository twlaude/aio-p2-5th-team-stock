from typing import Any

from app.clients.base import MCPToolClient


class CommunityMCPClient:
    def __init__(self, client: MCPToolClient) -> None:
        self.client = client

    async def get_community_reaction(self, company_name: str, stock_code: str) -> dict[str, Any]:
        return await self.client.call_tool(
            "get_community_reaction",
            {
                "company_name": company_name,
                "stock_code": stock_code,
                "lookback_days": 7,
                "limit": 100,
            },
        )
