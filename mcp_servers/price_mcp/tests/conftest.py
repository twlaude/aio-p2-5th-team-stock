from pathlib import Path
import sys

MCP_ROOT = Path(__file__).resolve().parents[1]
if str(MCP_ROOT) not in sys.path:
    sys.path.insert(0, str(MCP_ROOT))


def pytest_sessionstart(session):
    print("[TEST] price_mcp tests start")


def pytest_sessionfinish(session, exitstatus):
    print(f"[TEST] price_mcp tests exitstatus={exitstatus}")
