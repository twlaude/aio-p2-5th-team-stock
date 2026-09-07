RISK_READ = "read"
RISK_CHANGE = "change"
RISK_FORBIDDEN = "forbidden"

TOOL_RISK: dict[str, str] = dict.fromkeys((
    "get_stock_quote", "search_news", "get_recent_disclosures",
    "get_material_disclosures", "search_annual_report",
    "get_community_reaction", "get_disclosure_detail",
), RISK_READ)
CHANGE_TOOLS = frozenset()
FORBIDDEN_TOOLS = frozenset({"place_order", "make_payment", "send_message", "update_profile"})


def action_risk(tool_name: str, allowed_tools: frozenset[str]) -> str:
    if tool_name in FORBIDDEN_TOOLS or tool_name not in allowed_tools:
        return RISK_FORBIDDEN
    if tool_name in CHANGE_TOOLS:
        return RISK_CHANGE
    return TOOL_RISK.get(tool_name, RISK_READ)
