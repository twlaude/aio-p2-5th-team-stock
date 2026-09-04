import logging

from fastapi import FastAPI

from app.api import router


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="Stock Analysis MCP Client",
    version="0.1.0",
    description="Price, News, Disclosure, Community MCP 통합 분석 서버",
)
app.include_router(router)
