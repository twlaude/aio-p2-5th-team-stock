import json
from typing import Any

import redis

from app.core.config import settings

_client = redis.from_url(settings.redis_url, decode_responses=True)

EVENTS_CHANNEL = "backend:live-events"
_SHORT_TERM_PREFIX = "backend:short_term:"


def _key(user_id: str) -> str:
    return f"{_SHORT_TERM_PREFIX}{user_id}"


def get_state(user_id: str) -> dict[str, Any]:
    raw = _client.get(_key(user_id))
    return json.loads(raw) if raw else {}


def set_state(user_id: str, **fields: Any) -> dict[str, Any]:
    state = get_state(user_id)
    state.update(fields)
    _client.set(_key(user_id), json.dumps(state), ex=settings.redis_ttl_seconds)
    publish_event({"type": "short_term", "user_id": user_id, **state})
    return state


def clear_state(user_id: str) -> None:
    _client.delete(_key(user_id))


def publish_event(event: dict[str, Any]) -> None:
    """실황 페이지(SSE)에 즉시 알리기 위한 Pub/Sub 발행. 구독자가 없어도 안전하다."""
    _client.publish(EVENTS_CHANNEL, json.dumps(event, ensure_ascii=False, default=str))


def snapshot_short_term() -> list[dict[str, Any]]:
    """지금 살아있는 단기 Memory 키를 전부 모아 남은 TTL과 함께 반환한다."""
    results: list[dict[str, Any]] = []
    for key in _client.scan_iter(match=f"{_SHORT_TERM_PREFIX}*"):
        raw = _client.get(key)
        if raw is None:
            continue
        ttl = _client.ttl(key)
        user_id = key[len(_SHORT_TERM_PREFIX):]
        state = json.loads(raw)
        results.append({"user_id": user_id, "ttl_seconds": ttl, **state})
    return results
