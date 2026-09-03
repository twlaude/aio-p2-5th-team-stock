"""DART 정기보고서 XML에서 검색 가치가 있는 섹션만 추출한다."""

from __future__ import annotations

from dataclasses import dataclass
import html
import re
from xml.etree import ElementTree


@dataclass(frozen=True)
class ParsedReportSection:
    """청커에 전달할 사업보고서의 의미 단위."""

    section_title: str
    content: str
    has_table: bool


class ReportParseError(ValueError):
    """DART 정기보고서 XML을 해석할 수 없다."""


def parse_report_sections(xml: str) -> list[ParsedReportSection]:
    """분석용 섹션만 골라 문단과 표를 보존한 순서대로 반환한다.

    선택 범위는 회사 개요(1~2), 사업의 내용(전체), 배당, 주주에 관한 사항이다.
    재무제표·주석처럼 숫자 표 중심인 섹션은 색인하지 않는다.
    """

    try:
        root = ElementTree.fromstring(html.unescape(xml))
    except ElementTree.ParseError as error:
        raise ReportParseError("DART 정기보고서 XML을 파싱하지 못했습니다.") from error

    parsed: list[ParsedReportSection] = []
    for top_section in (item for item in root.iter() if _tag(item) == "SECTION-1"):
        top_title = _direct_title(top_section)
        section_kind = _selected_top_section(top_title)
        if section_kind is None:
            continue

        child_sections = [item for item in top_section if _tag(item) == "SECTION-2"]
        if not child_sections:
            section = _build_section(top_title, top_section)
            if section is not None:
                parsed.append(section)
            continue

        for child_section in child_sections:
            child_title = _direct_title(child_section)
            if not _include_child(section_kind, child_title):
                continue
            section = _build_section(
                f"{top_title} > {child_title}" if child_title else top_title,
                child_section,
            )
            if section is not None:
                parsed.append(section)
    return parsed


def _selected_top_section(title: str) -> str | None:
    normalized = _normalize(title)
    if normalized.startswith("I.") and "회사의개요" in normalized:
        return "company_overview"
    if normalized.startswith("II.") and "사업의내용" in normalized:
        return "business"
    if normalized.startswith("III.") and "재무에관한사항" in normalized:
        return "financial"
    if normalized.startswith("VII.") and "주주에관한사항" in normalized:
        return "shareholders"
    return None


def _include_child(section_kind: str, child_title: str) -> bool:
    normalized = _normalize(child_title)
    if section_kind == "company_overview":
        return normalized.startswith("1.") or normalized.startswith("2.")
    if section_kind == "financial":
        return normalized.startswith("6.") and "배당" in normalized
    return section_kind in {"business", "shareholders"}


def _build_section(
    section_title: str, section: ElementTree.Element
) -> ParsedReportSection | None:
    lines, has_table = _extract_content(section)
    content = "\n".join(_deduplicate_adjacent(lines))
    if not content:
        return None
    return ParsedReportSection(
        section_title=section_title,
        content=content,
        has_table=has_table,
    )


def _extract_content(section: ElementTree.Element) -> tuple[list[str], bool]:
    lines: list[str] = []
    has_table = False

    def collect(element: ElementTree.Element) -> None:
        nonlocal has_table
        tag = _tag(element)
        if tag.startswith("SECTION-") and element is not section:
            return
        if tag == "TABLE":
            has_table = True
            lines.extend(_flatten_table(element))
            return
        if tag == "P":
            text = _text_without_tables(element)
            if text:
                lines.append(text)
        for child in element:
            if _tag(child) != "TITLE":
                collect(child)

    collect(section)
    return lines, has_table


def _flatten_table(table: ElementTree.Element) -> list[str]:
    rows: list[str] = []
    for row in table.iter():
        if _tag(row) != "TR":
            continue
        cells = [
            _normalize_whitespace(" ".join(cell.itertext()))
            for cell in row
            if _tag(cell) in {"TD", "TE", "TU", "TH"}
        ]
        cells = [cell for cell in cells if cell]
        if cells:
            rows.append(" | ".join(cells))
    return rows


def _text_without_tables(element: ElementTree.Element) -> str:
    parts: list[str] = []

    def visit(node: ElementTree.Element) -> None:
        if _tag(node) == "TABLE":
            return
        if node.text:
            parts.append(node.text)
        for child in node:
            visit(child)
            if child.tail:
                parts.append(child.tail)

    visit(element)
    return _normalize_whitespace(" ".join(parts))


def _direct_title(element: ElementTree.Element) -> str:
    for child in element:
        if _tag(child) == "TITLE":
            return _normalize_whitespace(" ".join(child.itertext()))
    return ""


def _tag(element: ElementTree.Element) -> str:
    return element.tag.rsplit("}", maxsplit=1)[-1].upper()


def _normalize(value: str) -> str:
    return re.sub(r"\s+", "", value)


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _deduplicate_adjacent(lines: list[str]) -> list[str]:
    result: list[str] = []
    for line in lines:
        if not result or result[-1] != line:
            result.append(line)
    return result
