from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PRICE_MCP_ROOT = Path(__file__).resolve().parents[2]


def _env(name: str, default, cast):
    value = os.getenv(name)
    return cast(value) if value else default


@dataclass(frozen=True)
class PriceConfig:
    app_key: str | None = None
    app_secret: str | None = None
    base_url: str = "https://openapi.koreainvestment.com:9443"
    token_url: str = "/oauth2/tokenP"
    price_url: str = "/uapi/domestic-stock/v1/quotations/inquire-price"
    tr_id: str = "FHKST01010100"
    daily_url: str = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    daily_tr_id: str = "FHKST03010100"
    market_code: str = "J"
    token_cache_file: Path = PRICE_MCP_ROOT / ".cache" / "kis_token.json"
    host: str = "0.0.0.0"
    port: int = 8020
    cache_ttl_seconds: int = 60
    timeout_seconds: float = 10.0

    @property
    def credentials_configured(self) -> bool:
        return bool(self.app_key and self.app_secret)


def get_config() -> PriceConfig:
    cache_path = Path(os.getenv("KIS_TOKEN_CACHE_FILE", ".cache/kis_token.json"))
    if not cache_path.is_absolute():
        cache_path = PRICE_MCP_ROOT / cache_path

    return PriceConfig(
        app_key=os.getenv("KIS_APP_KEY") or None,
        app_secret=os.getenv("KIS_APP_SECRET") or None,
        base_url=os.getenv("KIS_BASE_URL", PriceConfig.base_url).rstrip("/"),
        token_url=os.getenv("KIS_TOKEN_URL", PriceConfig.token_url),
        price_url=os.getenv("KIS_PRICE_URL", PriceConfig.price_url),
        tr_id=os.getenv("KIS_TR_ID", PriceConfig.tr_id),
        daily_url=os.getenv("KIS_DAILY_URL", PriceConfig.daily_url),
        daily_tr_id=os.getenv("KIS_DAILY_TR_ID", PriceConfig.daily_tr_id),
        market_code=os.getenv("KIS_MARKET_CODE", PriceConfig.market_code),
        token_cache_file=cache_path,
        host=os.getenv("PRICE_MCP_HOST", PriceConfig.host),
        port=_env("PRICE_MCP_PORT", PriceConfig.port, int),
        cache_ttl_seconds=_env("PRICE_CACHE_TTL_SECONDS", PriceConfig.cache_ttl_seconds, int),
        timeout_seconds=_env("PRICE_API_TIMEOUT_SECONDS", PriceConfig.timeout_seconds, float),
    )
