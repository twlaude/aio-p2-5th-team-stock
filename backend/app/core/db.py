import asyncio
from contextlib import asynccontextmanager
import sys

from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.core.async_resource import LoopScopedResource
from app.core.config import settings

if sys.platform == "win32":
    # psycopg3 비동기 모드는 SelectorEventLoop가 필요하다. Windows 기본값인
    # ProactorEventLoop에서는 "cannot use the 'ProactorEventLoop'" 에러로 커넥션이 안 열린다.
    # (uvicorn CLI로 띄우면 uvicorn이 이 정책을 무시하고 강제로 Proactor를 쓴다 — 그래서
    # 로컬 실행은 run.py를 쓴다. pytest의 TestClient는 이 정책을 그대로 따르므로 여기 둔다.)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def _open_pool() -> AsyncConnectionPool:
    pool = AsyncConnectionPool(settings.database_url, min_size=2, max_size=20, open=False)
    await pool.open()
    return pool


async def _close_pool(pool: AsyncConnectionPool) -> None:
    await pool.close()


_pool_resource: LoopScopedResource[AsyncConnectionPool] = LoopScopedResource(_open_pool, _close_pool)


@asynccontextmanager
async def get_cursor(commit: bool = False):
    pool = await _pool_resource.get()
    async with pool.connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            try:
                yield cur
                if commit:
                    await conn.commit()
            except Exception:
                await conn.rollback()
                raise


async def close() -> None:
    """앱 종료 시 호출한다(FastAPI lifespan shutdown). 커넥션을 연 루프가 살아있는
    동안 호출해야 한다 — 죽은 루프 위의 풀을 닫으려 하면 멈춘다."""
    await _pool_resource.close()
