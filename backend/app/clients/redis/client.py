"""단기 State 저장소. Redis 연결 전까지 프로세스 메모리로 대체한다(골격 단계)."""
from typing import Any

_STATE: dict[str, dict[str, Any]] = {}


def get_state(user_id: str) -> dict[str, Any]:
    return dict(_STATE.get(user_id, {}))


def set_state(user_id: str, **fields: Any) -> dict[str, Any]:
    state = _STATE.setdefault(user_id, {})
    state.update(fields)
    return dict(state)


def clear_state(user_id: str) -> None:
    _STATE.pop(user_id, None)
