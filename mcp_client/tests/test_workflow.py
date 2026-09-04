import pytest

from app.core.config import Settings
from app.providers import MockNarrativeProvider
from app.runtime import StockAgentRuntime
from app.schemas.analysis import AnalysisRequest
from app.schemas.analysis import ToolFailure
from app.services.analysis_builder.scoring import calculate_evidence_level, calculate_market_temperature
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
    assert response.trace_summary.tool_calls == 6
    assert "관련 공시가 실제로 있어요" in response.common_analysis.one_line_summary
    assert "단일판매ㆍ공급계약체결" in response.common_analysis.disclosure_summary


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
    assert response.personalized_checkpoints.priority_checks[0] == "최근 사업보고서의 매출·영업이익 흐름"


def test_context_prioritizes_company_news_matched_material_and_receipt_enum():
    data = collected_data()
    data.news["articles"] = [
        {"headline": "일반 최신", "published_at": "2026-09-04T06:00:00Z"},
        {"headline": "삼성전자 회사 최신", "published_at": "2026-09-04T05:00:00Z"},
        {"headline": "고관련 최신", "published_at": "2026-09-04T04:00:00Z", "relevance": "high"},
        {"headline": "삼성전자 회사 이전", "published_at": "2026-09-04T03:00:00Z"},
        {"headline": "고관련 이전", "published_at": "2026-09-04T02:00:00Z", "relevance": "high"},
        {"headline": "일반 이전", "published_at": "2026-09-04T01:00:00Z"},
    ]
    data.material_disclosures["disclosures"].insert(
        0,
        {
            "report_name": "최대주주변경",
            "receipt_number": "202609040999",
            "published_at": "2026-09-04T01:00:00Z",
            "disclosure_kind": "major",
        },
    )
    request = AnalysisRequest(
        request_id="context-test",
        company={"company_name": "삼성전자", "stock_code": "005930"},
        investment_profile=None,
        requested_at="2026-09-04T00:00:00Z",
    )
    temperature = calculate_market_temperature(data)
    evidence = calculate_evidence_level(data, temperature.data_coverage)

    context = AnalysisWorkflow._context(request, data, temperature, evidence)
    receipts = AnalysisWorkflow._receipt_numbers(data, evidence)

    assert [item["headline"] for item in context["data"]["news"]["articles"]] == [
        "삼성전자 회사 최신",
        "삼성전자 회사 이전",
        "고관련 최신",
        "고관련 이전",
        "일반 최신",
    ]
    assert context["data"]["material_disclosures"]["disclosures"][0]["receipt_number"] == "202609040101"
    assert context["data"]["community"]["activity"] == data.community["activity"]
    assert receipts[:2] == ["202609040101", "202609040999"]


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
