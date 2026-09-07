import asyncio
import json

import httpx
from openai import AsyncOpenAI
import pytest

from app.core.config import Settings
from app.providers.openai import OpenAINarrativeProvider, ProviderError


NARRATIVE = {
    "one_line_summary": "현재 관심과 공식 자료를 함께 확인해야 합니다.",
    "news_summary": "관련 뉴스를 확인했습니다.",
    "disclosure_summary": "공식 공시를 확인했습니다.",
    "community_summary": "커뮤니티 반응은 사실 확인 자료가 아닙니다.",
    "personalized_checkpoints": None,
}


def response(response_id, text):
    return httpx.Response(200, json={
        "id": response_id, "created_at": 1788480000, "model": "gpt-5.6-luna", "object": "response",
        "output": [{"id": f"msg_{response_id}", "role": "assistant", "status": "completed", "type": "message",
                    "content": [{"annotations": [], "text": text, "type": "output_text"}]}],
        "usage": {"input_tokens": 11, "output_tokens": 7, "total_tokens": 18},
    })


@pytest.mark.asyncio
@pytest.mark.parametrize("enabled", [False, True])
async def test_schema_error_retains_id_and_continuation_replays_only_when_enabled(enabled):
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return response("invalid-json" if len(requests) == 1 else "fixed", "{" if len(requests) == 1 else json.dumps(NARRATIVE))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        provider = OpenAINarrativeProvider(
            Settings(openai_api_key="test-key", agent_reflection_enabled=enabled),
            client=AsyncOpenAI(api_key="test-key", http_client=http),
        )
        with pytest.raises(ProviderError) as caught:
            await provider.first_turn({"company": "삼성전자"}, [])
        assert caught.value.response_id == "invalid-json"
        assert (caught.value.input_tokens, caught.value.output_tokens) == (11, 7)
        feedback = [{"role": "user", "content": "형식 오류를 수정하세요."}]
        turn = await provider.next_turn(caught.value.response_id, feedback, [])
        assert turn.narrative.model_dump() == NARRATIVE
        second = requests[1]
        assert second["store"] is False and second["tools"] == []
        assert second["tool_choice"] == "none" and second["parallel_tool_calls"] is False
        if enabled:
            assert "previous_response_id" not in second
            assert second["include"] == ["reasoning.encrypted_content"]
            assert json.loads(second["input"][0]["content"]) == {"company": "삼성전자"}
            assert second["input"][1]["content"][0]["text"] == "{"
            assert second["input"][-1] == feedback[0]
        else:
            assert second["previous_response_id"] == "invalid-json"
            assert second["input"] == feedback and "include" not in second


@pytest.mark.asyncio
async def test_request_context_isolated_and_function_outputs_can_mix_with_messages():
    requests = []

    def handler(request):
        body = json.loads(request.content)
        requests.append(body)
        context = json.loads(body["input"] if isinstance(body["input"], str) else body["input"][0]["content"])
        if isinstance(body["input"], str):
            result = json.loads(response(context["request"], "").content)
            result["output"] = [
                {"type": "reasoning", "id": "reasoning", "summary": [], "encrypted_content": "encrypted-test"},
                {"type": "function_call", "id": "function", "call_id": "detail", "name": "get_disclosure_detail", "arguments": "{}"},
            ]
            return httpx.Response(200, json=result)
        assert body["input"][1]["encrypted_content"] == "encrypted-test"
        assert body["input"][2]["type"] == "function_call"
        assert body["input"][3]["type"] == "function_call_output"
        assert body["input"][4]["content"] == context["request"]
        return response("fixed-" + context["request"], json.dumps(NARRATIVE))

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http:
        provider = OpenAINarrativeProvider(
            Settings(openai_api_key="test-key", agent_reflection_enabled=True),
            client=AsyncOpenAI(api_key="test-key", http_client=http),
        )

        async def run(request_id):
            turn = await provider.first_turn({"request": request_id}, [])
            await asyncio.sleep(0)
            return await provider.next_turn(turn.response_id, [
                {"type": "function_call_output", "call_id": "detail", "output": "{}"},
                {"role": "user", "content": request_id},
            ], [])

        turns = await asyncio.gather(run("first"), run("second"))
        assert [turn.response_id for turn in turns] == ["fixed-first", "fixed-second"]
        with pytest.raises(ProviderError, match="이전 응답 컨텍스트"):
            await provider.next_turn("first", [], [])
        assert len(requests) == 4
