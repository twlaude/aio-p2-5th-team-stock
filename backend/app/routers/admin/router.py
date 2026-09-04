from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from redis import asyncio as redis_asyncio

from app.clients.redis import client as redis_client
from app.core.admin_auth import require_admin
from app.core.config import settings
from app.repositories import analysis_repository
from app.routers.admin.live_status_page import render_live_status_html

router = APIRouter(prefix="/admin", tags=["admin"])

_KEEPALIVE_SECONDS = 15


@router.get("/live-status", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
def live_status_page() -> str:
    return render_live_status_html(settings.mcp_server_urls)


@router.get("/live-status/snapshot", dependencies=[Depends(require_admin)])
def live_status_snapshot() -> dict:
    return {
        "short_term": redis_client.snapshot_short_term(),
        "recent_runs": analysis_repository.list_recent(limit=30),
    }


@router.get("/live-status/stream", dependencies=[Depends(require_admin)])
async def live_status_stream(request: Request) -> StreamingResponse:
    async def event_source():
        client = redis_asyncio.from_url(settings.redis_url, decode_responses=True)
        pubsub = client.pubsub()
        await pubsub.subscribe(redis_client.EVENTS_CHANNEL)
        try:
            while True:
                if await request.is_disconnected():
                    break
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=_KEEPALIVE_SECONDS)
                if message is None:
                    yield ": keep-alive\n\n"
                    continue
                yield f"data: {message['data']}\n\n"
        finally:
            await pubsub.unsubscribe(redis_client.EVENTS_CHANNEL)
            await pubsub.close()
            await client.close()

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
