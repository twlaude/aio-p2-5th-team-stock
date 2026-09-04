from pydantic import BaseModel


class ErrorDetail(BaseModel):
    service: str
    code: str
    message: str
    retryable: bool


class ErrorResponse(BaseModel):
    request_id: str
    status: str
    error: ErrorDetail


# shared/contracts/errors/README.md의 HTTP 상태 표. 정의 안 된 상태는 500(내부 오류)으로 취급한다.
STATUS_HTTP_CODE: dict[str, int] = {
    "timeout": 504,
    "external_api_error": 500,
    "internal_error": 500,
}
