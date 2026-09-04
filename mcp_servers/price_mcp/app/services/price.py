from collections.abc import Callable
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from time import monotonic
from typing import Any
from zoneinfo import ZoneInfo

from app.clients.kis_price import (
    KISAPIError,
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


def _optional_float(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    return float(_number(value))


def _volume_baseline(
    daily_prices: list[dict[str, Any]],
    current_volume: int,
    today: date,
) -> tuple[int | None, float | None]:
    today_text = today.strftime("%Y%m%d")
    dated_volumes: list[tuple[str, int]] = []
    for row in daily_prices:
        business_date = str(row.get("stck_bsop_date", "")).strip()
        if len(business_date) != 8 or not business_date.isdigit():
            continue
        if business_date >= today_text:
            continue
        try:
            volume = int(_number(row.get("acml_vol")))
        except KISAPIUnavailable:
            continue
        if volume < 0:
            continue
        dated_volumes.append((business_date, volume))

    recent_volumes = [
        volume
        for _, volume in sorted(dated_volumes, key=lambda item: item[0], reverse=True)[:20]
    ]
    if not recent_volumes:
        return None, None

    average = sum(recent_volumes) // len(recent_volumes)
    ratio = round(current_volume / average, 2) if average > 0 else None
    return average, ratio


def map_kis_quote(
    output: dict[str, Any],
    request: PriceRequest,
    now: datetime | None = None,
    daily_prices: list[dict[str, Any]] | None = None,
) -> PriceResponse:
    current_time = now or _utc_now()
    collected_at = _iso_utc(current_time)
    sign_code = str(output.get("prdy_vrss_sign", ""))
    current_volume = int(_number(output.get("acml_vol")))
    average_volume, volume_ratio = _volume_baseline(
        daily_prices or [],
        current_volume,
        current_time.astimezone(ZoneInfo("Asia/Seoul")).date(),
    )
    return {
        "status": "success",
        "company_name": request["company_name"],
        "stock_code": request["stock_code"],
        "current_price": int(_number(output.get("stck_prpr"))),
        "change": int(_signed(output.get("prdy_vrss", 0), sign_code)),
        "change_rate": float(_signed(output.get("prdy_ctrt", 0), sign_code)),
        "volume": current_volume,
        "volume_change_rate": _optional_float(output.get("prdy_vrss_vol_rate")),
        "avg_volume_20d": average_volume,
        "volume_ratio_20d": volume_ratio,
        "warnings": [],
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
        current_time = now()
        try:
            daily_prices = active_client.get_daily_prices(request["stock_code"])
            result = map_kis_quote(
                output,
                request,
                now=current_time,
                daily_prices=daily_prices,
            )
        except KISAPIError:
            result = map_kis_quote(output, request, now=current_time)
            result["warnings"] = ["VOLUME_BASELINE_UNAVAILABLE"]
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
