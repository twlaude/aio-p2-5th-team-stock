from datetime import datetime, timezone

from app.services.price import map_kis_quote

REQUEST = {"company_name": "삼성전자", "stock_code": "005930"}
NOW = datetime(2026, 9, 4, 5, 30, tzinfo=timezone.utc)


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


def test_maps_recent_20_day_volume_baseline_excluding_today():
    daily_prices = [
        {"stck_bsop_date": "20260904", "acml_vol": "999999"},
        *[
            {
                "stck_bsop_date": f"202608{day:02d}",
                "acml_vol": "1000" if day >= 12 else "999999",
            }
            for day in range(31, 9, -1)
        ],
    ]

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
        now=NOW,
        daily_prices=daily_prices,
    )

    assert result["avg_volume_20d"] == 1000
    assert result["volume_ratio_20d"] == 2.5
    assert result["warnings"] == []
