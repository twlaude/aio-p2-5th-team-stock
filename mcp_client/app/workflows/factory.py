import asyncio

from app.clients.base import MCPToolClient
from app.clients.community import CommunityMCPClient
from app.clients.disclosure import DisclosureMCPClient
from app.clients.news import NewsMCPClient
from app.clients.price import PriceMCPClient
from app.core.config import Settings
from app.providers import MockNarrativeProvider, OpenAINarrativeProvider
from app.runtime import StockAgentRuntime
from app.services.data_collector import DataCollector
from app.workflows.analysis import AnalysisWorkflow


def _base_clients(settings: Settings) -> dict[str, MCPToolClient]:
    timeout = settings.mcp_request_timeout_seconds
    return {
        "price": MCPToolClient("price_mcp", settings.price_mcp_url, timeout),
        "news": MCPToolClient("news_mcp", settings.news_mcp_url, timeout),
        "disclosure": MCPToolClient("disclosure_mcp", settings.disclosure_mcp_url, timeout),
        "community": MCPToolClient("community_mcp", settings.community_mcp_url, timeout),
    }


def build_workflow(settings: Settings) -> AnalysisWorkflow:
    clients = _base_clients(settings)
    price = PriceMCPClient(clients["price"])
    news = NewsMCPClient(clients["news"])
    disclosure = DisclosureMCPClient(clients["disclosure"])
    community = CommunityMCPClient(clients["community"])
    collector = DataCollector(price, news, disclosure, community)
    provider = (
        MockNarrativeProvider()
        if settings.llm_provider == "mock"
        else OpenAINarrativeProvider(settings)
    )
    agent = StockAgentRuntime(provider, disclosure, settings.max_agent_steps)
    return AnalysisWorkflow(settings, collector, agent)


async def mcp_connection_status(settings: Settings) -> dict[str, object]:
    clients = _base_clients(settings)

    async def check(name: str, client: MCPToolClient):
        try:
            tools = await client.list_tools()
            return name, {"status": "connected", "tools": tools}
        except Exception:
            return name, {"status": "unavailable", "tools": []}

    checks = await asyncio.gather(*(check(name, client) for name, client in clients.items()))
    services = dict(checks)
    return {
        "status": (
            "connected"
            if all(item["status"] == "connected" for item in services.values())
            else "partial"
        ),
        "services": services,
    }
