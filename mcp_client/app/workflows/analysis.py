import asyncio
from datetime import datetime, timezone
from time import monotonic
from typing import Any
from uuid import uuid4

from app.core.config import Settings
from app.runtime import StockAgentRuntime
from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    CommonAnalysis,
    PartialFailure,
    PriceSnapshot,
    TraceSummary,
)
from app.services.analysis_builder import (
    calculate_evidence_level,
    calculate_market_temperature,
    collect_sources,
)
from app.services.data_collector import DataCollector
from app.services.progress_reporter import ProgressReporter


class RequiredPriceError(Exception):
    pass


class AnalysisWorkflow:
    def __init__(
        self,
        settings: Settings,
        collector: DataCollector,
        agent: StockAgentRuntime,
    ) -> None:
        self.settings = settings
        self.collector = collector
        self.agent = agent

    @staticmethod
    def _context(
        request: AnalysisRequest,
        data: Any,
        temperature: Any,
        evidence: Any,
    ) -> dict[str, Any]:
        return {
            "goal": "추천 없이 현재 관심 정도와 확인할 근거를 설명한다.",
            "company": request.company.model_dump(),
            "investment_profile": (
                request.investment_profile.model_dump() if request.investment_profile else None
            ),
            "market_temperature": temperature.model_dump(),
            "evidence_level": evidence.model_dump(),
            "data": {
                "price": data.price,
                "news": {
                    **data.news,
                    "articles": (data.news.get("articles") or [])[:5],
                },
                "disclosures": {
                    **data.disclosures,
                    "disclosures": (data.disclosures.get("disclosures") or [])[:5],
                },
                "annual_report": {
                    **data.annual_report,
                    "matched_passages": (data.annual_report.get("matched_passages") or [])[:5],
                },
                "community": {
                    key: value
                    for key, value in data.community.items()
                    if key
                    in {
                        "status",
                        "sample_status",
                        "period",
                        "sample_size",
                        "sentiment",
                        "top_topics",
                        "representative_evidence",
                        "fgi_latest",
                        "source_name",
                        "collected_at",
                    }
                },
            },
        }

    async def run(self, request: AnalysisRequest) -> AnalysisResponse:
        started = monotonic()
        run_id = str(uuid4())
        reporter = ProgressReporter(self.settings, request.request_id, run_id)
        await reporter.publish(
            "workflow_started",
            "starting",
            "running",
            "기업 분석을 시작했어요.",
            5,
        )

        try:
            async with asyncio.timeout(self.settings.workflow_timeout_seconds):
                data = await self.collector.collect(request.company, reporter)
                if data.price.get("status") != "success":
                    raise RequiredPriceError("현재 가격을 확인하지 못했습니다.")

                temperature = calculate_market_temperature(data)
                evidence = calculate_evidence_level(data, temperature.data_coverage)
                context = self._context(request, data, temperature, evidence)
                receipt_numbers = [
                    str(item.get("receipt_number"))
                    for item in (data.disclosures.get("disclosures") or [])
                    if item.get("receipt_number")
                ]
                agent_result = await self.agent.run(context, receipt_numbers, reporter)
        except TimeoutError:
            await reporter.publish(
                "workflow_failed",
                "timeout",
                "failed",
                "분석 시간이 초과되었습니다.",
                100,
            )
            raise

        failures = [
            PartialFailure(service=item.service, status=item.status, message=item.message)
            for item in [*data.failures, *agent_result.failures]
        ]
        status = "partial_success" if failures else "success"
        termination_reason = (
            agent_result.termination_reason
            if agent_result.termination_reason != "completed"
            else ("partial_completed" if failures else "completed")
        )

        narrative = agent_result.narrative
        if request.investment_profile is None:
            narrative.personalized_checkpoints = None
        elif narrative.personalized_checkpoints is None:
            from app.services.analysis_builder.narrative import build_fallback_narrative

            narrative.personalized_checkpoints = build_fallback_narrative(
                context
            ).personalized_checkpoints

        price = PriceSnapshot(
            current_price=int(data.price["current_price"]),
            change=int(data.price["change"]),
            change_rate=float(data.price["change_rate"]),
            as_of=str(data.price["as_of"]),
            source_name=data.price.get("source_name"),
            volume_basis=data.price.get("volume_basis"),
            volume_as_of=data.price.get("volume_as_of"),
        )
        common = CommonAnalysis(
            one_line_summary=narrative.one_line_summary,
            market_temperature=temperature,
            evidence_level=evidence,
            news_summary=narrative.news_summary,
            disclosure_summary=narrative.disclosure_summary,
            community_summary=narrative.community_summary,
        )
        duration_ms = round((monotonic() - started) * 1000)
        response = AnalysisResponse(
            request_id=request.request_id,
            run_id=run_id,
            status=status,
            termination_reason=termination_reason,
            company=request.company,
            price=price,
            common_analysis=common,
            personalized_checkpoints=narrative.personalized_checkpoints,
            sources=collect_sources(data),
            partial_failures=failures,
            collected_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            trace_summary=TraceSummary(
                tool_calls=len(data.completed_tools) + len(data.failed_tools) + agent_result.tool_calls,
                llm_calls=agent_result.llm_calls,
                completed_tools=[*data.completed_tools, *agent_result.completed_tools],
                failed_tools=[*data.failed_tools, *agent_result.failed_tools],
                duration_ms=duration_ms,
            ),
        )
        await reporter.publish(
            "workflow_completed",
            "completed",
            status,
            "기업 분석을 완료했어요.",
            100,
        )
        return response
