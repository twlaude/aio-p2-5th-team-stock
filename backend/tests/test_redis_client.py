from uuid import uuid4

from app.clients.redis import client as redis_client


def test_set_get_clear_roundtrip():
    user_id = f"test-user-{uuid4().hex[:8]}"

    assert redis_client.get_state(user_id) == {}

    redis_client.set_state(user_id, recent_company_name="삼성전자", recent_stock_code="005930")
    state = redis_client.get_state(user_id)
    assert state["recent_company_name"] == "삼성전자"
    assert state["recent_stock_code"] == "005930"

    redis_client.set_state(user_id, searched_at="2026-09-03T00:00:00Z")
    merged = redis_client.get_state(user_id)
    assert merged["recent_company_name"] == "삼성전자"
    assert merged["searched_at"] == "2026-09-03T00:00:00Z"

    redis_client.clear_state(user_id)
    assert redis_client.get_state(user_id) == {}
