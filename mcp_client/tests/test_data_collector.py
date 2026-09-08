import pytest

from app.core.config import Settings
from app.schemas.analysis import CollectedData, CompanyRef
from app.services.data_collector.service import DataCollector
from app.services.progress_reporter import ProgressReporter


class SilentReporter(ProgressReporter):
    def __init__(self) -> None:
        super().__init__(Settings(llm_provider="mock", backend_event_url=""), "request", "run")

    async def publish(self, *args, **kwargs) -> None:
        return None


class StubClient:
    """모든 MCP 클라이언트 역할을 겸하는 stub. annual_report 응답만 바꿔 쓴다."""

    def __init__(self, annual_report: dict, annual_report_min_score: float = 0.0) -> None:
        self.annual_report = annual_report
        self.annual_report_min_score = annual_report_min_score

    async def get_stock_quote(self, company_name: str, stock_code: str):
        return {"status": "success"}

    async def search_news(self, company_name: str, stock_code: str):
        return {"status": "success"}

    async def get_recent_disclosures(self, company_name: str, stock_code: str):
        return {"status": "success"}

    async def get_material_disclosures(self, company_name: str, stock_code: str):
        return {"status": "success"}

    async def search_annual_report(self, company_name: str, stock_code: str):
        return self.annual_report

    async def get_community_reaction(self, company_name: str, stock_code: str):
        return {"status": "success"}


async def _collect(annual_report: dict, min_score: float = 0.0) -> CollectedData:
    stub = StubClient(annual_report, annual_report_min_score=min_score)
    collector = DataCollector(price=stub, news=stub, disclosure=stub, community=stub)  # type: ignore[arg-type]
    return await collector.collect(CompanyRef(company_name="테스트", stock_code="000001"), SilentReporter())


@pytest.mark.asyncio
async def test_collector_extracts_filter_stats_from_annual_report():
    collected = await _collect(
        {
            "status": "success",
            "matched_passages": [
                {"section": "1", "text": "passage1", "score": 0.45},
                {"section": "2", "text": "passage2", "score": 0.41},
            ],
            "filtered_out": 3,
        },
        min_score=0.3,
    )

    assert collected.report_filter_stats.total_retrieved == 2
    assert collected.report_filter_stats.total_filtered_out == 3
    assert collected.report_filter_stats.filter_threshold == 0.3
    assert len(collected.annual_report["matched_passages"]) == 2


@pytest.mark.asyncio
async def test_collector_handles_missing_filter_stats():
    collected = await _collect({"status": "success", "matched_passages": []})

    assert collected.report_filter_stats.total_retrieved == 0
    assert collected.report_filter_stats.total_filtered_out == 0
    assert collected.report_filter_stats.filter_threshold == 0.0


@pytest.mark.asyncio
async def test_collector_filter_stats_survive_malformed_annual_report():
    collected = await _collect({"status": "no_report", "matched_passages": None, "filtered_out": "n/a"})

    assert collected.report_filter_stats.total_retrieved == 0
    assert collected.report_filter_stats.total_filtered_out == 0
