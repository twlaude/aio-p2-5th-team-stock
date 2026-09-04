import app.tools.news as news_tool
from app.tools.news import search_news


def test_tool_validation_returns_invalid_request_without_raising():
    bad_code = search_news("삼성전자", "5930")
    bad_lookback = search_news("삼성전자", "005930", lookback_days=31)
    bad_limit = search_news("삼성전자", "005930", limit=101)

    assert bad_code["status"] == "invalid_request"
    assert bad_lookback["status"] == "invalid_request"
    assert bad_limit["status"] == "invalid_request"
    assert bad_code["error"]["service"] == "news_mcp"


def test_tool_allows_limit_100(monkeypatch):
    captured_request = None

    def fake_fetch_news(request):
        nonlocal captured_request
        captured_request = request
        return {"status": "success"}

    monkeypatch.setattr(news_tool, "fetch_news", fake_fetch_news)

    result = search_news("삼성전자", "005930", limit=100)

    assert result["status"] == "success"
    assert captured_request is not None
    assert captured_request["limit"] == 100
