"""Disclosure MCP 서버 진입점."""

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_config
from app.tools.disclosure import register_disclosure_tools


mcp = FastMCP("disclosure_mcp")
register_disclosure_tools(mcp)


@mcp.custom_route("/health", methods=["GET"])
async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "disclosure_mcp"})


if __name__ == "__main__":
    settings = get_config()
    mcp.run(
        transport="streamable-http",
        host=settings.host,
        port=settings.port,
    )
