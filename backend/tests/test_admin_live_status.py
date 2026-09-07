import base64


def _auth_header(username: str, password: str) -> dict[str, str]:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


def test_live_status_requires_auth(client):
    response = client.get("/api/v1/admin/live-status")
    assert response.status_code == 401


def test_live_status_rejects_wrong_credentials(client):
    response = client.get("/api/v1/admin/live-status", headers=_auth_header("admin", "wrong"))
    assert response.status_code == 401


def test_live_status_page_loads_with_correct_credentials(client):
    response = client.get("/api/v1/admin/live-status", headers=_auth_header("admin", "change-me"))
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_snapshot_shape(client):
    response = client.get("/api/v1/admin/live-status/snapshot", headers=_auth_header("admin", "change-me"))
    assert response.status_code == 200
    body = response.json()
    assert "short_term" in body
    assert "recent_runs" in body
    assert isinstance(body["short_term"], list)
    assert isinstance(body["recent_runs"], list)


def test_snapshot_requires_auth(client):
    response = client.get("/api/v1/admin/live-status/snapshot")
    assert response.status_code == 401


def test_system_requires_auth(client):
    assert client.get("/api/v1/admin/live-status/system").status_code == 401


def test_system_shape_and_independent_health(client, monkeypatch):
    import httpx
    from app.routers.admin import system_status

    urls = []

    async def health(self, url):
        urls.append(url)
        request = httpx.Request("GET", url)
        if url.port == 8020:
            raise httpx.ConnectError("unavailable", request=request)
        return httpx.Response(200, json={"status": "ok", "mock": True}, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "get", health)
    monkeypatch.setattr(system_status.settings, "mcp_client_url", "http://internal.example:8010")
    monkeypatch.setattr(system_status.settings, "mcp_public_host", "public.example")
    response = client.get("/api/v1/admin/live-status/system", headers=_auth_header("admin", "change-me"))
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"checked_at", "services", "postgres", "redis", "failures"}
    assert len(body["services"]) == 5
    assert [s["status"] for s in body["services"]] == ["ok", "down", "ok", "ok", "ok"]
    assert all(s["latency_ms"] >= 0 and s["role"] for s in body["services"])
    assert {url.host for url in urls} == {"internal.example"}
    assert all(url.path == "/health" for url in urls)
    assert body["postgres"]["ok"] is True
    assert all(isinstance(d["size_mb"], (int, float)) for d in body["postgres"]["databases"])
    tables = body["postgres"]["tables"]
    assert {t["database"] for t in tables} == {d["name"] for d in body["postgres"]["databases"]}
    assert all(isinstance(t["rows"], int) for t in tables)
    assert body["redis"]["ok"] is True
    assert all({"name", "type", "ttl_seconds"} <= set(k) for k in body["redis"]["keys"])


def test_system_survives_postgres_and_redis_failure(client, monkeypatch):
    from app.routers.admin import system_status

    async def postgres_failure():
        raise RuntimeError("postgres unavailable")

    def redis_failure(*args, **kwargs):
        raise RuntimeError("redis unavailable")

    monkeypatch.setattr(system_status.system_repository, "snapshot", postgres_failure)
    monkeypatch.setattr(system_status.redis, "from_url", redis_failure)
    response = client.get("/api/v1/admin/live-status/system", headers=_auth_header("admin", "change-me"))
    assert response.status_code == 200
    body = response.json()
    for name in ("postgres", "redis"):
        assert body[name]["ok"] is False
        assert body[name]["error"] == f"{name} unavailable"
    assert body["failures"] == {"recent": [], "by_service_7d": []}
    assert len(body["services"]) == 5
    assert all(service["status"] in {"ok", "down"} for service in body["services"])
