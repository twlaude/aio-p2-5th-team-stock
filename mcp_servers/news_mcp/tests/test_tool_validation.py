from app.tools.news import search_news


def test_tool_validation_returns_invalid_request_without_raising():
    bad_code = search_news("삼성전자", "5930")
    bad_lookback = search_news("삼성전자", "005930", lookback_days=31)
    bad_limit = search_news("삼성전자", "005930", limit=11)

    assert bad_code["status"] == "invalid_request"
    assert bad_lookback["status"] == "invalid_request"
    assert bad_limit["status"] == "invalid_request"
    assert bad_code["error"]["service"] == "news_mcp"
