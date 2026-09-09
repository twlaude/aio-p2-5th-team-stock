import asyncio
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class LoopScopedResource(Generic[T]):
    """같은 이벤트 루프에서 자원을 재사용하고, 루프가 바뀌면 새로 만든다.
    이전 자원의 close()는 생성한 루프에서 호출해야 한다.
    """

    def __init__(self, factory: Callable[[], Awaitable[T]], closer: Callable[[T], Awaitable[None]]) -> None:
        self._factory = factory
        self._closer = closer
        self._value: T | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._lock = asyncio.Lock()

    async def get(self) -> T:
        loop = asyncio.get_running_loop()
        if self._value is not None and self._loop is loop:
            return self._value
        async with self._lock:
            if self._value is not None and self._loop is loop:
                return self._value
            # 루프가 바뀐 경우 이전 값은 정리하지 않고 버린다(위 설명 참고).
            self._value = await self._factory()
            self._loop = loop
            return self._value

    async def close(self) -> None:
        """지금 이 자원을 만든 루프 위에서 호출해야 한다(운영 서버 종료 훅 등)."""
        if self._value is not None:
            await self._closer(self._value)
            self._value = None
            self._loop = None
