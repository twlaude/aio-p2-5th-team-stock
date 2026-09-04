from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/stock_insight"
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl_seconds: int = 1800

    mcp_client_url: str = "http://localhost:8010"
    mcp_client_timeout_seconds: float = 75.0  # 공통 계약: Backend → MCP Client 75초
    mcp_client_mode: str = "mock"  # "mock" | "live"
    narrative_source: str = "agent_first"  # "agent_first": Agent 서사 우선, 실패 시 Backend 조립 | "backend": 항상 Backend 조립

    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    openai_reasoning_effort: str = "low"

    auth_mode: str = "demo"
    demo_user_id: str = "demo-user-a"
    jwt_secret_key: str = "dev-secret-change-me-please-32-bytes-min"
    jwt_expires_minutes: int = 1440  # 24시간

    cors_allowed_origins: str = "http://localhost:5173"

    admin_username: str = "admin"
    admin_password: str = "change-me"

    @field_validator("jwt_secret_key", mode="before")
    @classmethod
    def _jwt_secret_not_empty(cls, value: str) -> str:
        # .env에 JWT_SECRET_KEY= 처럼 비워 두면 HMAC 키 오류로 로그인이 500이 되므로 개발 기본값으로 대체한다.
        return value if isinstance(value, str) and value.strip() else "dev-secret-change-me-please-32-bytes-min"

    @property
    def cors_allowed_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


settings = Settings()
