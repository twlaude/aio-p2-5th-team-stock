import httpx

from app.clients.fgi_api import CommunityFGIClient
from app.core.config import CommunityConfig
from app.services.reaction import fetch_fear_greed_index

CONFIG = CommunityConfig(api_token="token", mock_mode="0")
REQUEST = {"company_name": "삼성전자", "stock_code": "005930"}


def _client(handler):
    return CommunityFGIClient("http://upstream.test", "token", 10, httpx.MockTransport(handler))


def test_fgi_success_maps_latest_index():
    upstream = {"stock_code": "005930", "fgi": 64.2, "label": "탐욕", "post_count": 82, "summary": "매수 기대가 우세하다.", "as_of": "2026-09-02T09:15:00Z", "warnings": ["표본 부족 가능성"], "source_name": "태웅 종토방 FGI 서버"}
    result = fetch_fear_greed_index(REQUEST, CONFIG, _client(lambda request: httpx.Response(200, json=upstream)))

    assert result["status"] == "success"
    assert result["fgi"] == 64.2
    assert result["label"] == "탐욕"
    assert result["warnings"] == ["표본 부족 가능성"]
    assert result["source_detail"] == upstream["source_name"]


def test_fgi_unsupported_company_passthrough():
    upstream = {"status": "empty", "stock_code": "035420", "reason": "지원 20종목만 산출"}
    result = fetch_fear_greed_index({**REQUEST, "stock_code": "035420"}, CONFIG, _client(lambda request: httpx.Response(200, json=upstream)))

    assert result["status"] == "unsupported_company"
    assert result["stock_code"] == "035420"
    assert result["fgi"] is None


def test_fgi_upstream_unavailable_maps_to_error():
    result = fetch_fear_greed_index(REQUEST, CONFIG, _client(lambda request: httpx.Response(503)))
    assert result["status"] == "error"
    assert result["error"]["code"] == "COMMUNITY_API_UNAVAILABLE"
    assert result["error"]["retryable"] is True
