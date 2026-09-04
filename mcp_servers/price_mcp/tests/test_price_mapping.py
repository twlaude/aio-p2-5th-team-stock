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
        },
        REQUEST,
        now=NOW,
    )

    assert result["current_price"] == 70000
    assert result["change"] == 500
    assert result["change_rate"] == 0.72
    assert result["as_of"] == "2026-09-04T05:30:00Z"


def test_maps_falling_quote_with_negative_sign():
    result = map_kis_quote(
        {
            "stck_prpr": "69000",
            "prdy_vrss": "1000",
            "prdy_ctrt": "1.43",
            "prdy_vrss_sign": "5",
        },
        REQUEST,
        now=NOW,
    )

    assert result["change"] == -1000
    assert result["change_rate"] == -1.43
