"""stock_insight MCP 서버 진입점.

툴 구현은 app/tools/, 로직은 app/services/ 에 두고 여기서는 등록만 한다.
"""
import os

from fastmcp import FastMCP

mcp = FastMCP("stock_insight")


@mcp.tool()
def ping() -> str:
    """서버 생존 확인용 툴."""
    return "pong"


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host=os.getenv("MCP_HOST", "0.0.0.0"),
        port=int(os.getenv("MCP_PORT", "8050")),
    )
