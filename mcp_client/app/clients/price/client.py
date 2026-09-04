from typing import Any

from app.clients.base import MCPToolClient


class PriceMCPClient:
    def __init__(self, client: MCPToolClient) -> None:
        self.client = client

    async def get_stock_quote(self, company_name: str, stock_code: str) -> dict[str, Any]:
        return await self.client.call_tool(
            "get_stock_quote",
            {"company_name": company_name, "stock_code": stock_code},
        )
