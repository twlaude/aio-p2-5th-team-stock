"""Offline tests of measurement boundaries, not a second implementation of the runtime."""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from capture_fixtures import HERE, clean, required_receipts
from run_eval import FixtureCollector, evaluate, rescore_off, selection_result
from report import load_rows, metrics, ratio
from app.clients.base import MCPClientError
from app.providers.openai import FunctionCall, ModelTurn, OpenAINarrativeProvider, ProviderError
from app.services.analysis_builder.narrative import build_fallback_narrative


CASES = json.loads((HERE / "cases.json").read_text())


def test_case_distribution_and_fixture_coverage():
    from collections import Counter
    assert len(CASES) == len({case["case_id"] for case in CASES}) == 30
    assert Counter(case["kind"] for case in CASES) == {
        "normal": 12, "empty_disclosures": 4, "news_failure": 3, "community_failure": 3,
        "detail_failure": 3, "temptation": 3, "price_failure": 2,
    }
    assert sum(case["investment_profile"] is not None for case in CASES) == 6
    assert len({case["stock_code"] for case in CASES}) == 20
    for path in (HERE / "fixtures").glob("*.json"):
        fixture = json.loads(path.read_text())
        assert fixture["captured_at"] and fixture["data"]["price"]["status"] == "success"
        assert set(fixture["receipt_numbers"]) <= fixture["details"].keys()
        assert set(required_receipts(fixture, CASES)) <= fixture["details"].keys()
    assert len(list((HERE / "fixtures").glob("*.json"))) == 20


@pytest.mark.parametrize("calls,completed,correct", [([], True, True), ([], False, False),
    ([{"name": "get_disclosure_detail", "arguments": '{"receipt_number":"20260907000001"}'}], False, True),
    ([{"name": "get_disclosure_detail", "arguments": '{"receipt_number":"20990101000001"}'}], True, False),
    ([{"name": "get_disclosure_detail", "arguments": '{}'}], True, False),
    ([{"name": "order", "arguments": '{}'}], True, False),
])
def test_selection_counts_requests_and_excludes_failed_no_call(calls, completed, correct):
    assert selection_result([{"calls": calls, "allowed_tools": ["get_disclosure_detail"]}],
                            ["20260907000001"], completed)["correct"] is correct


def test_selection_respects_closed_tool_state():
    calls = [{"name": "get_disclosure_detail", "arguments": '{"receipt_number":"20260907000001"}'}]
    assert not selection_result([{"calls": calls, "allowed_tools": []}], ["20260907000001"], True)["correct"]


def test_injections_do_not_mutate_fixtures():
    fixture = json.loads((HERE / "fixtures/005930.json").read_text())
    original = deepcopy(fixture)
    for case in CASES:
        collector = FixtureCollector(fixture, case)
        if case["kind"] == "empty_disclosures":
            assert not collector.data.disclosures["disclosures"]
            assert not collector.data.material_disclosures["disclosures"]
        if case["kind"] == "news_failure":
            assert "search_news" in collector.data.failed_tools
            assert "search_news" not in collector.data.completed_tools
        if case["kind"] == "detail_failure":
            with pytest.raises(MCPClientError, match="주입"):
                asyncio.run(collector.get_disclosure_detail(fixture["receipt_numbers"][0]))
        if case["kind"] == "temptation":
            assert case["injected_receipt"] in collector.data.model_dump_json()
    assert fixture == original


@pytest.mark.parametrize("case", [case for case in CASES if case["kind"] == "price_failure"])
def test_price_failure_stops_real_workflow_before_provider(monkeypatch, case):
    async def forbidden(*args):
        pytest.fail("Price failure must not reach the provider")
    monkeypatch.setattr(OpenAINarrativeProvider, "first_turn", forbidden)
    row = asyncio.run(evaluate(case, "off", 1, HERE / "fixtures"))
    assert row["termination_reason"] == "RequiredPriceError"
    assert row["excluded_from_metrics"] and row["llm_calls"] == row["http_attempts"] == 0


def test_observation_precedes_workflow_repairs_and_counts_failed_calls(monkeypatch):
    async def mismatched(self, context, tools):
        narrative = build_fallback_narrative(context)
        narrative.personalized_checkpoints = None
        return ModelTurn("test", narrative=narrative)
    monkeypatch.setattr(OpenAINarrativeProvider, "first_turn", mismatched)
    case = deepcopy(CASES[0])
    case["kind"] = "news_failure"
    row = asyncio.run(evaluate(case, "off", 1, HERE / "fixtures"))
    assert row["termination_reason"] == "completed"
    assert row["workflow_termination_reason"] == "partial_completed"
    assert row["narrative"]["personalized_checkpoints"] is None
    assert not row["verifier"]["passed"]
    assert any("null" in item["detail"] for item in row["verifier"]["violations"])
    async def broken(*args):
        raise ProviderError("provider failure")
    monkeypatch.setattr(OpenAINarrativeProvider, "first_turn", broken)
    row = asyncio.run(evaluate(CASES[0], "off", 1, HERE / "fixtures"))
    assert row["llm_calls"] == 1 and row["runtime_llm_calls"] == 0
    assert not row["selection"]["correct"]


def test_metric_denominators_and_reflection_calls():
    base = dict(excluded_from_metrics=False, termination_reason="completed", verifier={"passed": True},
                selection={"eligible": True, "correct": True}, reflection_calls=1, llm_calls=2, http_attempts=3)
    failed = {**base, "termination_reason": "model_error", "selection": {"eligible": True, "correct": False}}
    excluded = {**base, "excluded_from_metrics": True}
    result = metrics([base, failed, excluded])
    assert result == {"completion": (1, 2), "selection": (1, 2), "consistency": (1, 1),
                      "reflections": (2, 2), "llm": (4, 2), "http": (6, 2)}
    assert ratio((0, 0)) == "N/A (0/0)"


def test_timeout_preserves_executed_tool_and_reflection_counts(monkeypatch):
    import run_eval
    original_settings = run_eval.settings_for
    monkeypatch.setattr(run_eval, "settings_for", lambda mode: original_settings(mode).model_copy(
        update={"workflow_timeout_seconds": 0.1}))
    async def first(self, context, tools):
        self.test_context = context
        self.test_next_calls = 0
        receipt = tools[0]["parameters"]["properties"]["receipt_number"]["enum"][0]
        return ModelTurn("test-1", calls=[FunctionCall("test-call", "get_disclosure_detail",
                                                     json.dumps({"receipt_number": receipt}))])
    async def next_turn(self, *args):
        self.test_next_calls += 1
        if self.test_next_calls == 1:
            narrative = build_fallback_narrative(self.test_context)
            narrative.news_summary = "매수하세요."
            return ModelTurn("test-2", narrative=narrative)
        await asyncio.sleep(1)
    monkeypatch.setattr(OpenAINarrativeProvider, "first_turn", first)
    monkeypatch.setattr(OpenAINarrativeProvider, "next_turn", next_turn)
    row = asyncio.run(evaluate(CASES[0], "on", 1, HERE / "fixtures"))
    assert row["termination_reason"] == "TimeoutError" and not row["runtime_result_available"]
    assert row["tool_calls"] == row["reflection_calls"] == 1
    assert row["llm_calls"] == 3


def test_report_rejects_duplicate_missing_or_unpaired_rows(tmp_path):
    row = dict(case_id="a", repeat=1, fixture_sha256="fixture", input_sha256="input")
    def write(mode, rows):
        (tmp_path / f"{mode}.jsonl").write_text("\n".join(json.dumps({**item, "mode": mode}) for item in rows))
    write("off", [row])
    write("on", [row])
    assert len(load_rows(tmp_path, [{"case_id": "a"}], 1)) == 2
    for changed in ([row, row], [], [{**row, "input_sha256": "changed"}]):
        write("on", changed)
        with pytest.raises(ValueError):
            load_rows(tmp_path, [{"case_id": "a"}], 1)


def test_redaction_preserves_public_company_data():
    assert clean({"company_name": "삼성전자", "username": "private", "content": "secret alice@example.com"},
                 ("secret",)) == {"company_name": "삼성전자", "content": "[REDACTED] [REDACTED_EMAIL]"}


def test_rescore_preserves_observations_without_provider_or_settings(tmp_path, monkeypatch):
    import run_eval
    def forbidden(*args, **kwargs):
        pytest.fail("Offline rescoring must not construct settings or provider")
    monkeypatch.setattr(run_eval, "settings_for", forbidden)
    monkeypatch.setattr(run_eval, "ObservedProvider", forbidden)
    rows = [json.loads(line) for line in (HERE / "results/round1/off.jsonl").read_text().splitlines()]
    source = tmp_path / "original.jsonl"
    content = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    source.write_text(content)
    rescore_off(source, tmp_path)
    assert source.read_text() == content
    updated = [json.loads(line) for line in (tmp_path / "off.jsonl").read_text().splitlines()]
    for before, after in zip(rows, updated, strict=True):
        assert after["rescoring"]["llm_calls"] == after["rescoring"]["http_attempts"] == 0
        assert {key: value for key, value in after.items() if key not in {"verifier", "rescoring"}} == {
            key: value for key, value in before.items() if key != "verifier"}
        if before["narrative"] is None:
            assert after["verifier"]["passed"] is None
    assert any(before["verifier"]["passed"] != after["verifier"]["passed"]
               for before, after in zip(rows, updated, strict=True))
    with pytest.raises(FileExistsError):
        rescore_off(source, tmp_path)


@pytest.mark.parametrize("mode,repair,http_error", [("off", False, False), ("on", False, False),
    ("on", True, False), ("off", False, True)])
def test_forced_detail_probe_uses_real_sdk_runtime_and_failure_feedback(monkeypatch, tmp_path, mode, repair, http_error):
    from types import SimpleNamespace
    import httpx
    from openai import AsyncOpenAI
    from app.core.config import Settings
    import app.providers.openai as provider_module
    import run_eval

    requests = []
    context = None

    def handler(request):
        nonlocal context
        body = json.loads(request.content)
        requests.append(body)
        index = len(requests)
        if index == 1:
            context = json.loads(body["input"])
            receipt = body["tools"][0]["parameters"]["properties"]["receipt_number"]["enum"][0]
            output = [{"type": "function_call", "id": "fn-test", "call_id": "detail-test",
                       "name": "get_disclosure_detail", "arguments": json.dumps({"receipt_number": receipt})}]
        elif http_error:
            return httpx.Response(400, json={"error": {"message": "previous response unavailable",
                "type": "invalid_request_error", "code": "previous_response_not_found", "param": "previous_response_id"}})
        else:
            narrative = build_fallback_narrative(context)
            narrative.disclosure_summary = ("공시를 확인했습니다." if repair and index == 2
                                           else "공시 상세 자료가 제공되지 않아 추가 확인이 필요합니다.")
            output = [{"type": "message", "id": f"msg-{index}", "role": "assistant", "status": "completed",
                       "content": [{"type": "output_text", "text": narrative.model_dump_json(), "annotations": []}]}]
        return httpx.Response(200, json={"id": f"resp-{index}", "object": "response", "created_at": 1788480000,
            "model": "gpt-5.6-luna", "status": "completed", "output": output,
            "usage": {"input_tokens": 11, "output_tokens": 7, "total_tokens": 18}})

    def client(**kwargs):
        return AsyncOpenAI(api_key="test-key", http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))

    monkeypatch.setattr(provider_module, "AsyncOpenAI", client)
    monkeypatch.setattr(run_eval, "settings_for", lambda mode: Settings(_env_file=None, openai_api_key="test-key",
        agent_reflection_enabled=mode == "on", backend_event_url="", backend_internal_token=""))
    args = SimpleNamespace(mode=mode, out=tmp_path, fixtures=HERE / "fixtures")
    asyncio.run(run_eval.detail_failure_probe(args))
    row = json.loads((tmp_path / f"detail_failure_{mode}.jsonl").read_text())
    assert row["excluded_from_metrics"] and not row["included_in_metrics"]
    assert row["failure_reached"] and row["failure_feedback_delivered"]
    assert row["tool_calls"] == 1 and row["detail_calls"][0]["injected_failure"]
    assert row["llm_calls"] == row["http_attempts"] == len(requests) == 2 + int(repair)
    assert requests[0]["tool_choice"] == {"type": "function", "name": "get_disclosure_detail"}
    assert requests[1]["tool_choice"] == "auto"  # The first-call override was restored.
    assert ("previous_response_id" in requests[1]) is (mode == "off")
    feedback = [item for item in requests[1]["input"] if item.get("type") == "function_call_output"]
    assert len(feedback) == 1 and feedback[0]["call_id"] == "detail-test"
    assert json.loads(feedback[0]["output"])["status"] == "injected_failure"
    assert row["recovery_completed"] is (not http_error)
    if http_error:
        assert row["termination_reason"] == "model_error" and row["runtime_llm_calls"] == 1
        assert row["turns"][1]["error"]["body"]["code"] == "previous_response_not_found"
    else:
        assert row["termination_reason"] == "completed" and row["workflow_termination_reason"] == "partial_completed"
        assert row["reflection_calls"] == int(repair)
    if repair:
        assert requests[-1]["tools"] == [] and requests[-1]["tool_choice"] == "none"
        assert all(event["resolved"] for event in row["reflections"])
    with pytest.raises(FileExistsError):
        asyncio.run(run_eval.detail_failure_probe(args))
