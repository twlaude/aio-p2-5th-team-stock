from fastapi.testclient import TestClient

from app.main import app


def test_health_does_not_expose_secrets():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["service"] == "mcp_client"
    assert "openai_api_key" not in response.json()


def test_rejects_invalid_stock_code_before_workflow():
    response = TestClient(app).post(
        "/internal/v1/common-analyses",
        json={
            "request_id": "request",
            "company": {"company_name": "삼성전자", "stock_code": "5930"},
            "investment_profile": None,
            "requested_at": "2026-09-04T00:00:00Z",
        },
    )

    assert response.status_code == 422
