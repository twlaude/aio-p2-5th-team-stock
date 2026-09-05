import asyncio

import httpx
import pytest

from app.clients.mcp_client import client as mcp_client
from app.core.config import settings


def test_live_mode_connection_error_returns_external_api_error(client, monkeypatch):
    async def _raise_connect_error(self, *args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(settings, "mcp_client_mode", "live")
    monkeypatch.setattr(httpx.AsyncClient, "post", _raise_connect_error)

    response = client.post("/api/v1/analyses", json={"query": "삼성전자"})

    assert response.status_code == 500
    body = response.json()
    assert body["status"] == "external_api_error"
    assert body["error"]["service"] == "mcp_client"


def test_live_mode_timeout_returns_timeout_status(client, monkeypatch):
    async def _raise_timeout(self, *args, **kwargs):
        raise httpx.TimeoutException("timed out")

    monkeypatch.setattr(settings, "mcp_client_mode", "live")
    monkeypatch.setattr(httpx.AsyncClient, "post", _raise_timeout)

    response = client.post("/api/v1/analyses", json={"query": "삼성전자"})

    assert response.status_code == 504
    assert response.json()["status"] == "timeout"


def test_live_mode_request_id_mismatch_raises(monkeypatch):
    class _FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"request_id": "different-id"}

    async def _fake_post(self, *args, **kwargs):
        return _FakeResponse()

    monkeypatch.setattr(settings, "mcp_client_mode", "live")
    monkeypatch.setattr(httpx.AsyncClient, "post", _fake_post)

    async def scenario():
        with pytest.raises(mcp_client.MCPClientError):
            await mcp_client.fetch_common_analysis("삼성전자", "005930", None, "expected-id")

    asyncio.run(scenario())
