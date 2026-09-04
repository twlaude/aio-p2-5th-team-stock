from datetime import datetime, timezone

from app.core.config import PriceConfig
from app.clients.kis_price import KISAPIUnavailable
from app.services.price import clear_quote_cache, fetch_stock_quote


class FakeClient:
    def __init__(self):
        self.calls = 0

    def get_quote(self, stock_code):
        self.calls += 1
        return {
            "stck_prpr": "70000",
            "prdy_vrss": "500",
            "prdy_ctrt": "0.72",
            "prdy_vrss_sign": "2",
            "acml_vol": "2000",
            "prdy_vrss_vol_rate": "200.00",
        }

    def get_daily_prices(self, stock_code):
        self.calls += 1
        return [{"stck_bsop_date": "20260903", "acml_vol": "1000"}]


def test_reuses_quote_inside_cache_ttl():
    clear_quote_cache()
    client = FakeClient()
    config = PriceConfig(cache_ttl_seconds=60)
    request = {"company_name": "삼성전자", "stock_code": "005930"}
    now = lambda: datetime(2026, 9, 4, 5, 30, tzinfo=timezone.utc)

    first = fetch_stock_quote(
        request,
        config=config,
        client=client,
        now_provider=now,
        cache_clock=lambda: 100.0,
    )
    second = fetch_stock_quote(
        request,
        config=config,
        client=client,
        now_provider=now,
        cache_clock=lambda: 120.0,
    )

    assert first == second
    assert client.calls == 2


class DailyFailureClient(FakeClient):
    def get_daily_prices(self, stock_code):
        self.calls += 1
        raise KISAPIUnavailable()


def test_daily_price_failure_keeps_current_quote_successful_and_cached():
    clear_quote_cache()
    client = DailyFailureClient()
    config = PriceConfig(cache_ttl_seconds=60)
    request = {"company_name": "삼성전자", "stock_code": "005930"}
    now = lambda: datetime(2026, 9, 4, 5, 30, tzinfo=timezone.utc)

    first = fetch_stock_quote(
        request,
        config=config,
        client=client,
        now_provider=now,
        cache_clock=lambda: 100.0,
    )
    second = fetch_stock_quote(
        request,
        config=config,
        client=client,
        now_provider=now,
        cache_clock=lambda: 120.0,
    )

    assert first["status"] == "success"
    assert first["volume"] == 2000
    assert first["avg_volume_20d"] is None
    assert first["volume_ratio_20d"] is None
    assert first["volume_basis"] is None
    assert first["volume_as_of"] is None
    assert first["projected_volume"] is None
    assert first["warnings"] == ["VOLUME_BASELINE_UNAVAILABLE"]
    assert second == first
    assert client.calls == 2
