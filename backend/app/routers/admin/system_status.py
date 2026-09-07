import asyncio
from datetime import datetime, timezone
from time import perf_counter

import httpx
import redis.asyncio as redis

from app.core.config import _MCP_SERVER_PORTS, settings
from app.repositories import system_repository

_ROLES = {
    "mcp_client": "4개 MCP를 묶어서 LLM 분석을 만드는 곳",
    "price_mcp": "주가·시세(한국투자증권 API)",
    "news_mcp": "뉴스 검색(네이버)",
    "disclosure_mcp": "공시(DART)",
    "community_mcp": "커뮤니티 여론 지수(FGI)",
}


async def _health(client: httpx.AsyncClient, name: str, url: httpx.URL) -> dict:
    started = perf_counter()
    try:
        async with asyncio.timeout(3):
            response = await client.get(url)
            response.raise_for_status()
            detail = response.json()
            status = "ok" if isinstance(detail, dict) and detail.get("status") == "ok" else "down"
    except Exception as exc:
        status, detail = "down", {"error": str(exc) or type(exc).__name__}
    return {"name": name, "role": _ROLES[name], "url": str(url), "status": status,
            "latency_ms": round((perf_counter() - started) * 1000, 1), "detail": detail}


async def _services() -> list[dict]:
    base = httpx.URL(settings.mcp_client_url).copy_with(path="/health", query=None, fragment=None)
    urls = {"mcp_client": base, **{name: base.copy_with(port=port) for name, port in _MCP_SERVER_PORTS.items()}}
    async with httpx.AsyncClient(timeout=3) as client:
        return await asyncio.gather(*(_health(client, name, url) for name, url in urls.items()))


async def _postgres() -> tuple[dict, dict]:
    try:
        async with asyncio.timeout(5):
            return await system_repository.snapshot()
    except Exception as exc:
        return ({"ok": False, "error": str(exc) or type(exc).__name__, "version": "",
                 "databases": [], "tables": [], "analysis": {
                     "total": 0, "last_24h": 0, "success_rate_24h": None, "last_requested_at": None}},
                {"recent": [], "by_service_7d": []})


async def _redis() -> dict:
    result = {"ok": False, "error": None, "keys_in_db": 0, "used_memory_human": "",
              "connected_clients": 0, "uptime_days": 0, "short_term_keys": 0, "last_event_at": None}
    try:
        async with asyncio.timeout(5):
            async with redis.from_url(settings.redis_url, decode_responses=True, socket_timeout=3) as client:
                info = await client.info()
                result.update(keys_in_db=await client.dbsize(), uptime_days=info["uptime_in_days"],
                              **{key: info[key] for key in ("used_memory_human", "connected_clients")})
                keys = {key async for key in client.scan_iter(match="backend:short_term:*")}
                result.update(short_term_keys=len(keys), last_event_at=await client.get("backend:last_event_at"), ok=True)
    except Exception as exc:
        result["error"] = str(exc) or type(exc).__name__
    return result


async def snapshot() -> dict:
    """상태 조회를 동시에 실행하고 PG·Redis 장애를 해당 블록에만 담는다."""
    services, (postgres, failures), redis_status = await asyncio.gather(_services(), _postgres(), _redis())
    return {"checked_at": datetime.now(timezone.utc).isoformat(), "services": services,
            "postgres": postgres, "redis": redis_status, "failures": failures}
