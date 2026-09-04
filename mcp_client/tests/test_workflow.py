import pytest

from app.core.config import Settings
from app.providers import MockNarrativeProvider
from app.runtime import StockAgentRuntime
from app.schemas.analysis import AnalysisRequest
from app.schemas.analysis import ToolFailure
from app.workflows.analysis import AnalysisWorkflow
from tests.helpers import FakeCollector, FakeDisclosureClient, collected_data


@pytest.mark.asyncio
async def test_builds_backend_contract_for_guest():
    settings = Settings(llm_provider="mock")
    data = collected_data()
    agent = StockAgentRuntime(MockNarrativeProvider(), FakeDisclosureClient(), max_steps=3)
    workflow = AnalysisWorkflow(settings, FakeCollector(data), agent)
    request = AnalysisRequest(
        request_id="request-1",
        company={"company_name": "삼성전자", "stock_code": "005930"},
        investment_profile=None,
        requested_at="2026-09-04T00:00:00Z",
    )

    response = await workflow.run(request)

    assert response.status == "success"
    assert response.termination_reason == "completed"
    assert response.price.current_price == 70000
    assert response.price.volume_basis == "intraday_pace"
    assert response.price.volume_as_of == "2026-09-04"
    assert response.personalized_checkpoints is None
    assert response.trace_summary.tool_calls == 5


@pytest.mark.asyncio
async def test_adds_personalized_checkpoints_for_member():
    settings = Settings(llm_provider="mock")
    data = collected_data()
    agent = StockAgentRuntime(MockNarrativeProvider(), FakeDisclosureClient(), max_steps=3)
    workflow = AnalysisWorkflow(settings, FakeCollector(data), agent)
    request = AnalysisRequest(
        request_id="request-2",
        company={"company_name": "삼성전자", "stock_code": "005930"},
        investment_profile={
            "experience_level": "beginner",
            "risk_profile": "conservative",
            "investment_horizon": "long",
            "preferred_evidence": "financial",
        },
        requested_at="2026-09-04T00:00:00Z",
    )

    response = await workflow.run(request)

    assert response.personalized_checkpoints is not None
    assert "공식 공시" in response.personalized_checkpoints.priority_checks[0]


@pytest.mark.asyncio
async def test_preserves_successful_data_when_optional_source_fails():
    settings = Settings(llm_provider="mock")
    data = collected_data()
    data.news = {"status": "external_api_error", "articles": [], "result_count": 0}
    data.failures.append(
        ToolFailure(
            service="news_mcp",
            status="NEWS_API_UNAVAILABLE",
            message="뉴스를 가져오지 못했습니다.",
            retryable=True,
        )
    )
    data.completed_tools.remove("search_news")
    data.failed_tools.append("search_news")
    agent = StockAgentRuntime(MockNarrativeProvider(), FakeDisclosureClient(), max_steps=3)
    workflow = AnalysisWorkflow(settings, FakeCollector(data), agent)
    request = AnalysisRequest(
        request_id="request-3",
        company={"company_name": "삼성전자", "stock_code": "005930"},
        investment_profile=None,
        requested_at="2026-09-04T00:00:00Z",
    )

    response = await workflow.run(request)

    assert response.status == "partial_success"
    assert response.termination_reason == "partial_completed"
    assert response.price.current_price == 70000
    assert response.partial_failures[0].service == "news_mcp"
