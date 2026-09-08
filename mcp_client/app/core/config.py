from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = Field(default="0.0.0.0", validation_alias="MCP_CLIENT_HOST")
    port: int = Field(default=8010, validation_alias="MCP_CLIENT_PORT")

    price_mcp_url: str = "http://localhost:8020/mcp"
    news_mcp_url: str = "http://localhost:8021/mcp"
    disclosure_mcp_url: str = "http://localhost:8022/mcp"
    community_mcp_url: str = "http://localhost:8023/mcp"
    mcp_request_timeout_seconds: float = 15.0
    workflow_timeout_seconds: float = 60.0

    llm_provider: Literal["openai", "mock"] = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    openai_reasoning_effort: str = "low"
    max_agent_steps: int = 3
    # 사업보고서 벡터검색 유사도 하한. 실측 상위 5건 점수가 0.35~0.51 수준이라
    # 0.7 같은 값은 전부 걸러져 사업보고서 근거가 0건이 된다. 기본은 서버와 같은 0.0(필터 없음).
    annual_report_min_score: float = Field(default=0.0, ge=0.0, le=1.0)
    agent_reflection_enabled: bool = True
    agent_max_reflections: int = Field(default=2, ge=0)

    backend_event_url: str = ""
    backend_internal_token: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
