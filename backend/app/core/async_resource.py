import asyncio
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class LoopScopedResource(Generic[T]):
    """이벤트 루프 하나당 자원(커넥션 풀 등) 하나만 만들어 재사용한다.

    운영 환경은 이벤트 루프가 하나라 사실상 싱글턴이다. pytest는 TestClient를
    만들 때마다(테스트 함수마다) 새 이벤트 루프를 띄우는데, asyncpg/psycopg
    비동기 커넥션은 자신을 만든 루프에 묶인다. 루프가 바뀌면 이전 자원은
    "그 루프가 이미 죽어있는" 상태라 여기서 정상적으로 close()할 수 없다
    (다른 루프에서 close()를 시도하면 크로스 루프 문제로 멈춘다) — 그래서
    루프가 바뀌면 이전 값은 그냥 버리고 새로 만든다. 정말 깔끔하게 닫고
    싶으면(운영 서버 종료 시 등) 자신이 만들어진 그 루프 위에서 close()를
    명시적으로 호출한다.
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
