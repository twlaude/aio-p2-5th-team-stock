from dataclasses import dataclass
from datetime import date, datetime, timezone
import re
from typing import Any

from app.schemas.analysis import MatchedDisclosure


MATERIAL_TERMS = (
    "단일판매ㆍ공급계약",
    "단일판매·공급계약",
    "단일판매공급계약",
    "영업(잠정)실적",
    "매출액또는손익구조",
    "유상증자",
    "무상증자",
    "전환사채",
    "자기주식",
    "주식소각",
    "현금ㆍ현물배당",
    "합병",
    "분할",
    "신규시설투자",
    "타법인주식및출자증권취득",
    "조회공시요구에대한답변",
    "풍문또는보도에대한해명",
    "소송",
    "최대주주변경",
    "영업정지",
    "중대재해",
)

# 이슈 문장 키워드군 -> 공시명 키워드군. 임베딩이나 유사도 점수는 쓰지 않는다.
ISSUE_RULES = (
    (("수주", "계약", "공급", "납품"), ("단일판매", "공급계약")),
    (("실적", "매출", "이익", "어닝"), ("영업잠정실적", "손익구조")),
    (("유상증자", "증자", "자금조달"), ("유상증자", "무상증자", "증권신고서")),
    (("전환사채", "CB", "채권"), ("전환사채", "증권신고서")),
    (("자사주", "자기주식", "소각"), ("자기주식", "주식소각")),
    (("배당", "주주환원"), ("배당", "자기주식", "주식소각")),
    (("합병", "분할", "상장"), ("합병", "분할", "분할상장")),
    (("투자", "설비", "증설", "공장"), ("신규시설투자", "타법인주식")),
    (("소송", "분쟁"), ("소송",)),
    (("지분", "최대주주", "대량보유"), ("최대주주", "대량보유")),
    (("파업", "사고", "중대재해"), ("중대재해", "영업정지")),
    (("논란", "의혹", "풍문", "보도"), ("풍문또는보도", "조회공시")),
    (("영업정지", "가동중단", "생산중단"), ("영업정지",)),
    (("인수", "출자", "자회사"), ("타법인주식", "합병")),
    (("SMR", "원전", "수주"), ("단일판매", "공급계약")),
)


@dataclass(frozen=True)
class MatchResult:
    matched: list[MatchedDisclosure]
    unmatched: list[str]
    material_count: int
    major_receipts: list[str]


def _normalized(value: object) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]", "", str(value or "")).lower()


_NORMALIZED_MATERIAL_TERMS = tuple(_normalized(term) for term in MATERIAL_TERMS)


def _published_date(value: object) -> date | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = datetime.strptime(raw, "%Y%m%d")
        except ValueError:
            return None
    return parsed.date()


def is_recent_disclosure(disclosure: dict[str, Any]) -> bool:
    published = _published_date(disclosure.get("published_at"))
    if published is None:
        return False
    days_ago = (datetime.now(timezone.utc).date() - published).days
    return 0 <= days_ago <= 30


def disclosure_date_label(value: object) -> str:
    published = _published_date(value)
    return f"{published.month}월 {published.day}일" if published else "날짜 미상"


def is_material_disclosure(disclosure: dict[str, Any]) -> bool:
    if disclosure.get("disclosure_kind") == "major":
        return True
    report_name = _normalized(disclosure.get("report_name"))
    return any(term in report_name for term in _NORMALIZED_MATERIAL_TERMS)


def recent_material_disclosures(payload: dict[str, Any]) -> list[dict[str, Any]]:
    disclosures = payload.get("disclosures") or []
    material = [
        item
        for item in disclosures
        if isinstance(item, dict) and is_recent_disclosure(item) and is_material_disclosure(item)
    ]
    return sorted(
        material,
        key=lambda item: _published_date(item.get("published_at")) or date.min,
        reverse=True,
    )


def _matches(issue: str, report_name: str) -> bool:
    normalized_issue = _normalized(issue)
    normalized_report = _normalized(report_name)
    for issue_terms, report_terms in ISSUE_RULES:
        if any(_normalized(term) in normalized_issue for term in issue_terms) and any(
            _normalized(term) in normalized_report for term in report_terms
        ):
            return True
    return False


def match_issues(issues: list[str], material_disclosures: dict[str, Any]) -> MatchResult:
    material = recent_material_disclosures(material_disclosures)
    matched: list[MatchedDisclosure] = []
    unmatched: list[str] = []

    for issue in issues:
        disclosure = next(
            (item for item in material if _matches(issue, str(item.get("report_name") or ""))),
            None,
        )
        if disclosure is None:
            unmatched.append(issue)
            continue
        matched.append(
            MatchedDisclosure(
                issue=issue,
                report_name=str(disclosure.get("report_name") or "전자공시"),
                receipt_number=str(disclosure.get("receipt_number") or ""),
                published_at=str(disclosure.get("published_at") or ""),
            )
        )

    receipts = list(
        dict.fromkeys(
            str(item.get("receipt_number"))
            for item in material
            if item.get("receipt_number")
        )
    )
    return MatchResult(
        matched=matched,
        unmatched=unmatched,
        material_count=len(material),
        major_receipts=receipts,
    )
