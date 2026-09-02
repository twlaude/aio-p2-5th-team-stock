from app.tools.community import get_community_reaction


def test_tool_validation_returns_invalid_request_without_raising():
    bad_code = get_community_reaction("삼성전자", "5930")
    bad_lookback = get_community_reaction("삼성전자", "005930", lookback_days=29)
    bad_limit = get_community_reaction("삼성전자", "005930", limit=501)

    assert bad_code["status"] == "invalid_request"
    assert bad_lookback["status"] == "invalid_request"
    assert bad_limit["status"] == "invalid_request"
    assert bad_code["error"]["service"] == "community_mcp"
