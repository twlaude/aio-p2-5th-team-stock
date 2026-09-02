from fastmcp import FastMCP
from starlette.responses import JSONResponse

from app.core.config import get_config
from app.tools.community import register_community_tools

mcp = FastMCP("community_mcp")
register_community_tools(mcp)


@mcp.custom_route("/health", methods=["GET"])
async def health(request) -> JSONResponse:
    config = get_config()
    return JSONResponse(
        {"status": "ok", "service": "community_mcp", "mock": config.mock_enabled}
    )


if __name__ == "__main__":
    server_config = get_config()
    mcp.run(
        transport="streamable-http",
        host=server_config.host,
        port=server_config.port,
    )
