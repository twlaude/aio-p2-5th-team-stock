from fastapi import FastAPI

from app.routers.analysis.router import router as analysis_router
from app.routers.auth.router import router as auth_router
from app.routers.memories.router import router as memories_router
from app.routers.profiles.router import router as profiles_router

app = FastAPI(title="stock_insight backend")

API_PREFIX = "/api/v1"
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(profiles_router, prefix=API_PREFIX)
app.include_router(memories_router, prefix=API_PREFIX)
app.include_router(analysis_router, prefix=API_PREFIX)


@app.get("/health")
def health():
    return {"status": "ok"}
