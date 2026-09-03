"""전자공시 MCP 환경변수 설정.

비밀 값은 환경변수에서만 읽고, 설정 객체나 로그에서 원문 값을 노출하지 않는다.
"""

from dataclasses import dataclass
import os

from dotenv import load_dotenv

from .errors import ConfigurationError


load_dotenv()


def _env(name: str, default: int, cast: type[int]) -> int:
    value = os.getenv(name)
    if not value:
        return default

    try:
        return cast(value)
    except ValueError as error:
        raise ConfigurationError(f"{name} must be a valid {cast.__name__}.") from error


@dataclass(frozen=True)
class DisclosureConfig:
    """Disclosure MCP 실행에 필요한 환경 설정."""

    dart_api_key: str | None = None
    dart_api_url: str = "https://opendart.fss.or.kr/api"
    database_url: str | None = None
    openai_api_key: str | None = None
    embedding_provider: str | None = None
    embedding_model: str | None = None
    host: str = "0.0.0.0"
    port: int = 8022
    lookback_days: int = 30
    annual_report_top_k: int = 5

    def validate_for_disclosures(self) -> None:
        """OpenDART 공시 조회를 시작하기 전 필수 설정을 검증한다."""

        if not self.dart_api_key:
            raise ConfigurationError("DART_API_KEY is required for OpenDART requests.")
        if len(self.dart_api_key) != 40:
            raise ConfigurationError("DART_API_KEY must be 40 characters.")
        if not self.dart_api_url.startswith("https://"):
            raise ConfigurationError("DART_API_URL must use HTTPS.")
        if self.lookback_days < 1:
            raise ConfigurationError("DART_LOOKBACK_DAYS must be at least 1.")

    def validate_for_annual_report_search(self) -> None:
        """사업보고서 수집·임베딩·검색을 시작하기 전 설정을 검증한다."""

        self.validate_for_disclosures()
        missing = [
            name
            for name, value in {
                "DATABASE_URL": self.database_url,
                "OPENAI_API_KEY": self.openai_api_key,
                "EMBEDDING_PROVIDER": self.embedding_provider,
                "EMBEDDING_MODEL": self.embedding_model,
            }.items()
            if not value
        ]
        if missing:
            raise ConfigurationError(
                f"Missing required configuration: {', '.join(missing)}."
            )
        if not 1 <= self.annual_report_top_k <= 5:
            raise ConfigurationError("ANNUAL_REPORT_TOP_K must be between 1 and 5.")
        if self.embedding_provider != "openai":
            raise ConfigurationError("EMBEDDING_PROVIDER must be 'openai'.")
        if self.embedding_model != "text-embedding-3-small":
            raise ConfigurationError(
                "EMBEDDING_MODEL must be 'text-embedding-3-small' for vector(1536)."
            )


def get_config() -> DisclosureConfig:
    """현재 환경변수에서 설정을 만들되, 비밀값을 출력하지 않는다."""

    return DisclosureConfig(
        dart_api_key=os.getenv("DART_API_KEY") or None,
        dart_api_url=os.getenv("DART_API_URL", DisclosureConfig.dart_api_url),
        database_url=os.getenv("DATABASE_URL") or None,
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        embedding_provider=os.getenv("EMBEDDING_PROVIDER") or None,
        embedding_model=os.getenv("EMBEDDING_MODEL") or None,
        host=os.getenv("DISCLOSURE_MCP_HOST", DisclosureConfig.host),
        port=_env("DISCLOSURE_MCP_PORT", DisclosureConfig.port, int),
        lookback_days=_env("DART_LOOKBACK_DAYS", DisclosureConfig.lookback_days, int),
        annual_report_top_k=_env(
            "ANNUAL_REPORT_TOP_K", DisclosureConfig.annual_report_top_k, int
        ),
    )
