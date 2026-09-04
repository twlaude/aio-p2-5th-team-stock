from datetime import datetime, timezone

from app.services.price import map_kis_quote

REQUEST = {"company_name": "삼성전자", "stock_code": "005930"}
NOW = datetime(2026, 9, 4, 5, 30, tzinfo=timezone.utc)


def daily_history(include_today=True, last_session_volume="1000"):
    return [
        *([{"stck_bsop_date": "20260904", "acml_vol": "999999"}] if include_today else []),
        {"stck_bsop_date": "20260903", "acml_vol": last_session_volume},
        *[
            {"stck_bsop_date": f"202608{day:02d}", "acml_vol": "1000"}
            for day in range(31, 11, -1)
        ],
    ]


def test_maps_rising_quote():
    result = map_kis_quote(
        {
            "stck_prpr": "70000",
            "prdy_vrss": "500",
            "prdy_ctrt": "0.72",
            "prdy_vrss_sign": "2",
            "acml_vol": "2500",
            "prdy_vrss_vol_rate": "125.50",
        },
        REQUEST,
        now=NOW,
    )

    assert result["current_price"] == 70000
    assert result["change"] == 500
    assert result["change_rate"] == 0.72
    assert result["volume"] == 2500
    assert result["volume_change_rate"] == 125.5
    assert result["avg_volume_20d"] is None
    assert result["volume_ratio_20d"] is None
    assert result["volume_basis"] is None
    assert result["volume_as_of"] is None
    assert result["projected_volume"] is None
    assert result["as_of"] == "2026-09-04T05:30:00Z"


def test_maps_falling_quote_with_negative_sign():
    result = map_kis_quote(
        {
            "stck_prpr": "69000",
            "prdy_vrss": "1000",
            "prdy_ctrt": "1.43",
            "prdy_vrss_sign": "5",
            "acml_vol": "1900",
        },
        REQUEST,
        now=NOW,
    )

    assert result["change"] == -1000
    assert result["change_rate"] == -1.43
    assert result["volume_change_rate"] is None


def test_uses_intraday_pace_during_business_day_session():
    result = map_kis_quote(
        {
            "stck_prpr": "70000",
            "prdy_vrss": "0",
            "prdy_ctrt": "0.00",
            "prdy_vrss_sign": "3",
            "acml_vol": "2500",
            "prdy_vrss_vol_rate": "250.00",
        },
        REQUEST,
        now=datetime(2026, 9, 4, 3, 15, tzinfo=timezone.utc),
        daily_prices=daily_history(),
    )

    assert result["avg_volume_20d"] == 1000
    assert result["volume_ratio_20d"] == 5.0
    assert result["volume_basis"] == "intraday_pace"
    assert result["volume_as_of"] == "2026-09-04"
    assert result["projected_volume"] == 5000
    assert result["warnings"] == []


def test_uses_today_close_at_and_after_market_close():
    result = map_kis_quote(
        {"stck_prpr": "70000", "acml_vol": "2500"},
        REQUEST,
        now=datetime(2026, 9, 4, 6, 30, tzinfo=timezone.utc),
        daily_prices=daily_history(),
    )

    assert result["avg_volume_20d"] == 1000
    assert result["volume_ratio_20d"] == 2.5
    assert result["volume_basis"] == "today_close"
    assert result["volume_as_of"] == "2026-09-04"
    assert result["projected_volume"] is None


def test_uses_last_session_before_market_open():
    result = map_kis_quote(
        {"stck_prpr": "70000", "acml_vol": "777"},
        REQUEST,
        now=datetime(2026, 9, 3, 23, 59, tzinfo=timezone.utc),
        daily_prices=daily_history(last_session_volume="2500"),
    )

    assert result["volume"] == 777
    assert result["avg_volume_20d"] == 1000
    assert result["volume_ratio_20d"] == 2.5
    assert result["volume_basis"] == "last_session"
    assert result["volume_as_of"] == "2026-09-03"


def test_intraday_pace_clamps_elapsed_fraction_at_ten_percent():
    result = map_kis_quote(
        {"stck_prpr": "70000", "acml_vol": "1000"},
        REQUEST,
        now=datetime(2026, 9, 4, 0, 1, tzinfo=timezone.utc),
        daily_prices=daily_history(),
    )

    assert result["projected_volume"] == 10000
    assert result["volume_ratio_20d"] == 10.0


def test_uses_last_session_when_today_row_is_absent():
    result = map_kis_quote(
        {"stck_prpr": "70000", "acml_vol": "777"},
        REQUEST,
        now=NOW,
        daily_prices=daily_history(include_today=False, last_session_volume="2500"),
    )

    assert result["volume"] == 777
    assert result["avg_volume_20d"] == 1000
    assert result["volume_ratio_20d"] == 2.5
    assert result["volume_basis"] == "last_session"
    assert result["volume_as_of"] == "2026-09-03"
