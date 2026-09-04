import json

import pytest

from app.agents import StockAnalysisAgent
from app.core.config import Settings
from app.providers.openai import FunctionCall, ModelTurn
from app.runtime import StockAgentRuntime
from app.services.progress_reporter import ProgressReporter
from tests.helpers import FakeDisclosureClient


class InvalidReceiptProvider:
    async def first_turn(self, context, tools):
        return ModelTurn(
            response_id="one",
            calls=[
                FunctionCall(
                    call_id="call-1",
                    name="get_disclosure_detail",
                    arguments=json.dumps({"receipt_number": "not-in-base-result"}),
                )
            ],
        )

    async def next_turn(self, previous_response_id, tool_outputs, tools):
        raise AssertionError("잘못된 Tool은 실행 후 재호출하면 안 됩니다.")


@pytest.mark.asyncio
async def test_blocks_receipt_number_not_in_base_result():
    context = {
        "company": {"company_name": "삼성전자", "stock_code": "005930"},
        "investment_profile": None,
        "market_temperature": {"score": 50, "label": "보통"},
        "evidence_level": {"level": "medium"},
        "data": {"news": {}, "disclosures": {}, "annual_report": {}, "community": {}},
    }
    runtime = StockAgentRuntime(InvalidReceiptProvider(), FakeDisclosureClient(), max_steps=3)
    reporter = ProgressReporter(Settings(llm_provider="mock"), "request", "run")

    result = await runtime.run(context, ["202609040001"], reporter)

    assert result.termination_reason == "invalid_tool_call"
    assert result.tool_calls == 0
    assert result.failures[0].retryable is False


def test_agent_has_only_read_only_detail_tool():
    assert StockAnalysisAgent().allowed_tools == frozenset({"get_disclosure_detail"})
