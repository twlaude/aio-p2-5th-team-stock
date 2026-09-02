import httpx

from app.clients.fgi_api import CommunityFGIClient
from app.core.config import CommunityConfig
from app.services.reaction import fetch_community_reaction


def _config() -> CommunityConfig:
    return CommunityConfig(api_token="token", mock_mode="0")


def _request(stock_code: str = "005930"):
    return {
        "company_name": "삼성전자",
        "stock_code": stock_code,
        "lookback_days": 7,
        "limit": 100,
    }


def _client(handler) -> CommunityFGIClient:
    return CommunityFGIClient("http://upstream.test", "token", 10, httpx.MockTransport(handler))


def test_success_sufficient_mapping_preserves_contract_fields():
    upstream = {
        "status": "success",
        "sample_status": "sufficient",
        "stock_code": "005930",
        "period": {"from": "2026-08-26T09:00:00Z", "to": "2026-09-02T09:00:00Z"},
        "sample_size": 100,
        "sentiment": {"positive_count": 18, "neutral_count": 27, "negative_count": 55},
        "top_topics": {"expectations": ["수급 기대"], "concerns": ["하락 우려"]},
        "representative_evidence": [{"text": "요지", "sentiment": "negative", "posted_at": "2026-09-02T06:12:00Z"}],
        "source_name": "태웅 종토방 FGI 서버 (네이버 종목토론실)",
        "collected_at": "2026-09-02T09:06:59Z",
        "fgi_mean": 41.02,
        "note": "원문은 포함하지 않는다.",
    }
    result = fetch_community_reaction(_request(), _config(), _client(lambda request: httpx.Response(200, json=upstream)))

    assert result["status"] == "success"
    assert result["sample_status"] == "sufficient"
    assert result["source_name"] == "태웅님 커뮤니티 서버"
    assert result["source_detail"] == upstream["source_name"]
    assert result["fgi_mean"] == 41.02
    assert result["note"] == upstream["note"]


def test_success_insufficient_sample_mapping():
    upstream = {
        "status": "success",
        "sample_status": "insufficient_sample",
        "stock_code": "005930",
        "sample_size": 5,
        "sentiment": {"positive_count": 1, "neutral_count": 2, "negative_count": 2},
        "top_topics": {"expectations": [], "concerns": []},
        "representative_evidence": [],
        "collected_at": "2026-09-02T09:06:59Z",
    }
    result = fetch_community_reaction(_request(), _config(), _client(lambda request: httpx.Response(200, json=upstream)))

    assert result["status"] == "success"
    assert result["sample_status"] == "insufficient_sample"
    assert result["sample_size"] == 5


def test_no_data_and_unsupported_company_are_passthrough_statuses():
    no_data = {"status": "no_data", "sample_status": "no_data", "stock_code": "005930", "sample_size": 0}
    unsupported = {"status": "unsupported_company", "sample_status": "no_data", "stock_code": "000000", "supported_codes": ["005930"]}

    no_data_result = fetch_community_reaction(_request(), _config(), _client(lambda request: httpx.Response(200, json=no_data)))
    unsupported_result = fetch_community_reaction(_request("000000"), _config(), _client(lambda request: httpx.Response(200, json=unsupported)))

    assert no_data_result["status"] == "no_data"
    assert no_data_result["sample_status"] == "no_data"
    assert unsupported_result["status"] == "unsupported_company"
    assert unsupported_result["supported_codes"] == ["005930"]


def test_upstream_failures_map_to_contract_errors():
    unavailable = fetch_community_reaction(_request(), _config(), _client(lambda request: httpx.Response(503)))
    timeout = fetch_community_reaction(_request(), _config(), _client(lambda request: (_ for _ in ()).throw(httpx.ReadTimeout("timeout"))))
    unauthorized = fetch_community_reaction(_request(), _config(), _client(lambda request: httpx.Response(401)))

    assert unavailable["status"] == "external_api_error"
    assert unavailable["error"]["retryable"] is True
    assert timeout["status"] == "timeout"
    assert timeout["error"]["retryable"] is True
    assert unauthorized["status"] == "unauthorized"
    assert unauthorized["error"]["retryable"] is False
