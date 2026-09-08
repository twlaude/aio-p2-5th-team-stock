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


@pytest.mark.asyncio
async def test_annual_report_default_min_score_is_off():
    transport = RecordingClient()
    client = DisclosureMCPClient(transport)  # type: ignore[arg-type]

    await client.search_annual_report("삼성전자", "005930")

    assert transport.call == (
        "search_annual_report",
        {
            "company_name": "삼성전자",
            "stock_code": "005930",
            "query": "최근 사업 현황, 성장 계획, 주요 위험 요인, 실적에 영향을 줄 수 있는 요인",
            "top_k": 5,
            "min_score": 0.0,
        },
    )


@pytest.mark.asyncio
async def test_annual_report_uses_configured_min_score():
    transport = RecordingClient()
    client = DisclosureMCPClient(transport, annual_report_min_score=0.3)  # type: ignore[arg-type]

    await client.search_annual_report("삼성전자", "005930")

    assert transport.call is not None
    assert transport.call[1]["min_score"] == 0.3
