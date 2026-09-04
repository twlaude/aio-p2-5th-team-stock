"""DART 정기보고서 XML에서 검색 가치가 있는 섹션만 추출한다."""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
import logging
import re
import unicodedata
from xml.etree import ElementTree


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedReportSection:
    """청커에 전달할 사업보고서의 의미 단위."""

    section_title: str
    content: str
    has_table: bool


class ReportParseError(ValueError):
    """DART 정기보고서 XML을 해석할 수 없다."""


@dataclass
class _SectionState:
    level: int
    title: str = ""
    lines: list[str] = field(default_factory=list)
    has_table: bool = False
    child_section_count: int = 0


class _DartHTMLRecoveryParser(HTMLParser):
    """깨진 XML을 재직렬화하지 않고 문서 순서대로 복구한다."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.section_stack: list[_SectionState] = []
        self.sections: list[ParsedReportSection] = []
        self.top_titles: list[str] = []
        self._capturing_title = False
        self._title_parts: list[str] = []
        self._paragraph_depth = 0
        self._paragraph_parts: list[str] = []
        self._table_depth = 0
        self._table_rows: list[list[str]] = []
        self._current_row: list[str] | None = None
        self._cell_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        level = _section_level(tag)
        if level is not None:
            self.section_stack.append(_SectionState(level=level))
            return
        tag_name = tag.upper()
        if tag_name == "TITLE" and self.section_stack:
            self._capturing_title = True
            self._title_parts = []
            return
        if tag_name == "TABLE":
            self._table_depth += 1
            if self._table_depth == 1:
                self._table_rows = []
            return
        if self._table_depth:
            if tag_name == "TR":
                self._current_row = []
            elif tag_name in {"TD", "TE", "TU", "TH"}:
                self._cell_parts = []
            return
        if tag_name == "P":
            self._paragraph_depth += 1
            if self._paragraph_depth == 1:
                self._paragraph_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag_name = tag.upper()
        if tag_name == "TITLE" and self._capturing_title:
            self._finish_title()
            return
        if _section_level(tag) is not None:
            if self._table_depth:
                self._force_finish_table()
            self._finish_section()
            return
        if self._table_depth:
            if tag_name in {"TD", "TE", "TU", "TH"}:
                self._finish_cell()
            elif tag_name == "TR":
                self._finish_row()
            elif tag_name == "TABLE":
                self._finish_table()
            return
        if tag_name == "P" and self._paragraph_depth:
            self._paragraph_depth -= 1
            if self._paragraph_depth == 0:
                self._finish_paragraph()

    def handle_data(self, data: str) -> None:
        if self._capturing_title:
            self._title_parts.append(data)
        elif self._cell_parts is not None:
            self._cell_parts.append(data)
        elif self._paragraph_depth:
            self._paragraph_parts.append(data)

    def finish(self) -> None:
        if self._table_depth:
            self._force_finish_table()
        if self._paragraph_depth:
            self._finish_paragraph()
            self._paragraph_depth = 0
        while self.section_stack:
            self._finish_section()

    def _finish_title(self) -> None:
        title = _normalize_whitespace(" ".join(self._title_parts))
        current = self.section_stack[-1] if self.section_stack else None
        if current is not None and not current.title:
            current.title = title
            if current.level == 1 and title:
                self.top_titles.append(title)
        self._capturing_title = False
        self._title_parts = []

    def _finish_paragraph(self) -> None:
        text = _normalize_whitespace(" ".join(self._paragraph_parts))
        self._paragraph_parts = []
        if text and self.section_stack:
            self.section_stack[-1].lines.append(text)

    def _finish_cell(self) -> None:
        if self._current_row is not None and self._cell_parts is not None:
            text = _normalize_whitespace(" ".join(self._cell_parts))
            if text:
                self._current_row.append(text)
        self._cell_parts = None

    def _finish_row(self) -> None:
        if self._current_row:
            self._table_rows.append(self._current_row)
        self._current_row = None

    def _finish_table(self) -> None:
        self._table_depth -= 1
        if self._table_depth == 0:
            self._append_table()

    def _force_finish_table(self) -> None:
        self._finish_cell()
        self._finish_row()
        self._table_depth = 0
        self._append_table()

    def _append_table(self) -> None:
        current = self.section_stack[-1] if self.section_stack else None
        if current is not None and self._table_rows:
            current.lines.extend(" | ".join(row) for row in self._table_rows if row)
            current.has_table = True
        self._table_rows = []

    def _finish_section(self) -> None:
        if not self.section_stack:
            return
        section = self.section_stack.pop()
        parent = self.section_stack[-1] if self.section_stack else None
        top = next(
            (item for item in reversed(self.section_stack) if item.level == 1),
            None,
        )
        if section.level == 2 and top is not None:
            top.child_section_count += 1
            kind = _selected_top_section(top.title)
            if kind is not None and _include_child(kind, section.title):
                parsed = _build_section_from_lines(
                    f"{top.title} > {section.title}" if section.title else top.title,
                    section.lines,
                    section.has_table,
                )
                if parsed is not None:
                    self.sections.append(parsed)
        elif section.level == 1 and section.child_section_count == 0:
            if _selected_top_section(section.title) is not None:
                parsed = _build_section_from_lines(
                    section.title, section.lines, section.has_table
                )
                if parsed is not None:
                    self.sections.append(parsed)
        if parent is not None:
            parent.lines.extend(section.lines)
            parent.has_table = parent.has_table or section.has_table


def parse_report_sections(xml: str) -> list[ParsedReportSection]:
    """분석용 섹션만 골라 문단과 표를 보존한 순서대로 반환한다.

    선택 범위는 회사 개요(1~2), 사업의 내용(전체), 배당, 주주에 관한 사항이다.
    재무제표·주석처럼 숫자 표 중심인 섹션은 색인하지 않는다.
    """

    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError:
        # DART 원문에는 미이스케이프 '&'와 비표준 한글 태그가 섞여 있다.
        # HTMLParser가 허용하는 형태로 읽되 XML로 재직렬화하지 않는다.
        try:
            parser = _DartHTMLRecoveryParser()
            parser.feed(xml)
            parser.close()
            parser.finish()
            parsed, top_titles = parser.sections, parser.top_titles
        except Exception as error:
            raise ReportParseError("DART 정기보고서 XML을 파싱하지 못했습니다.") from error
    else:
        parsed, top_titles = _parse_element_tree(root)

    if not parsed:
        titles = " | ".join(top_titles[:20]) or "(없음)"
        LOGGER.warning("색인 가능한 사업보고서 섹션이 없습니다. 상위 제목: %s", titles)
    return parsed


def _parse_element_tree(
    root: ElementTree.Element,
) -> tuple[list[ParsedReportSection], list[str]]:
    parsed: list[ParsedReportSection] = []
    top_titles: list[str] = []
    for top_section in (item for item in root.iter() if _section_level(_tag(item)) == 1):
        top_title = _direct_title(top_section)
        if top_title:
            top_titles.append(top_title)
        section_kind = _selected_top_section(top_title)
        if section_kind is None:
            continue

        child_sections = [item for item in top_section if _section_level(_tag(item)) == 2]
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
    return parsed, top_titles


def _selected_top_section(title: str) -> str | None:
    normalized = _normalize_title(title)
    roman_match = re.match(r"^([IVX]+)", normalized)
    roman = roman_match.group(1) if roman_match else ""
    if roman == "I" and "회사의개요" in normalized:
        return "company_overview"
    if roman == "II" and "사업의내용" in normalized:
        return "business"
    if roman == "III" and "재무에관한사항" in normalized:
        return "financial"
    if roman == "VII" and "주주에관한사항" in normalized:
        return "shareholders"
    return None


def _include_child(section_kind: str, child_title: str) -> bool:
    normalized = _normalize_title(child_title)
    number_match = re.match(r"^(\d+)", normalized)
    number = number_match.group(1) if number_match else ""
    if section_kind == "company_overview":
        return number in {"1", "2"}
    if section_kind == "financial":
        return number == "6" and "배당" in normalized
    return section_kind in {"business", "shareholders"}


def _build_section(
    section_title: str, section: ElementTree.Element
) -> ParsedReportSection | None:
    lines, has_table = _extract_content(section)
    return _build_section_from_lines(section_title, lines, has_table)


def _build_section_from_lines(
    section_title: str, lines: list[str], has_table: bool
) -> ParsedReportSection | None:
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
        if _section_level(tag) is not None and element is not section:
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


def _section_level(tag: str) -> int | None:
    match = re.fullmatch(r"SECTION-?(\d+)", tag.upper())
    return int(match.group(1)) if match else None


def _normalize_title(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    return re.sub(r"[\W_]+", "", normalized, flags=re.UNICODE)


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _deduplicate_adjacent(lines: list[str]) -> list[str]:
    result: list[str] = []
    for line in lines:
        if not result or result[-1] != line:
            result.append(line)
    return result
