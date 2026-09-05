from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.clients.redis import client as redis_client
from app.core import db
from app.core.config import settings
from app.routers.admin.router import router as admin_router
from app.routers.analysis.router import router as analysis_router
from app.routers.auth.router import router as auth_router
from app.routers.memories.router import router as memories_router
from app.routers.profiles.router import router as profiles_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # DB 커넥션 풀·Redis 클라이언트는 만든 이벤트 루프가 살아있는 지금 시점에 닫아야 한다.
    # 안 닫고 루프가 죽으면(pytest의 TestClient 등) 백그라운드 정리 작업이 멈춘다.
    await db.close()
    await redis_client.close()


app = FastAPI(title="stock_insight backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(profiles_router, prefix=API_PREFIX)
app.include_router(memories_router, prefix=API_PREFIX)
app.include_router(analysis_router, prefix=API_PREFIX)
app.include_router(admin_router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok"}
