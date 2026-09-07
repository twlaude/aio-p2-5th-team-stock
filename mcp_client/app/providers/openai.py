from dataclasses import dataclass, field
from contextvars import ContextVar
import json
from typing import Any, Protocol

from openai import AsyncOpenAI

from app.core.config import Settings
from app.prompts import ANALYSIS_INSTRUCTIONS
from app.schemas.analysis import Narrative
from app.services.analysis_builder.narrative import build_fallback_narrative


class ProviderError(Exception):
    def __init__(
        self, message: str, response_id: str | None = None,
        input_tokens: int = 0, output_tokens: int = 0,
    ) -> None:
        super().__init__(message)
        self.response_id = response_id
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens


@dataclass(frozen=True)
class FunctionCall:
    call_id: str
    name: str
    arguments: str


@dataclass
class ModelTurn:
    response_id: str
    calls: list[FunctionCall] = field(default_factory=list)
    narrative: Narrative | None = None
    input_tokens: int = 0
    output_tokens: int = 0


class NarrativeProvider(Protocol):
    async def first_turn(self, context: dict[str, Any], tools: list[dict[str, Any]]) -> ModelTurn: ...

    async def next_turn(
        self,
        previous_response_id: str,
        tool_outputs: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ModelTurn: ...


class OpenAINarrativeProvider:
    def __init__(self, settings: Settings, client: AsyncOpenAI | None = None) -> None:
        self._settings = settings
        self._client = client or AsyncOpenAI(api_key=settings.openai_api_key or "missing-api-key")
        self._history: ContextVar[tuple[str, list[dict[str, Any]]] | None] = ContextVar(
            "narrative_response_history", default=None,
        )

    @staticmethod
    def _text_format() -> dict[str, Any]:
        return {
            "type": "json_schema",
            "name": "stock_information_analysis",
            "strict": True,
            "schema": Narrative.model_json_schema(),
        }

    @staticmethod
    def _normalize(response: Any) -> ModelTurn:
        usage = getattr(response, "usage", None)
        calls = [
            FunctionCall(call_id=item.call_id, name=item.name, arguments=item.arguments)
            for item in response.output
            if item.type == "function_call"
        ]
        narrative = None
        if not calls:
            try:
                narrative = Narrative.model_validate_json(response.output_text)
            except Exception as exc:
                raise ProviderError(
                    "Luna의 JSON 응답을 검증하지 못했습니다.", response.id,
                    int(getattr(usage, "input_tokens", 0) or 0),
                    int(getattr(usage, "output_tokens", 0) or 0),
                ) from exc
        return ModelTurn(
            response_id=response.id,
            calls=calls,
            narrative=narrative,
            input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
            output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
        )

    async def first_turn(self, context: dict[str, Any], tools: list[dict[str, Any]]) -> ModelTurn:
        if not self._settings.openai_api_key:
            raise ProviderError("OPENAI_API_KEY가 설정되지 않았습니다.")
        response = await self._client.responses.create(
            model=self._settings.openai_model,
            instructions=ANALYSIS_INSTRUCTIONS,
            input=json.dumps(context, ensure_ascii=False),
            tools=tools,
            tool_choice="auto" if tools else "none",
            parallel_tool_calls=False,
            reasoning={"effort": self._settings.openai_reasoning_effort},
            text={"format": self._text_format()},
            max_output_tokens=1200,
            store=False,
            **({"include": ["reasoning.encrypted_content"]} if self._settings.agent_reflection_enabled else {}),
        )
        self._remember(response, [{"role": "user", "content": json.dumps(context, ensure_ascii=False)}])
        return self._normalize(response)

    def _remember(self, response: Any, inputs: list[dict[str, Any]]) -> None:
        if self._settings.agent_reflection_enabled:
            self._history.set((response.id, [
                *inputs, *(item.model_dump(exclude_none=True) for item in response.output),
            ]))

    async def next_turn(
        self,
        previous_response_id: str,
        tool_outputs: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ModelTurn:
        options: dict[str, Any] = {"previous_response_id": previous_response_id, "input": tool_outputs}
        if self._settings.agent_reflection_enabled:
            history = self._history.get()
            if history is None or history[0] != previous_response_id:
                raise ProviderError("현재 요청의 이전 응답 컨텍스트를 찾지 못했습니다.")
            # store=False: replay request-local items, including encrypted reasoning, without persistence.
            options = {"input": [*history[1], *tool_outputs], "include": ["reasoning.encrypted_content"]}
        response = await self._client.responses.create(
            model=self._settings.openai_model,
            instructions=ANALYSIS_INSTRUCTIONS,
            **options,
            tools=tools,
            tool_choice="auto" if tools else "none",
            parallel_tool_calls=False,
            reasoning={"effort": self._settings.openai_reasoning_effort},
            text={"format": self._text_format()},
            max_output_tokens=1200,
            store=False,
        )
        self._remember(response, options["input"])
        return self._normalize(response)


class MockNarrativeProvider:
    """External calls 없이 Workflow와 Frontend 연결을 확인하는 local provider."""

    async def first_turn(self, context: dict[str, Any], tools: list[dict[str, Any]]) -> ModelTurn:
        return ModelTurn(response_id="mock-response", narrative=build_fallback_narrative(context))

    async def next_turn(
        self,
        previous_response_id: str,
        tool_outputs: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> ModelTurn:
        raise ProviderError("Mock Provider는 Tool Call을 생성하지 않습니다.")
