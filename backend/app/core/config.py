from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/stock_insight"
    openai_api_key: str = ""
    dart_api_key: str = ""
    mcp_server_url: str = "http://localhost:8050"


settings = Settings()
