from app.services.analysis_builder.sources import collect_sources
from tests.helpers import collected_data


def test_collect_sources_preserves_frontend_metadata():
    data = collected_data()
    data.disclosures["disclosures"][0]["document_type"] = "disclosure"
    data.annual_report.update({"receipt_number": "202509040001", "document_type": "annual_report"})
    data.material_disclosures["disclosures"].append(
        {
            "report_name": "최대주주변경",
            "receipt_number": "202609020101",
            "published_at": "2026-09-02T00:00:00Z",
            "document_type": "disclosure",
            "disclosure_kind": "major",
            "source_url": "https://dart.fss.or.kr/material/3",
        }
    )

    sources = collect_sources(data)

    assert sources[1].meta == {"publisher": "example.com"}
    assert [source.title for source in sources[6:10]] == [
        "단일판매ㆍ공급계약체결",
        "최대주주변경",
        "주요사항보고서",
        "2025년 사업보고서",
    ]
    assert sources[6].meta == {
        "confirmed": ["대규모 공급계약 효과"],
        "disclosure_kind": "major",
        "receipt_number": "202609040101",
        "document_type": "disclosure",
        "unconfirmed": ["업황", "삼성전자 관련 뉴스 0", "삼성전자 관련 뉴스 1"],
    }
    assert sources[8].meta["disclosure_kind"] == "periodic"
    assert sources[9].meta == {
        "disclosure_kind": "periodic",
        "receipt_number": "202509040001",
        "document_type": "annual_report",
    }
    assert sources[10].meta == {
        "samples": 50,
        "positive": 20,
        "neutral": 20,
        "negative": 10,
        "fgi": 75.0,
        "fgi_label": "탐욕",
        "topics": [
            {"text": "대규모 공급계약 효과", "sentiment": "positive", "weight": 5},
            {"text": "업황", "sentiment": "negative", "weight": 5},
        ],
    }
    assert sum(source.source_type == "disclosure" for source in sources) == 4
