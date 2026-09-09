from app.services.mock import build_mock_reaction


def test_mock_response_echoes_requested_stock_code():
    result = build_mock_reaction("현대차", "005380")

    assert result["mock"] is True
    assert result["company_name"] == "현대차"
    assert result["stock_code"] == "005380"
    assert result["source_name"] == "커뮤니티 FGI 서버(네이버 종목토론실)"
    assert result["activity"] == {
        "posts_7d": 100,
        "weekly_avg_prev_28d": 70.0,
        "ratio": 1.43,
        "baseline_days": 28,
    }
