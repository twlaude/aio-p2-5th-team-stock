from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default, cast):
    value = os.getenv(name)
    return cast(value) if value else default


@dataclass(frozen=True)
class NewsConfig:
    api_url: str = "https://naverapihub.apigw.ntruss.com/search/v1/news"
    client_id: str | None = None
    client_secret: str | None = None
    host: str = "0.0.0.0"
    port: int = 8021
    lookback_days: int = 7
    result_limit: int = 10
    timeout_sec: float = 10.0
    mock_mode: str = "auto"

    @property
    def mock_enabled(self) -> bool:
        mode = self.mock_mode.strip().lower()
        if mode in {"1", "true", "yes", "on"}:
            return True
        if mode in {"0", "false", "no", "off"}:
            return False
        return not bool(self.client_id and self.client_secret)


def get_config() -> NewsConfig:
    return NewsConfig(
        api_url=os.getenv("NAVER_NEWS_API_URL", NewsConfig.api_url),
        client_id=os.getenv("NAVER_NEWS_CLIENT_ID") or None,
        client_secret=os.getenv("NAVER_NEWS_CLIENT_SECRET") or None,
        host=os.getenv("NEWS_MCP_HOST", NewsConfig.host),
        port=_env("NEWS_MCP_PORT", NewsConfig.port, int),
        lookback_days=_env("NEWS_LOOKBACK_DAYS", NewsConfig.lookback_days, int),
        result_limit=_env("NEWS_RESULT_LIMIT", NewsConfig.result_limit, int),
        timeout_sec=_env("NEWS_TIMEOUT_SEC", NewsConfig.timeout_sec, float),
        mock_mode=os.getenv("NEWS_MOCK", NewsConfig.mock_mode),
    )
