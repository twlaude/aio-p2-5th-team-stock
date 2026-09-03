from app.services.mock import build_mock_news


def test_mock_response_echoes_requested_stock_code():
    result = build_mock_news("현대차", "005380")

    assert result["mock"] is True
    assert result["company_name"] == "현대차"
    assert result["stock_code"] == "005380"
    assert result["result_count"] == len(result["articles"])
