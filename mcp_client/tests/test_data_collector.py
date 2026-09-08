import pytest

from app.schemas.analysis import CollectedData, FilterStats, ToolFailure
from app.services.data_collector.service import DataCollector
from app.services.progress_reporter import ProgressReporter


class MockProgressReporter(ProgressReporter):
    async def publish(
        self,
        event_type: str,
        phase: str,
        status: str,
        message: str,
        progress: int,
        **kwargs,
    ) -> None:
        pass


class MockClient:
    def __init__(
        self,
        price_result: dict = None,
        news_result: dict = None,
        disclosure_result: dict = None,
        annual_report_result: dict = None,
        community_result: dict = None,
    ) -> None:
        self.price_result = price_result or {"status": "success"}
        self.news_result = news_result or {"status": "success"}
        self.disclosure_result = disclosure_result or {"status": "success"}
        self.annual_report_result = annual_report_result or {
            "status": "success",
            "matched_passages": [],
            "filtered_out": 0,
        }
        self.community_result = community_result or {"status": "success"}

    async def get_stock_quote(self, company_name: str, stock_code: str):
        return self.price_result

    async def search_news(self, company_name: str, stock_code: str):
        return self.news_result

    async def get_recent_disclosures(self, company_name: str, stock_code: str):
        return self.disclosure_result

    async def get_material_disclosures(self, company_name: str, stock_code: str):
        return self.disclosure_result

    async def search_annual_report(self, company_name: str, stock_code: str):
        return self.annual_report_result

    async def get_community_reaction(self, company_name: str, stock_code: str):
        return self.community_result


@pytest.mark.asyncio
async def test_collector_extracts_filter_stats_from_annual_report():
    """Verify that filtering statistics are captured from annual_report response."""
    annual_report_response = {
        "status": "success",
        "matched_passages": [
            {"section": "1", "text": "passage1", "score": 0.85},
            {"section": "2", "text": "passage2", "score": 0.78},
        ],
        "filtered_out": 3,
    }

    price_client = MockClient()
    news_client = MockClient()
    disclosure_client = MockClient()
    community_client = MockClient()

    annual_report_client = MockClient(annual_report_result=annual_report_response)

    # Manually create a mock DataCollector by monkey-patching
    collector = DataCollector(
        price=price_client,  # type: ignore[arg-type]
        news=news_client,  # type: ignore[arg-type]
        disclosure=disclosure_client,  # type: ignore[arg-type]
        community=community_client,  # type: ignore[arg-type]
    )
    collector.disclosure = disclosure_client  # type: ignore[attr-defined]

    # Override search_annual_report since we're testing indirectly
    collector.disclosure.search_annual_report = (  # type: ignore[attr-defined]
        annual_report_client.search_annual_report
    )

    reporter = MockProgressReporter()

    from app.schemas.analysis import CompanyRef

    company = CompanyRef(company_name="테스트", stock_code="000001")
    collected = await collector.collect(company, reporter)

    assert isinstance(collected, CollectedData)
    assert collected.report_filter_stats.total_retrieved == 2
    assert collected.report_filter_stats.total_filtered_out == 3
    assert collected.report_filter_stats.filter_threshold == 0.7


@pytest.mark.asyncio
async def test_collector_handles_missing_filter_stats():
    """Verify that missing filter stats default to zero."""
    annual_report_response = {
        "status": "success",
        "matched_passages": [],
    }

    price_client = MockClient()
    news_client = MockClient()
    disclosure_client = MockClient()
    community_client = MockClient()
    annual_report_client = MockClient(annual_report_result=annual_report_response)

    collector = DataCollector(
        price=price_client,  # type: ignore[arg-type]
        news=news_client,  # type: ignore[arg-type]
        disclosure=disclosure_client,  # type: ignore[arg-type]
        community=community_client,  # type: ignore[arg-type]
    )
    collector.disclosure = disclosure_client  # type: ignore[attr-defined]
    collector.disclosure.search_annual_report = (  # type: ignore[attr-defined]
        annual_report_client.search_annual_report
    )

    reporter = MockProgressReporter()

    from app.schemas.analysis import CompanyRef

    company = CompanyRef(company_name="테스트", stock_code="000001")
    collected = await collector.collect(company, reporter)

    assert collected.report_filter_stats.total_retrieved == 0
    assert collected.report_filter_stats.total_filtered_out == 0
