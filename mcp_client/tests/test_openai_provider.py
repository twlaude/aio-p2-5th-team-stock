import json

import httpx
import pytest
from openai import AsyncOpenAI

from app.core.config import Settings
from app.providers.openai import OpenAINarrativeProvider


@pytest.mark.asyncio
async def test_uses_responses_api_with_structured_output():
    captured = {}
    narrative = {
        "one_line_summary": "관심 정도와 공식 근거를 함께 확인해야 합니다.",
        "news_summary": "최근 뉴스 요약입니다.",
        "disclosure_summary": "최근 공식 공시 요약입니다.",
        "community_summary": "커뮤니티 반응 요약입니다.",
        "personalized_checkpoints": None,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "id": "resp_test",
                "created_at": 1788480000,
                "model": "gpt-5.6-luna",
                "object": "response",
                "output": [
                    {
                        "id": "msg_test",
                        "content": [
                            {"annotations": [], "text": json.dumps(narrative), "type": "output_text"}
                        ],
                        "role": "assistant",
                        "status": "completed",
                        "type": "message",
                    }
                ],
                "parallel_tool_calls": False,
                "tool_choice": "none",
                "tools": [],
            },
        )

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = AsyncOpenAI(api_key="test-key", http_client=http_client)
    provider = OpenAINarrativeProvider(
        Settings(llm_provider="openai", openai_api_key="test-key"),
        client=client,
    )
    try:
        turn = await provider.first_turn(
            {"company": {"company_name": "삼성전자", "stock_code": "005930"}},
            [],
        )
    finally:
        await http_client.aclose()

    assert captured["model"] == "gpt-5.6-luna"
    assert captured["text"]["format"]["type"] == "json_schema"
    assert captured["reasoning"]["effort"] == "low"
    assert turn.narrative is not None
    assert turn.narrative.personalized_checkpoints is None
