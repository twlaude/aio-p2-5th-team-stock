from app.tools.price import get_stock_quote


def test_rejects_empty_company_name():
    result = get_stock_quote(" ", "005930")

    assert result["status"] == "invalid_request"
    assert result["error"]["code"] == "INVALID_COMPANY_NAME"


def test_rejects_invalid_stock_code():
    result = get_stock_quote("삼성전자", "5930")

    assert result["status"] == "invalid_request"
    assert result["error"]["service"] == "price_mcp"
