from typing import Any

from app.schemas.price import PriceRequest
from app.services.price import error_response, fetch_stock_quote


def get_stock_quote(company_name: str, stock_code: str) -> dict[str, Any]:
    """Return the current KRX price for one six-digit Korean stock code."""
    normalized_name = company_name.strip()
    normalized_code = stock_code.strip()
    if not normalized_name:
        return error_response(
            "invalid_request",
            "INVALID_COMPANY_NAME",
            "company_name은 비어 있을 수 없습니다.",
            False,
        )
    if not normalized_code.isdigit() or len(normalized_code) != 6:
        return error_response(
            "invalid_request",
            "INVALID_STOCK_CODE",
            "stock_code는 6자리 숫자여야 합니다.",
            False,
        )

    request: PriceRequest = {
        "company_name": normalized_name,
        "stock_code": normalized_code,
    }
    return fetch_stock_quote(request)


def register_price_tools(mcp: Any) -> None:
    mcp.tool()(get_stock_quote)
