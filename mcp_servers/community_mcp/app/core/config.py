from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default, cast):
    value = os.getenv(name)
    return cast(value) if value else default


@dataclass(frozen=True)
class CommunityConfig:
    api_url: str = "http://159.223.75.71:8877"
    api_token: str | None = None
    host: str = "0.0.0.0"
    port: int = 8023
    lookback_days: int = 7
    result_limit: int = 100
    timeout_sec: float = 10.0
    mock_mode: str = "auto"

    @property
    def mock_enabled(self) -> bool:
        mode = self.mock_mode.strip().lower()
        if mode in {"1", "true", "yes", "on"}:
            return True
        if mode in {"0", "false", "no", "off"}:
            return False
        return not bool(self.api_token)


def get_config() -> CommunityConfig:
    return CommunityConfig(
        api_url=os.getenv("COMMUNITY_API_URL", CommunityConfig.api_url),
        api_token=os.getenv("COMMUNITY_API_TOKEN") or None,
        host=os.getenv("COMMUNITY_MCP_HOST", CommunityConfig.host),
        port=_env("COMMUNITY_MCP_PORT", CommunityConfig.port, int),
        lookback_days=_env("COMMUNITY_LOOKBACK_DAYS", CommunityConfig.lookback_days, int),
        result_limit=_env("COMMUNITY_RESULT_LIMIT", CommunityConfig.result_limit, int),
        timeout_sec=_env("COMMUNITY_TIMEOUT_SEC", CommunityConfig.timeout_sec, float),
        mock_mode=os.getenv("COMMUNITY_MOCK", CommunityConfig.mock_mode),
    )
