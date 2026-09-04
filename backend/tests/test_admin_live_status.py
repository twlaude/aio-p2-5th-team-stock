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
