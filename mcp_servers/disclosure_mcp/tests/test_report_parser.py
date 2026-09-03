from pathlib import Path

from app.rag.parser import parse_report_sections


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "annual_report_excerpt.xml"


def test_parser_keeps_only_selected_sections_and_preserves_table() -> None:
    sections = parse_report_sections(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert [section.section_title for section in sections] == [
        "I. 회사의 개요 > 1. 회사의 개요",
        "II. 사업의 내용 > 1. 사업의 개요",
        "III. 재무에 관한 사항 > 6. 배당에 관한 사항",
        "VII. 주주에 관한 사항 > 1. 최대주주",
    ]
    business = sections[1]
    assert business.has_table is True
    assert "구분 | 2025" in business.content
    assert "색인하지 않는 재무제표" not in "\n".join(
        section.content for section in sections
    )
