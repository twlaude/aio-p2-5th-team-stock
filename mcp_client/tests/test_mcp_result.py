from types import SimpleNamespace

from app.clients.base import MCPToolClient


def test_extracts_json_text_from_mcp_result():
    result = SimpleNamespace(content=[SimpleNamespace(text='{"status":"success","value":1}')])

    assert MCPToolClient._extract_result(result) == {"status": "success", "value": 1}


def test_prefers_structured_content():
    result = SimpleNamespace(
        structured_content={"status": "success", "value": 2},
        content=[],
    )

    assert MCPToolClient._extract_result(result)["value"] == 2
