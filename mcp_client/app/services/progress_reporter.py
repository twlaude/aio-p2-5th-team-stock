from datetime import datetime, timezone
import logging
from typing import Any

import httpx

from app.core.config import Settings


logger = logging.getLogger(__name__)


class ProgressReporter:
    """Collect safe trace events and optionally forward them to Backend."""

    def __init__(self, settings: Settings, request_id: str, run_id: str) -> None:
        self._settings = settings
        self.request_id = request_id
        self.run_id = run_id
        self.events: list[dict[str, Any]] = []

    async def publish(
        self,
        event: str,
        step: str,
        status: str,
        message: str,
        progress_percent: int,
        *,
        tool_name: str | None = None,
        service: str | None = None,
    ) -> None:
        payload = {
            "request_id": self.request_id,
            "run_id": self.run_id,
            "event": event,
            "step": step,
            "status": status,
            "message": message,
            "progress_percent": max(0, min(100, progress_percent)),
            "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        if tool_name:
            payload["tool_name"] = tool_name
        if service:
            payload["service"] = service
        self.events.append(payload)

        if not self._settings.backend_event_url:
            return
        headers = {}
        if self._settings.backend_internal_token:
            headers["authorization"] = f"Bearer {self._settings.backend_internal_token}"
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.post(
                    self._settings.backend_event_url,
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
        except httpx.HTTPError:
            logger.warning(
                "Backend 진행 이벤트 전송 실패 request_id=%s event=%s",
                self.request_id,
                event,
            )
