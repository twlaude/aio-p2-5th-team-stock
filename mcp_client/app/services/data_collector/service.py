import asyncio
from collections.abc import Awaitable
from typing import Any

from app.clients.base import MCPClientError
from app.clients.community import CommunityMCPClient
from app.clients.disclosure import DisclosureMCPClient
from app.clients.news import NewsMCPClient
from app.clients.price import PriceMCPClient
from app.schemas.analysis import CollectedData, CompanyRef, ToolFailure
from app.services.progress_reporter import ProgressReporter


class DataCollector:
    def __init__(
        self,
        price: PriceMCPClient,
        news: NewsMCPClient,
        disclosure: DisclosureMCPClient,
        community: CommunityMCPClient,
    ) -> None:
        self.price = price
        self.news = news
        self.disclosure = disclosure
        self.community = community

    async def collect(self, company: CompanyRef, reporter: ProgressReporter) -> CollectedData:
        company_name, stock_code = company.company_name, company.stock_code
        jobs: dict[str, tuple[str, Awaitable[dict[str, Any]]]] = {
            "get_stock_quote": (
                "price_mcp",
                self.price.get_stock_quote(company_name, stock_code),
            ),
            "search_news": (
                "news_mcp",
                self.news.search_news(company_name, stock_code),
            ),
            "get_recent_disclosures": (
                "disclosure_mcp",
                self.disclosure.get_recent_disclosures(company_name, stock_code),
            ),
            "get_material_disclosures": (
                "disclosure_mcp",
                self.disclosure.get_material_disclosures(company_name, stock_code),
            ),
            "search_annual_report": (
                "disclosure_mcp",
                self.disclosure.search_annual_report(company_name, stock_code),
            ),
            "get_community_reaction": (
                "community_mcp",
                self.community.get_community_reaction(company_name, stock_code),
            ),
        }

        await reporter.publish(
            "collection_started",
            "collecting",
            "running",
            "가격·뉴스·공시·커뮤니티 자료를 확인하고 있어요.",
            10,
        )

        async def run_one(tool_name: str, service: str, job: Awaitable[dict[str, Any]]):
            await reporter.publish(
                "tool_started",
                "collecting",
                "running",
                f"{service} 자료를 확인하고 있어요.",
                15,
                tool_name=tool_name,
                service=service,
            )
            try:
                result = await job
            except MCPClientError as error:
                await reporter.publish(
                    "tool_failed",
                    "collecting",
                    "partial_success",
                    error.message,
                    55,
                    tool_name=tool_name,
                    service=service,
                )
                return tool_name, None, ToolFailure(
                    service=error.service,
                    status=error.code,
                    message=error.message,
                    retryable=error.retryable,
                )
            except Exception:
                message = f"{service} 자료를 처리하지 못했습니다."
                await reporter.publish(
                    "tool_failed",
                    "collecting",
                    "partial_success",
                    message,
                    55,
                    tool_name=tool_name,
                    service=service,
                )
                return tool_name, None, ToolFailure(
                    service=service,
                    status="internal_error",
                    message=message,
                    retryable=False,
                )
            await reporter.publish(
                "tool_completed",
                "collecting",
                "running",
                f"{service} 자료 확인을 마쳤어요.",
                55,
                tool_name=tool_name,
                service=service,
            )
            return tool_name, result, None

        outcomes = await asyncio.gather(
            *(run_one(name, service, job) for name, (service, job) in jobs.items())
        )

        results: dict[str, dict[str, Any]] = {}
        failures: list[ToolFailure] = []
        completed_tools: list[str] = []
        failed_tools: list[str] = []
        for tool_name, result, failure in outcomes:
            if failure:
                failures.append(failure)
                failed_tools.append(tool_name)
                results[tool_name] = {"status": "external_api_error"}
            else:
                results[tool_name] = result or {"status": "no_data"}
                completed_tools.append(tool_name)

        return CollectedData(
            price=results["get_stock_quote"],
            news=results["search_news"],
            disclosures=results["get_recent_disclosures"],
            material_disclosures=results["get_material_disclosures"],
            annual_report=results["search_annual_report"],
            community=results["get_community_reaction"],
            failures=failures,
            completed_tools=completed_tools,
            failed_tools=failed_tools,
        )
