from datetime import datetime, timezone
import json

import httpx

from app.clients.kis_price import KISPriceClient
from app.core.config import PriceConfig


def test_issues_token_once_and_fetches_quote(tmp_path):
    calls = {"token": 0, "quote": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/tokenP":
            calls["token"] += 1
            return httpx.Response(
                200,
                json={"access_token": "test-token", "expires_in": 86400},
            )
        calls["quote"] += 1
        assert request.headers["authorization"] == "Bearer test-token"
        assert request.headers["tr_id"] == "FHKST01010100"
        assert request.url.params["FID_INPUT_ISCD"] == "005930"
        return httpx.Response(
            200,
            json={
                "rt_cd": "0",
                "output": {
                    "stck_prpr": "70000",
                    "prdy_vrss": "500",
                    "prdy_ctrt": "0.72",
                    "prdy_vrss_sign": "2",
                },
            },
        )

    config = PriceConfig(
        app_key="test-key",
        app_secret="test-secret",
        token_cache_file=tmp_path / "token.json",
    )
    client = KISPriceClient(
        config,
        transport=httpx.MockTransport(handler),
        now_provider=lambda: datetime(2026, 9, 4, tzinfo=timezone.utc),
    )
    try:
        first = client.get_quote("005930")
        second = client.get_quote("005930")
    finally:
        client.close()

    assert first["stck_prpr"] == "70000"
    assert second["stck_prpr"] == "70000"
    assert calls == {"token": 1, "quote": 2}


def test_does_not_reuse_token_cached_for_another_app_key(tmp_path):
    token_cache = tmp_path / "token.json"
    token_cache.write_text(
        json.dumps(
            {
                "access_token": "another-key-token",
                "expires_at": "2099-01-01T00:00:00+00:00",
                "app_key_fingerprint": "not-the-current-key",
            }
        ),
        encoding="utf-8",
    )
    calls = {"token": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/tokenP":
            calls["token"] += 1
            return httpx.Response(
                200,
                json={"access_token": "current-key-token", "expires_in": 86400},
            )
        assert request.headers["authorization"] == "Bearer current-key-token"
        return httpx.Response(
            200,
            json={
                "rt_cd": "0",
                "output": {
                    "stck_prpr": "70000",
                    "prdy_vrss": "0",
                    "prdy_ctrt": "0.00",
                    "prdy_vrss_sign": "3",
                },
            },
        )

    config = PriceConfig(
        app_key="current-key",
        app_secret="test-secret",
        token_cache_file=token_cache,
    )
    client = KISPriceClient(
        config,
        transport=httpx.MockTransport(handler),
        now_provider=lambda: datetime(2026, 9, 4, tzinfo=timezone.utc),
    )
    try:
        client.get_quote("005930")
    finally:
        client.close()

    assert calls["token"] == 1


def test_fetches_quote_and_daily_prices_with_required_daily_parameters(tmp_path):
    calls = {"token": 0, "quote": 0, "daily": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/oauth2/tokenP":
            calls["token"] += 1
            return httpx.Response(
                200,
                json={"access_token": "test-token", "expires_in": 86400},
            )
        if request.url.path.endswith("/inquire-price"):
            calls["quote"] += 1
            assert request.headers["tr_id"] == "FHKST01010100"
            return httpx.Response(
                200,
                json={"rt_cd": "0", "output": {"stck_prpr": "70000"}},
            )

        calls["daily"] += 1
        assert request.url.path.endswith("/inquire-daily-itemchartprice")
        assert request.headers["tr_id"] == "FHKST03010100"
        assert dict(request.url.params) == {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": "005930",
            "FID_INPUT_DATE_1": "20260721",
            "FID_INPUT_DATE_2": "20260904",
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0",
        }
        return httpx.Response(
            200,
            json={
                "rt_cd": "0",
                "output2": [{"stck_bsop_date": "20260903", "acml_vol": "1000"}],
            },
        )

    client = KISPriceClient(
        PriceConfig(
            app_key="test-key",
            app_secret="test-secret",
            token_cache_file=tmp_path / "token.json",
        ),
        transport=httpx.MockTransport(handler),
        now_provider=lambda: datetime(2026, 9, 4, tzinfo=timezone.utc),
    )
    try:
        quote = client.get_quote("005930")
        daily_prices = client.get_daily_prices("005930")
    finally:
        client.close()

    assert quote["stck_prpr"] == "70000"
    assert daily_prices == [{"stck_bsop_date": "20260903", "acml_vol": "1000"}]
    assert calls == {"token": 1, "quote": 1, "daily": 1}
