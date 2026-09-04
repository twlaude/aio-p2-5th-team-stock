import logging
from pathlib import Path

import pytest

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


@pytest.mark.parametrize(
    ("fixture_name", "expected_titles", "expected_text"),
    [
        (
            "hyundai_malformed_excerpt.xml",
            [
                "I. 회사의 개요 > 1. 회사의 개요",
                "II. 사업의 내용 > 1. (제조서비스업)사업의 개요",
            ],
            "S&P(미국) | A",
        ),
        (
            "kb_malformed_excerpt.xml",
            [
                "III. 재무에 관한 사항 > 6. 배당에 관한 사항",
                "VII. 주주에 관한 사항",
            ],
            "배당 정책을 설명합니다.",
        ),
    ],
)
def test_parser_recovers_real_malformed_dart_patterns(
    fixture_name: str, expected_titles: list[str], expected_text: str
) -> None:
    xml = (FIXTURE_PATH.parent / fixture_name).read_text(encoding="utf-8")

    sections = parse_report_sections(xml)

    assert [section.section_title for section in sections] == expected_titles
    assert expected_text in "\n".join(section.content for section in sections)


def test_parser_normalizes_roman_punctuation_and_section_tag_variants() -> None:
    xml = (FIXTURE_PATH.parent / "title_variants_excerpt.xml").read_text(
        encoding="utf-8"
    )

    sections = parse_report_sections(xml)

    assert [section.section_title for section in sections] == [
        "Ⅰ． 회 사의 개요 > １． 회사의 개요",
        "Ⅱ。 사업의 내용 > １：사업의 개요",
    ]
    assert "색인 제외 대상" not in "\n".join(
        section.content for section in sections
    )


def test_parser_logs_available_titles_when_no_target_section(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.WARNING)

    sections = parse_report_sections(
        "<ROOT><SECTION-1><TITLE>IV. 이사의 경영진단</TITLE>"
        "<P>대상 아님</P></SECTION-1></ROOT>"
    )

    assert sections == []
    assert "IV. 이사의 경영진단" in caplog.text
