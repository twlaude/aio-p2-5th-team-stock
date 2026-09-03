from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def member_token(client: TestClient) -> str:
    response = client.post("/api/v1/auth/login", json={"username": "demo001", "password": "Demo1234!"})
    return response.json()["access_token"]


def pytest_sessionstart(session):
    print("[TEST] backend tests start")


def pytest_sessionfinish(session, exitstatus):
    print(f"[TEST] backend tests exitstatus={exitstatus}")
