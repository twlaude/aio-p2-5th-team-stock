from datetime import datetime, timedelta, timezone

from app.services.analysis_builder.issues import extract_issues
from app.services.analysis_builder.matching import (
    is_material_disclosure,
    match_issues,
    recent_material_disclosures,
)
from tests.helpers import collected_data


def _published(days_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


def _disclosure(
    report_name: str, receipt_number: str, days_ago: int, kind: str = "other"
) -> dict[str, str]:
    return {
        "report_name": report_name,
        "receipt_number": receipt_number,
        "published_at": _published(days_ago),
        "disclosure_kind": kind,
    }


def test_extract_issues_preserves_priority_deduplicates_and_requires_exact_company_name():
    data = collected_data()
    data.community["top_topics"] = {
        "expectations": [" 공급   계약 ", "신규 공장", "공급 계약", "제외"],
        "concerns": ["소송 우려", "업황", "제외"],
    }
    data.news["articles"] = [
        {"headline": "전자 공급계약 보도"},
        {"headline": "삼성전자 신규 수주"},
        {"headline": "삼성전자 실적 발표"},
    ]

    assert extract_issues(data, "삼성전자") == [
        "공급 계약",
        "신규 공장",
        "소송 우려",
        "업황",
        "삼성전자 신규 수주",
        "삼성전자 실적 발표",
    ]


def test_material_filter_accepts_title_variants_and_major_kind_but_excludes_noise_and_old_items():
    payload = {
        "status": "success",
        "disclosures": [
            _disclosure("단일판매·공급계약체결", "1", 1),
            _disclosure("분류는 major인 별도 공시", "2", 2, "major"),
            _disclosure("기업설명회(IR)개최", "3", 1),
            _disclosure("자기주식취득결정", "4", 31),
        ],
    }

    assert is_material_disclosure(payload["disclosures"][0]) is True
    assert [item["receipt_number"] for item in recent_material_disclosures(payload)] == ["1", "2"]


def test_match_issues_selects_latest_disclosure_per_issue_and_tracks_unmatched():
    payload = {
        "status": "success",
        "disclosures": [
            _disclosure("단일판매ㆍ공급계약체결", "new", 1, "major"),
            _disclosure("단일판매공급계약체결", "old", 5, "major"),
            _disclosure("소송등의제기", "lawsuit", 2, "major"),
        ],
    }

    result = match_issues(["대규모 수주 기대", "배당 확대"], payload)

    assert result.matched[0].receipt_number == "new"
    assert result.unmatched == ["배당 확대"]
    assert result.material_count == 3
    assert result.major_receipts == ["new", "lawsuit", "old"]


def test_match_issues_supports_smr_rule_without_similarity_scoring():
    payload = {
        "status": "success",
        "disclosures": [_disclosure("단일판매ㆍ공급계약체결", "smr", 0, "major")],
    }

    result = match_issues(["SMR 원전 사업 기대"], payload)

    assert result.matched[0].receipt_number == "smr"
