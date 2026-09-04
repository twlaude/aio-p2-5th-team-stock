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

    backend_event_url: str = ""
    backend_internal_token: str = ""


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
