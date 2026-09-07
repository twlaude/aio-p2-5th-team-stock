"""Deterministic checks of model prose against the collected source context."""

from dataclasses import dataclass
import re
from typing import Any

from app.schemas.analysis import Narrative


RECEIPT_PATTERN = re.compile(r"(?<!\d)\d{14}(?!\d)")
LIMITATIONS = ("확인하지 못", "조회하지 못", "자료가 없", "실패")
VERIFIER_VERSION = "v2_action_patterns"
# Require directive endings: 매도벽, 매수세, 순매수/순매도, 매수/매도 우위,
# 기관 매수 and 외국인 매도 alone are supply/demand facts, not advice.
PROHIBITED_PATTERN = re.compile(
    r"(?:매수|매도|보유)\s*(?:를\s*)?"
    r"(?:하세요|하십시오|하셔야|해야|하는\s*게|추천|시점|타이밍|기회|해\s*보)"
    r"|사세요|파세요|사도\s*좋|목표\s*주가"
    r"|(?:오를|내릴|상승할|하락할)\s*것"
    r"|(?:상승|하락)(?:이|을)?\s*예상(?!보다)|급등할|급락할"
)
SOURCE_TOOLS = {
    "news": {"search_news"},
    "disclosure": {
        "get_recent_disclosures", "get_material_disclosures",
        "search_annual_report", "get_disclosure_detail",
    },
    "community": {"get_community_reaction"},
}


@dataclass(frozen=True)
class Violation:
    kind: str
    detail: str


def _receipts(value: Any) -> set[str]:
    if isinstance(value, dict):
        return {
            str(item) for key, item in value.items() if key == "receipt_number" and item
        } | set().union(*(_receipts(item) for item in value.values()))
    if isinstance(value, list):
        return set().union(*(_receipts(item) for item in value))
    return set()


def _texts(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, (dict, list)):
        for item in value.values() if isinstance(value, dict) else value:
            yield from _texts(item)


def verify_narrative(narrative: Narrative, context: dict[str, Any]) -> list[Violation]:
    data = context.get("data") or {}
    # News/community text cannot promote an injected receipt into official evidence.
    known_receipts = _receipts(context.get("evidence_level") or {})
    for source in ("disclosures", "material_disclosures", "annual_report", "disclosure_details"):
        known_receipts |= _receipts(data.get(source))
    text = str(narrative.model_dump())
    violations = [
        Violation("hallucination", f"컨텍스트에 없는 DART 접수번호입니다: {receipt}")
        for receipt in sorted(set(RECEIPT_PATTERN.findall(text)) - known_receipts)
    ]
    failed_tools = set(context.get("failed_tools") or [])
    failures = [*(context.get("partial_failures") or []), *(context.get("failures") or [])]
    services = {item.get("service") for item in failures if isinstance(item, dict)}
    for source, tools in SOURCE_TOOLS.items():
        keys = ("disclosures", "material_disclosures", "annual_report") if source == "disclosure" else (source,)
        failed = bool(tools & failed_tools) or source in services or f"{source}_mcp" in services
        failed |= any(
            (data.get(key) or {}).get("status") not in (None, "success", "no_data") for key in keys
        )
        summary = getattr(narrative, f"{source}_summary")
        if failed and not any(marker in summary for marker in LIMITATIONS):
            violations.append(Violation("inconsistency", f"{source}_summary에 조회 실패 제한을 명시해야 합니다."))
    terms = list(dict.fromkeys(term for value in _texts(narrative.model_dump())
                              for term in PROHIBITED_PATTERN.findall(value)))
    if terms:
        violations.append(Violation("inconsistency", "추천·예측 금지 표현입니다: " + ", ".join(terms)))
    if (context.get("investment_profile") is not None) != (narrative.personalized_checkpoints is not None):
        violations.append(Violation("inconsistency", "투자 성향 유무와 personalized_checkpoints의 null 여부가 다릅니다."))
    return violations
