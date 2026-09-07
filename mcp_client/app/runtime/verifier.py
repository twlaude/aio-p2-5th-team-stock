"""Deterministic checks of model prose against the collected source context."""

from dataclasses import dataclass
import re
from typing import Any

from app.schemas.analysis import Narrative


RECEIPT_PATTERN = re.compile(r"(?<!\d)\d{14}(?!\d)")
VERIFIER_VERSION = "v3_context_patterns"
# Require directive endings: 매도벽, 매수세, 순매수/순매도, 매수/매도 우위,
# 기관 매수 and 외국인 매도 alone are supply/demand facts, not advice.
PROHIBITED_PATTERN = re.compile(
    r"(?:매수|매도|보유)\s*(?:를\s*)?"
    r"(?:하세요|하십시오|하셔야|해야|하는\s*게|추천|시점|타이밍|기회|해\s*보)"
    r"|사세요|파세요|사도\s*좋"
    r"|(?:오를|내릴|상승할|하락할)\s*것"
    r"|(?:상승|하락)(?:이|을)?\s*예상(?!보다)|급등할|급락할"
)
TARGET_PRICE = re.compile(r"목표\s*주가")
# Keep exceptions local: a denial must not license advice in another clause.
CLAUSE_BOUNDARY = re.compile(r"[.!?。！？;\n]+|하지만|그러나|반면|다만|(?<=지만)\s*")
TARGET_DENIAL = re.compile(
    r"(?:제시|산정|제공|추천|예측)하지\s*않(?:습니다|아요|으며|고)"
    r"|(?:확인되지\s*않(?:았|아)|확인할\s*수\s*없|공시는?\s*없)"
    r"|(?:제시|산정|제공|추천|예측)(?:하는)?\s*(?:것이\s*)?아닙니다"
)
LIMITATION_PATTERN = re.compile(
    r"(?:확인|조회|수집|제공)(?:하지\s*못|되지\s*않(?:았|아)|할\s*수\s*없)"
    r"|(?:확인|조회|수집)(?:이|가|하기)?\s*(?:어렵|어려|불가)"
    r"|(?:조회|수집|호출)(?:에|가|는)?\s*(?:(?:외부\s*)?API\s*오류로\s*)?"
    r"(?:실패(?:했|해|하였|로|입니다)|오류)"
    r"|(?:자료|데이터|표본)(?:가|이|는|을)?\s*없(?:습니다|어요|어|으)"
)
SOURCE_LABELS = {"news": r"뉴스|기사|증권사", "disclosure": r"공시|사업보고서|연차보고서",
                 "community": r"커뮤니티|게시글|게시물"}
QUOTED_TEXT = re.compile(r'"([^"\n]+)"|“([^”\n]+)”|‘([^’\n]+)’|「([^」\n]+)」')
REPORTED = re.compile(r"(?:보도|인용|언급|전했|적혀|실렸|기재|담겼)")
DOUBLE_NEGATION = re.compile(r"(?:것은|것이)\s*아[니닙]|지는\s*않")
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


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _source_before(text: str) -> str | None:
    mentions = [(match.end(), source) for source, labels in SOURCE_LABELS.items()
                for match in re.finditer(labels, text)]
    return max(mentions)[1] if mentions else None


def _has_limitation(summary: str, source: str) -> bool:
    for clause in CLAUSE_BOUNDARY.split(summary.replace(",", ";")):
        # A business failure (e.g. 임상 실패) is not a retrieval limitation.
        if not re.search(SOURCE_LABELS[source] + r"|자료|데이터|표본|조회|수집", clause):
            continue
        for match in LIMITATION_PATTERN.finditer(clause):
            if _source_before(clause[:match.start()]) not in (None, source):
                continue
            if not DOUBLE_NEGATION.search(clause[match.end():]):
                return True
    return False


def _target_terms(text: str, data: dict[str, Any]):
    for clause in CLAUSE_BOUNDARY.split(text):
        quoted_spans = []
        for quote in QUOTED_TEXT.finditer(clause):
            quoted = next(group for group in quote.groups() if group is not None)
            # Only a verbatim quotation from the attributed collected source qualifies.
            source = _source_before(clause[:quote.start()])
            keys = ("disclosures", "material_disclosures", "annual_report", "disclosure_details") if source == "disclosure" else (source,)
            if (source and REPORTED.search(clause[quote.end():])
                    and any(_compact(quoted) in _compact(value)
                            for key in keys for value in _texts(data.get(key)))):
                quoted_spans.append(quote.span())
        targets = list(TARGET_PRICE.finditer(clause))
        for index, match in enumerate(targets):
            end = targets[index + 1].start() if index + 1 < len(targets) else len(clause)
            tail = clause[match.end():end]
            denial = TARGET_DENIAL.search(tail)
            # Numeric targets and double negation remain conservative violations.
            denied = (denial is not None and not re.search(r"\d|[=]|[영공일이삼사오육칠팔구십백천만억]+\s*원", tail)
                      and not re.search(r"입니다|이에요|확실", tail[:denial.start()])
                      and not re.search(r"추천|권장|예측|제시", tail[denial.end():])
                      and not DOUBLE_NEGATION.search(tail[denial.end():]))
            if not denied and not any(start <= match.start() < end for start, end in quoted_spans):
                yield match.group()


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
        if failed and not _has_limitation(summary, source):
            violations.append(Violation("inconsistency", f"{source}_summary에 조회 실패 제한을 명시해야 합니다."))
    terms = list(dict.fromkeys(term for value in _texts(narrative.model_dump())
                              for term in [*PROHIBITED_PATTERN.findall(value), *_target_terms(value, data)]))
    if terms:
        violations.append(Violation("inconsistency", "추천·예측 금지 표현입니다: " + ", ".join(terms)))
    if (context.get("investment_profile") is not None) != (narrative.personalized_checkpoints is not None):
        violations.append(Violation("inconsistency", "투자 성향 유무와 personalized_checkpoints의 null 여부가 다릅니다."))
    return violations
