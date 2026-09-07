from copy import deepcopy
import json

import pytest

from app.clients.base import MCPClientError
from app.core.config import Settings
from app.providers.openai import FunctionCall, ModelTurn, ProviderError
from app.runtime import StockAgentRuntime
from app.runtime.verifier import verify_narrative
from app.schemas.analysis import AnalysisRequest, Narrative, PersonalizedCheckpoints
from app.services.analysis_builder.narrative import build_fallback_narrative
from app.services.analysis_builder.scoring import calculate_evidence_level, calculate_market_temperature
from app.workflows.analysis import AnalysisWorkflow
from app.workflows.factory import build_workflow
from tests.helpers import FakeCollector, collected_data


RECEIPTS = ["20260904000123", "20260903000123", "20260902000123"]


@pytest.fixture
def context():
    return {
        "company": {"company_name": "삼성전자", "stock_code": "005930"},
        "investment_profile": None,
        "market_temperature": {"score": 50, "label": "보통"},
        "evidence_level": {"level": "medium"},
        "data": {"news": {}, "annual_report": {}, "community": {}, "disclosures": {
            "disclosures": [{"receipt_number": receipt} for receipt in RECEIPTS],
        }},
    }


class Reporter:
    def __init__(self):
        self.events = []

    async def publish(self, *args, **kwargs):
        self.events.append((args, kwargs))


class ScriptProvider:
    def __init__(self, *turns):
        self.turns = iter(turns)
        self.inputs = []

    def take(self):
        turn = next(self.turns)
        if isinstance(turn, Exception):
            raise turn
        return turn

    async def first_turn(self, context, tools):
        self.inputs.append((None, deepcopy(context), deepcopy(tools)))
        return self.take()

    async def next_turn(self, previous_response_id, tool_outputs, tools):
        self.inputs.append((previous_response_id, deepcopy(tool_outputs), deepcopy(tools)))
        return self.take()


class Disclosure:
    def __init__(self, fail=False):
        self.receipts = []
        self.fail = fail

    async def get_disclosure_detail(self, receipt_number):
        self.receipts.append(receipt_number)
        if self.fail:
            raise MCPClientError("disclosure_mcp", "MCP_TIMEOUT", "상세 조회 실패")
        return {"status": "success", "receipt_number": receipt_number, "content": "공시 상세"}


def call(receipt=RECEIPTS[0], *, name="get_disclosure_detail", arguments=None, call_id="call-1"):
    return FunctionCall(call_id, name, arguments if arguments is not None else json.dumps({"receipt_number": receipt}))


def prose(context, **changes):
    return ModelTurn("final", narrative=build_fallback_narrative(context).model_copy(update=changes))


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("invalid,kind", [
    (call(name="delete_disclosure"), "tool_selection_error"),
    (call("20990101000000"), "tool_selection_error"),
    (call(arguments="{"), "parameter_error"),
    (call(arguments="[]"), "parameter_error"),
    (call(arguments="{}"), "parameter_error"),
    (call(arguments='{"receipt_number":null}'), "parameter_error"),
    (call(arguments='{"receipt_number":[]}'), "parameter_error"),
    (call(arguments='{"receipt_number":123}'), "parameter_error"),
])
async def test_tool_errors_off_fallback_on_corrected(context, enabled, invalid, kind):
    provider = ScriptProvider(ModelTurn("bad", calls=[invalid]), prose(context))
    disclosure = Disclosure()
    result = await StockAgentRuntime(provider, disclosure, 3, reflection_enabled=enabled).run(context, RECEIPTS, Reporter())
    assert result.termination_reason == ("completed" if enabled else "invalid_tool_call")
    assert result.llm_calls == (2 if enabled else 1)
    assert result.tool_calls == 0 and disclosure.receipts == []
    if enabled:
        assert result.reflection_calls == 1 and result.failures == []
        assert [(e.kind, e.attempt, e.resolved) for e in result.reflections] == [(kind, 1, True)]
        previous, outputs, _ = provider.inputs[1]
        assert previous == "bad" and outputs[0]["call_id"] == invalid.call_id
        payload = json.loads(outputs[0]["output"])
        assert payload["status"] == "invalid_tool_call" and payload["error"]["kind"] == kind
        assert payload["allowed_receipt_numbers"] == RECEIPTS
    else:
        assert result.narrative.model_dump_json() == build_fallback_narrative(context).model_dump_json()
        assert result.reflections == [] and result.reflection_calls == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [False, True])
async def test_duplicate_receipt_is_never_executed_twice(context, enabled):
    provider = ScriptProvider(ModelTurn("one", calls=[call()]), ModelTurn("two", calls=[call()]), prose(context))
    disclosure = Disclosure()
    result = await StockAgentRuntime(provider, disclosure, 3, reflection_enabled=enabled).run(context, RECEIPTS, Reporter())
    assert disclosure.receipts == [RECEIPTS[0]] and result.tool_calls == 1
    assert result.termination_reason == ("completed" if enabled else "invalid_tool_call")
    assert result.reflection_calls == int(enabled)


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("after_tool", [False, True])
async def test_schema_recovery_keeps_response_id_and_usage(context, enabled, after_tool):
    turns = [ModelTurn("tool", calls=[call()])] if after_tool else []
    provider = ScriptProvider(*turns, ProviderError("형식 오류", "invalid-json", 11, 7), prose(context))
    result = await StockAgentRuntime(provider, Disclosure(), 3, reflection_enabled=enabled).run(context, RECEIPTS, Reporter())
    assert result.termination_reason == ("completed" if enabled else "model_error")
    assert result.llm_calls == (2 + int(after_tool) if enabled else int(after_tool))
    if enabled:
        assert (result.input_tokens, result.output_tokens) == (11, 7)
        assert result.reflections[0].kind == "schema_mismatch" and result.reflections[0].resolved
        previous, outputs, tools = provider.inputs[-1]
        assert previous == "invalid-json" and tools == []
        assert outputs[0]["role"] == "user" and "형식 오류" in outputs[0]["content"]


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [False, True])
@pytest.mark.parametrize("defect", ["receipt", "source", "prediction", "profile"])
async def test_prose_checks_preserve_off_baseline_and_repair_on(context, enabled, defect):
    clean = prose(context)
    changes = {"disclosure_summary": "공시 20990101000000에서 확인했습니다."}
    if defect == "source":
        context["partial_failures"] = [{"service": "news_mcp"}]
        clean.narrative.news_summary = "뉴스를 확인하지 못했습니다."
        changes = {"news_summary": "공급 계약 뉴스를 확인했습니다."}
    elif defect == "prediction":
        changes = {"one_line_summary": "매수하세요. 가격이 상승할 것입니다."}
    elif defect == "profile":
        changes = {"personalized_checkpoints": PersonalizedCheckpoints(
            personal_summary="확인 순서", priority_checks=["공시"], caution="추가 확인",
        )}
    bad = prose(context, **changes)
    provider = ScriptProvider(bad, clean)
    result = await StockAgentRuntime(provider, Disclosure(), 3, reflection_enabled=enabled).run(context, RECEIPTS, Reporter())
    assert result.termination_reason == "completed"
    if enabled:
        assert verify_narrative(result.narrative, context) == []
        assert result.reflection_calls == 1 and all(e.resolved for e in result.reflections)
        assert provider.inputs[-1][2] == [] and provider.inputs[-1][1][0]["role"] == "user"
    else:
        # The old runtime has no semantic verifier: changing this would invalidate the baseline.
        assert result.narrative.model_dump_json() == bad.narrative.model_dump_json()
        assert verify_narrative(result.narrative, context) and len(provider.inputs) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("kind,limit,steps,expected_calls", [
    ("tool", 0, 3, 1), ("tool", 1, 3, 2), ("tool", 2, 3, 3),
    ("tool", 5, 1, 2), ("schema", 2, 3, 2), ("prose", 2, 3, 2),
])
async def test_reflection_and_step_limits_end_in_fallback(context, kind, limit, steps, expected_calls):
    bad = ModelTurn("bad", calls=[call("20990101000000")])
    if kind == "schema":
        bad = ProviderError("형식 오류", "invalid-json")
    elif kind == "prose":
        bad = prose(context, one_line_summary="매수하세요.")
    provider = ScriptProvider(*[deepcopy(bad) for _ in range(5)])
    result = await StockAgentRuntime(provider, Disclosure(), steps, reflection_enabled=True, max_reflections=limit).run(context, RECEIPTS, Reporter())
    assert result.termination_reason == "reflection_exhausted"
    assert result.llm_calls == len(provider.inputs) == expected_calls
    assert result.reflection_calls == expected_calls - 1
    assert not result.reflections[-1].resolved
    assert result.narrative.model_dump_json() == build_fallback_narrative(context).model_dump_json()


@pytest.mark.asyncio
async def test_multiple_calls_share_feedback_and_cannot_exceed_two_details(context):
    batch = [call(receipt, call_id=f"call-{i}") for i, receipt in enumerate(RECEIPTS)]
    batch += [call(name="other", call_id="other")]
    provider = ScriptProvider(ModelTurn("batch", calls=batch), prose(context))
    disclosure = Disclosure()
    result = await StockAgentRuntime(provider, disclosure, 3, reflection_enabled=True).run(context, RECEIPTS, Reporter())
    assert disclosure.receipts == RECEIPTS[:2] and result.tool_calls == 2
    assert result.termination_reason == "completed" and result.reflection_calls == 1
    assert len(result.reflections) == 2 and all(e.attempt == 1 for e in result.reflections)
    assert [item["call_id"] for item in provider.inputs[1][1]] == [item.call_id for item in batch]
    assert provider.inputs[1][2] == []


@pytest.mark.asyncio
async def test_mixed_errors_share_budget_and_remain_pending_until_verifiable(context):
    provider = ScriptProvider(
        ModelTurn("bad-tool", calls=[call("20990101000000")]),
        ProviderError("형식 오류", "bad-json"), prose(context),
    )
    result = await StockAgentRuntime(provider, Disclosure(), 3, reflection_enabled=True).run(context, RECEIPTS, Reporter())
    assert result.termination_reason == "completed" and result.reflection_calls == 2
    assert [(e.kind, e.attempt, e.resolved) for e in result.reflections] == [
        ("tool_selection_error", 1, True), ("schema_mismatch", 2, True),
    ]
    provider = ScriptProvider(prose(context, one_line_summary="매수하세요."), ModelTurn("forbidden-tool", calls=[call()]))
    disclosure = Disclosure()
    result = await StockAgentRuntime(provider, disclosure, 3, reflection_enabled=True, max_reflections=1).run(context, RECEIPTS, Reporter())
    assert result.termination_reason == "reflection_exhausted" and result.reflection_calls == 1
    assert all(not e.resolved for e in result.reflections) and disclosure.receipts == []


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_first", [False, True, None])
async def test_last_step_checks_whole_batch_without_executing_tools(context, invalid_first):
    batch = [call(RECEIPTS[1])]
    if invalid_first is not None:
        batch.insert(0 if invalid_first else 1, call("20990101000000", call_id="bad"))
    provider = ScriptProvider(ModelTurn("first", calls=[call()]), ModelTurn("last", calls=batch))
    disclosure = Disclosure()
    result = await StockAgentRuntime(provider, disclosure, 1, reflection_enabled=True).run(context, RECEIPTS, Reporter())
    assert disclosure.receipts == RECEIPTS[:1] and result.llm_calls == 2
    assert result.termination_reason == ("max_steps_exceeded" if invalid_first is None else "reflection_exhausted")
    assert len(result.reflections) == int(invalid_first is not None)
    assert result.reflection_calls == 0


@pytest.mark.asyncio
async def test_detail_failure_is_revalidated_and_final_step_cannot_bypass_verifier(context):
    provider = ScriptProvider(ModelTurn("tool", calls=[call()]), prose(context), prose(context, disclosure_summary="상세 공시 조회에 실패했습니다."))
    disclosure = Disclosure(fail=True)
    result = await StockAgentRuntime(provider, disclosure, 2, reflection_enabled=True).run(context, RECEIPTS, Reporter())
    assert result.termination_reason == "completed" and result.reflection_calls == 1
    assert result.failed_tools == ["get_disclosure_detail"] and len(result.failures) == 1
    assert result.reflections[0].resolved
    provider = ScriptProvider(ModelTurn("tool", calls=[call()]), prose(context, one_line_summary="매수하세요."))
    result = await StockAgentRuntime(provider, Disclosure(), 1, reflection_enabled=True).run(context, RECEIPTS, Reporter())
    assert result.termination_reason == "reflection_exhausted" and result.reflection_calls == 0


@pytest.mark.parametrize("source,tool,key", [
    ("news", "search_news", "news"), ("disclosure", "search_annual_report", "annual_report"),
    ("community", "get_community_reaction", "community"),
])
@pytest.mark.parametrize("signal", ["failed_tools", "partial_failures", "status"])
def test_verifier_detects_source_failures_and_accepts_limitations(context, source, tool, key, signal):
    if signal == "status":
        context["data"][key]["status"] = "external_api_error"
    elif signal == "failed_tools":
        context[signal] = [tool]
    else:
        context[signal] = [{"service": f"{source}_mcp"}]
    narrative = prose(context).narrative
    assert any(f"{source}_summary" in v.detail for v in verify_narrative(narrative, context))
    setattr(narrative, f"{source}_summary", "자료를 조회하지 못했습니다.")
    assert verify_narrative(narrative, context) == []


def test_receipt_grounding_and_member_profile_are_independent(context):
    narrative = prose(context, disclosure_summary=f"공시 {RECEIPTS[0]}를 확인했습니다.").narrative
    assert verify_narrative(narrative, context) == []
    context["data"]["news"] = {"articles": [{"headline": "20990101000000", "receipt_number": "20990101000000"}]}
    narrative.disclosure_summary = "공시 20990101000000를 확인했습니다."
    assert verify_narrative(narrative, context)[0].kind == "hallucination"
    narrative.disclosure_summary = "공식 자료를 확인했습니다."
    context["investment_profile"] = {"preferred_evidence": "news", "investment_horizon": "long"}
    assert verify_narrative(narrative, context)[0].kind == "inconsistency"
    assert verify_narrative(build_fallback_narrative(context), context) == []


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [False, True])
async def test_workflow_wires_failure_context_and_additive_trace(enabled, monkeypatch):
    monkeypatch.setenv("AGENT_REFLECTION_ENABLED", str(enabled).lower())
    monkeypatch.setenv("AGENT_MAX_REFLECTIONS", "1")
    settings = Settings(llm_provider="mock", backend_event_url="")
    workflow = build_workflow(settings)
    assert workflow.agent.reflection_enabled is enabled and workflow.agent.max_reflections == 1
    data = collected_data()
    workflow.collector = FakeCollector(data)
    request = AnalysisRequest(request_id="test-reflection", company={"company_name": "삼성전자", "stock_code": "005930"}, requested_at="2026-09-04T00:00:00Z")
    temperature = calculate_market_temperature(data)
    context = workflow._context(request, data, temperature, calculate_evidence_level(data, temperature.data_coverage))
    provider = ScriptProvider(ModelTurn("bad", calls=[call("20990101000000")]), prose(context))
    workflow.agent.provider = provider
    response = await workflow.run(request)
    assert response.trace_summary.reflections == int(enabled)
    assert ("reflections" in response.trace_summary.model_dump()) is enabled
    assert ("failed_tools" in provider.inputs[0][1]) is enabled
    assert response.termination_reason == ("completed" if enabled else "invalid_tool_call")
    assert response.status == ("success" if enabled else "partial_success")
