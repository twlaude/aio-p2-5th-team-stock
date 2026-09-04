from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from time import monotonic
from typing import Any

from app.clients.kis_price import (
    KISAPINoData,
    KISAPITimeout,
    KISAPIUnauthorized,
    KISAPIUnavailable,
    KISConfigurationError,
    KISPriceClient,
)
from app.core.config import PriceConfig, get_config
from app.schemas.price import ErrorDetail, PriceRequest, PriceResponse

SERVICE_NAME = "price_mcp"
SOURCE_NAME = "한국투자증권 Open API"

_QUOTE_CACHE: dict[str, tuple[float, PriceResponse]] = {}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_utc(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _number(value: Any) -> Decimal:
    try:
        return Decimal(str(value).strip())
    except (InvalidOperation, ValueError, AttributeError) as exc:
        raise KISAPIUnavailable() from exc


def _signed(value: Any, sign_code: str | None) -> Decimal:
    number = _number(value)
    if sign_code in {"1", "2"}:
        return abs(number)
    if sign_code == "3":
        return Decimal("0")
    if sign_code in {"4", "5"}:
        return -abs(number)
    return number


def map_kis_quote(
    output: dict[str, Any],
    request: PriceRequest,
    now: datetime | None = None,
) -> PriceResponse:
    collected_at = _iso_utc(now or _utc_now())
    sign_code = str(output.get("prdy_vrss_sign", ""))
    return {
        "status": "success",
        "company_name": request["company_name"],
        "stock_code": request["stock_code"],
        "current_price": int(_number(output.get("stck_prpr"))),
        "change": int(_signed(output.get("prdy_vrss", 0), sign_code)),
        "change_rate": float(_signed(output.get("prdy_ctrt", 0), sign_code)),
        "as_of": collected_at,
        "source_name": SOURCE_NAME,
        "collected_at": collected_at,
    }


def error_response(status: str, code: str, message: str, retryable: bool) -> PriceResponse:
    error: ErrorDetail = {
        "service": SERVICE_NAME,
        "code": code,
        "message": message,
        "retryable": retryable,
    }
    return {"status": status, "error": error}


def clear_quote_cache() -> None:
    _QUOTE_CACHE.clear()


def fetch_stock_quote(
    request: PriceRequest,
    config: PriceConfig | None = None,
    client: KISPriceClient | None = None,
    now_provider: Callable[[], datetime] | None = None,
    cache_clock: Callable[[], float] = monotonic,
) -> PriceResponse:
    active_config = config or get_config()
    now = now_provider or _utc_now
    cached = _QUOTE_CACHE.get(request["stock_code"])
    current_tick = cache_clock()
    if cached and cached[0] > current_tick:
        return dict(cached[1])

    owns_client = client is None
    active_client = client or KISPriceClient(active_config)
    try:
        output = active_client.get_quote(request["stock_code"])
        result = map_kis_quote(output, request, now=now())
        _QUOTE_CACHE[request["stock_code"]] = (
            current_tick + active_config.cache_ttl_seconds,
            result,
        )
        return result
    except KISConfigurationError:
        return error_response(
            "unauthorized",
            "KIS_CREDENTIALS_MISSING",
            "한국투자증권 API 인증정보가 설정되지 않았습니다.",
            False,
        )
    except KISAPITimeout:
        return error_response(
            "timeout",
            "KIS_API_TIMEOUT",
            "현재 가격 조회가 시간 초과되었습니다.",
            True,
        )
    except KISAPIUnauthorized:
        return error_response(
            "unauthorized",
            "KIS_API_UNAUTHORIZED",
            "한국투자증권 API 인증에 실패했습니다.",
            False,
        )
    except KISAPINoData:
        return {
            "status": "no_data",
            "company_name": request["company_name"],
            "stock_code": request["stock_code"],
            "source_name": SOURCE_NAME,
            "collected_at": _iso_utc(now()),
        }
    except KISAPIUnavailable:
        return error_response(
            "external_api_error",
            "KIS_API_UNAVAILABLE",
            "현재 가격 정보를 일시적으로 가져오지 못했습니다.",
            True,
        )
    finally:
        if owns_client:
            active_client.close()
