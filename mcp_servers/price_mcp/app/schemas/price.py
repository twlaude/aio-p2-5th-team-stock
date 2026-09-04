from typing import Literal, TypedDict

Status = Literal[
    "success",
    "no_data",
    "invalid_request",
    "unauthorized",
    "external_api_error",
    "timeout",
    "internal_error",
]


class PriceRequest(TypedDict):
    company_name: str
    stock_code: str


class ErrorDetail(TypedDict):
    service: str
    code: str
    message: str
    retryable: bool


class PriceResponse(TypedDict, total=False):
    status: Status
    company_name: str
    stock_code: str
    current_price: int
    change: int
    change_rate: float
    as_of: str
    source_name: str
    collected_at: str
    error: ErrorDetail
