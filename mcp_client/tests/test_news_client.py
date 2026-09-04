import pytest

from app.clients.news import NewsMCPClient


class RecordingToolClient:
    def __init__(self) -> None:
        self.tool_name = ""
        self.arguments = {}

    async def call_tool(self, tool_name, arguments):
        self.tool_name = tool_name
        self.arguments = arguments
        return {"status": "success"}


@pytest.mark.asyncio
async def test_requests_up_to_one_hundred_news_articles():
    tool_client = RecordingToolClient()

    result = await NewsMCPClient(tool_client).search_news("삼성전자", "005930")

    assert result == {"status": "success"}
    assert tool_client.tool_name == "search_news"
    assert tool_client.arguments == {
        "company_name": "삼성전자",
        "stock_code": "005930",
        "lookback_days": 7,
        "limit": 100,
    }
