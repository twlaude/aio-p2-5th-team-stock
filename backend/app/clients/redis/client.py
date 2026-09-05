import json
from typing import Any

import redis.asyncio as redis

from app.core.async_resource import LoopScopedResource
from app.core.config import settings

EVENTS_CHANNEL = "backend:live-events"
_SHORT_TERM_PREFIX = "backend:short_term:"


async def _open_client() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


async def _close_client(client: redis.Redis) -> None:
    await client.aclose()


_client_resource: LoopScopedResource[redis.Redis] = LoopScopedResource(_open_client, _close_client)


def _key(user_id: str) -> str:
    return f"{_SHORT_TERM_PREFIX}{user_id}"


async def get_state(user_id: str) -> dict[str, Any]:
    client = await _client_resource.get()
    raw = await client.get(_key(user_id))
    return json.loads(raw) if raw else {}


async def set_state(user_id: str, **fields: Any) -> dict[str, Any]:
    state = await get_state(user_id)
    state.update(fields)
    client = await _client_resource.get()
    await client.set(_key(user_id), json.dumps(state), ex=settings.redis_ttl_seconds)
    await publish_event({"type": "short_term", "user_id": user_id, **state})
    return state


async def clear_state(user_id: str) -> None:
    client = await _client_resource.get()
    await client.delete(_key(user_id))


async def publish_event(event: dict[str, Any]) -> None:
    """실황 페이지(SSE)에 즉시 알리기 위한 Pub/Sub 발행. 구독자가 없어도 안전하다."""
    client = await _client_resource.get()
    await client.publish(EVENTS_CHANNEL, json.dumps(event, ensure_ascii=False, default=str))


async def snapshot_short_term() -> list[dict[str, Any]]:
    """지금 살아있는 단기 Memory 키를 전부 모아 남은 TTL과 함께 반환한다."""
    client = await _client_resource.get()
    results: list[dict[str, Any]] = []
    async for key in client.scan_iter(match=f"{_SHORT_TERM_PREFIX}*"):
        raw = await client.get(key)
        if raw is None:
            continue
        ttl = await client.ttl(key)
        user_id = key[len(_SHORT_TERM_PREFIX):]
        state = json.loads(raw)
        results.append({"user_id": user_id, "ttl_seconds": ttl, **state})
    return results


async def close() -> None:
    """앱 종료 시 호출한다(FastAPI lifespan shutdown). 만든 루프가 살아있는 동안 호출한다."""
    await _client_resource.close()
