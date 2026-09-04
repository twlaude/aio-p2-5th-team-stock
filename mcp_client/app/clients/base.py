import asyncio
import json
from typing import Any

from fastmcp import Client


class MCPClientError(Exception):
    def __init__(self, service: str, code: str, message: str, retryable: bool = True) -> None:
        super().__init__(message)
        self.service = service
        self.code = code
        self.message = message
        self.retryable = retryable


class MCPToolClient:
    def __init__(self, service: str, url: str, timeout_seconds: float) -> None:
        self.service = service
        self.url = url
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _extract_result(result: Any) -> dict[str, Any]:
        if isinstance(result, dict):
            return result

        for attribute in ("structured_content", "structuredContent", "data"):
            value = getattr(result, attribute, None)
            if isinstance(value, dict):
                return value

        content = getattr(result, "content", None) or []
        text = "\n".join(
            str(item.text) for item in content if getattr(item, "text", None) is not None
        ).strip()
        if not text:
            raise ValueError("MCP Tool이 JSON 결과를 반환하지 않았습니다.")
        value = json.loads(text)
        if not isinstance(value, dict):
            raise ValueError("MCP Tool 결과는 JSON Object여야 합니다.")
        return value

    async def list_tools(self) -> list[str]:
        try:
            async with asyncio.timeout(self.timeout_seconds):
                async with Client(self.url) as client:
                    tools = await client.list_tools()
        except TimeoutError as exc:
            raise MCPClientError(self.service, "MCP_TIMEOUT", "Tool 조회가 시간 초과되었습니다.") from exc
        except Exception as exc:
            raise MCPClientError(self.service, "MCP_UNAVAILABLE", "MCP 서버에 연결할 수 없습니다.") from exc
        return [tool.name for tool in tools]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            async with asyncio.timeout(self.timeout_seconds):
                async with Client(self.url) as client:
                    result = await client.call_tool(name, arguments)
            value = self._extract_result(result)
        except MCPClientError:
            raise
        except TimeoutError as exc:
            raise MCPClientError(self.service, "MCP_TIMEOUT", "MCP Tool 실행이 시간 초과되었습니다.") from exc
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise MCPClientError(
                self.service,
                "INVALID_MCP_RESPONSE",
                "MCP Tool 응답 형식이 올바르지 않습니다.",
                False,
            ) from exc
        except Exception as exc:
            raise MCPClientError(self.service, "MCP_UNAVAILABLE", "MCP Tool 실행에 실패했습니다.") from exc

        if value.get("status") in {
            "invalid_request",
            "unauthorized",
            "external_api_error",
            "timeout",
            "internal_error",
            "error",
            "unsupported_company",
        }:
            error = value.get("error") or {}
            raise MCPClientError(
                self.service,
                str(error.get("code") or value.get("status")),
                str(error.get("message") or f"{self.service} 조회에 실패했습니다."),
                bool(error.get("retryable", False)),
            )
        return value
