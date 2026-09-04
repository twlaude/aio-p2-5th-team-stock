import json
from typing import Any

import redis

from app.core.config import settings

_client = redis.from_url(settings.redis_url, decode_responses=True)


def _key(user_id: str) -> str:
    return f"backend:short_term:{user_id}"


def get_state(user_id: str) -> dict[str, Any]:
    raw = _client.get(_key(user_id))
    return json.loads(raw) if raw else {}


def set_state(user_id: str, **fields: Any) -> dict[str, Any]:
    state = get_state(user_id)
    state.update(fields)
    _client.set(_key(user_id), json.dumps(state), ex=settings.redis_ttl_seconds)
    return state


def clear_state(user_id: str) -> None:
    _client.delete(_key(user_id))
