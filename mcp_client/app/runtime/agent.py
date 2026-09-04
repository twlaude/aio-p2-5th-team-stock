from dataclasses import dataclass, field
import json
from typing import Any

from app.agents import StockAnalysisAgent
from app.clients.base import MCPClientError
from app.clients.disclosure import DisclosureMCPClient
from app.providers.openai import NarrativeProvider
from app.schemas.analysis import Narrative, ToolFailure
from app.services.analysis_builder.narrative import build_fallback_narrative
from app.services.progress_reporter import ProgressReporter


@dataclass
class AgentResult:
    narrative: Narrative
    termination_reason: str
    llm_calls: int = 0
    tool_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    completed_tools: list[str] = field(default_factory=list)
    failed_tools: list[str] = field(default_factory=list)
    failures: list[ToolFailure] = field(default_factory=list)


class StockAgentRuntime:
    def __init__(
        self,
        provider: NarrativeProvider,
        disclosure: DisclosureMCPClient,
        max_steps: int,
    ) -> None:
        self.provider = provider
        self.disclosure = disclosure
        self.max_steps = max_steps
        self.profile = StockAnalysisAgent()

    @staticmethod
    def _tools(receipt_numbers: list[str]) -> list[dict[str, Any]]:
        if not receipt_numbers:
            return []
        return [
            {
                "type": "function",
                "name": "get_disclosure_detail",
                "description": "최근 공시 제목만으로 설명이 부족할 때 공식 공시 상세 내용을 조회합니다.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "receipt_number": {
                            "type": "string",
                            "enum": receipt_numbers,
                            "description": "기본 조회 결과에 포함된 DART 접수번호",
                        }
                    },
                    "required": ["receipt_number"],
                    "additionalProperties": False,
                },
                "strict": True,
            }
        ]

    async def run(
        self,
        context: dict[str, Any],
        receipt_numbers: list[str],
        reporter: ProgressReporter,
    ) -> AgentResult:
        ordered_receipts = list(dict.fromkeys(receipt_numbers))[:5]
        allowed_receipts = set(ordered_receipts)
        tools = self._tools(ordered_receipts)
        fallback = build_fallback_narrative(context)
        result = AgentResult(narrative=fallback, termination_reason="model_error")

        await reporter.publish(
            "llm_started",
            "analyzing",
            "running",
            "수집한 자료를 종합하고 있어요.",
            70,
        )
        try:
            turn = await self.provider.first_turn(context, tools)
        except Exception:
            result.failures.append(
                ToolFailure(
                    service="openai",
                    status="model_error",
                    message="Luna 분석을 완료하지 못해 규칙 기반 설명을 제공합니다.",
                    retryable=True,
                )
            )
            await reporter.publish(
                "llm_failed",
                "analyzing",
                "partial_success",
                "AI 설명 생성에 실패해 기본 설명을 사용했어요.",
                90,
                service="openai",
            )
            return result

        result.llm_calls += 1
        result.input_tokens += turn.input_tokens
        result.output_tokens += turn.output_tokens
        used_receipts: set[str] = set()

        for _step in range(1, self.max_steps + 1):
            if not turn.calls:
                if turn.narrative is None:
                    result.failures.append(
                        ToolFailure(
                            service="openai",
                            status="model_error",
                            message="Luna가 분석 문장을 반환하지 않았습니다.",
                            retryable=True,
                        )
                    )
                    return result
                result.narrative = turn.narrative
                result.termination_reason = "completed"
                await reporter.publish(
                    "llm_completed",
                    "analyzing",
                    "running",
                    "자료 종합을 마쳤어요.",
                    90,
                    service="openai",
                )
                return result

            outputs = []
            for call in turn.calls:
                try:
                    if call.name not in self.profile.allowed_tools:
                        raise ValueError("허용되지 않은 Tool입니다.")
                    arguments = json.loads(call.arguments)
                    if not isinstance(arguments, dict):
                        raise ValueError("Tool arguments는 JSON Object여야 합니다.")
                    receipt_number = arguments.get("receipt_number")
                    if receipt_number not in allowed_receipts:
                        raise ValueError("기본 조회 결과에 없는 접수번호입니다.")
                    if receipt_number in used_receipts:
                        raise ValueError("같은 공시를 반복 조회할 수 없습니다.")
                except (json.JSONDecodeError, TypeError, ValueError) as error:
                    result.termination_reason = "invalid_tool_call"
                    result.failures.append(
                        ToolFailure(
                            service="openai",
                            status="invalid_tool_call",
                            message=str(error),
                            retryable=False,
                        )
                    )
                    return result

                used_receipts.add(receipt_number)
                await reporter.publish(
                    "tool_started",
                    "analyzing",
                    "running",
                    "중요한 공시의 상세 근거를 확인하고 있어요.",
                    80,
                    tool_name=call.name,
                    service="disclosure_mcp",
                )
                try:
                    detail = await self.disclosure.get_disclosure_detail(receipt_number)
                except MCPClientError as error:
                    detail = {
                        "status": error.code,
                        "error": {"message": error.message, "retryable": error.retryable},
                    }
                    result.failed_tools.append(call.name)
                    result.failures.append(
                        ToolFailure(
                            service=error.service,
                            status=error.code,
                            message=error.message,
                            retryable=error.retryable,
                        )
                    )
                else:
                    result.completed_tools.append(call.name)
                result.tool_calls += 1
                outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": json.dumps(detail, ensure_ascii=False),
                    }
                )

            active_tools = [] if len(used_receipts) >= 2 else tools
            try:
                turn = await self.provider.next_turn(turn.response_id, outputs, active_tools)
            except Exception:
                result.termination_reason = "model_error"
                result.failures.append(
                    ToolFailure(
                        service="openai",
                        status="model_error",
                        message="상세 공시 확인 후 Luna 분석을 완료하지 못했습니다.",
                        retryable=True,
                    )
                )
                return result
            result.llm_calls += 1
            result.input_tokens += turn.input_tokens
            result.output_tokens += turn.output_tokens

        if not turn.calls and turn.narrative is not None:
            result.narrative = turn.narrative
            result.termination_reason = "completed"
            return result
        result.termination_reason = "max_steps_exceeded"
        result.failures.append(
            ToolFailure(
                service="openai",
                status="max_steps_exceeded",
                message="Agent 최대 반복 횟수를 초과해 기본 설명을 제공합니다.",
                retryable=False,
            )
        )
        return result
