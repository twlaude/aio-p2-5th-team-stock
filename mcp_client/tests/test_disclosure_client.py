import pytest

from app.clients.disclosure.client import DisclosureMCPClient


class RecordingClient:
    def __init__(self) -> None:
        self.call: tuple[str, dict] | None = None

    async def call_tool(self, name: str, arguments: dict) -> dict:
        self.call = (name, arguments)
        return {"status": "success", "disclosures": []}


@pytest.mark.asyncio
async def test_material_disclosures_use_thirty_day_non_periodic_query():
    transport = RecordingClient()
    client = DisclosureMCPClient(transport)  # type: ignore[arg-type]

    await client.get_material_disclosures("삼성전자", "005930")

    assert transport.call == (
        "get_recent_disclosures",
        {
            "company_name": "삼성전자",
            "stock_code": "005930",
            "lookback_days": 30,
            "limit": 50,
            "disclosure_types": ["B", "C", "D", "E", "I"],
        },
    )
