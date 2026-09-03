from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/stock_insight"
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl_seconds: int = 1800

    mcp_client_url: str = "http://localhost:8010"
    mcp_client_timeout_seconds: float = 75.0  # 공통 계약: Backend → MCP Client 75초
    mcp_client_mode: str = "mock"  # "mock" | "live"

    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    openai_reasoning_effort: str = "low"

    auth_mode: str = "demo"
    demo_user_id: str = "demo-user-a"
    jwt_secret_key: str = "dev-secret-change-me"

    cors_allowed_origins: str = "http://localhost:5173"

    @property
    def cors_allowed_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


settings = Settings()
