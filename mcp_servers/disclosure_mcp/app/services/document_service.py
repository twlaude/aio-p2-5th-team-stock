"""DART 공시 XML을 읽기 쉬운 상세 원문으로 변환한다."""

from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from xml.etree import ElementTree

from bs4 import BeautifulSoup
from app.clients.dart import DartClient
from app.clients.repository import DisclosureRepository
from app.schemas.search import DisclosureDetailResponse


DETAIL_CONTENT_LIMIT = 3_000
_LINE_TAGS = {"P", "TITLE", "P0", "P1", "P2", "P3", "P4", "P5"}


class DocumentParseError(ValueError):
    """DART 원문을 사람이 읽을 수 있는 텍스트로 변환할 수 없다."""


class DocumentService:
    """접수번호로 공시 원문을 가져와 MCP 상세 응답으로 정제한다."""

    def __init__(self, *, dart_client: DartClient, repository: DisclosureRepository) -> None:
        self._dart_client = dart_client
        self._repository = repository

    def get_disclosure_detail(self, receipt_number: str) -> DisclosureDetailResponse:
        """원문 전체 길이는 보존하고, 응답 본문은 3,000자로 제한한다."""

        document = self._dart_client.get_document(receipt_number)
        content = flatten_document_xml(document["xml"])
        metadata = self._repository.find_disclosure_metadata(receipt_number)
        source_url = (
            metadata["source_url"]
            if metadata is not None
            else self._source_url(receipt_number)
        )
        total_chars = len(content)
        returned_content = content[:DETAIL_CONTENT_LIMIT]
        response: DisclosureDetailResponse = {
            "status": "success",
            "receipt_number": receipt_number,
            "document_type": "disclosure",
            "content": returned_content,
            "content_truncated": total_chars > DETAIL_CONTENT_LIMIT,
            "total_chars": total_chars,
            "summary": "DART 공시 원문 앞부분",
            "source_url": source_url,
            "collected_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        if metadata is not None:
            response["report_name"] = metadata["report_name"]
            if metadata["published_at"] is not None:
                response["published_at"] = (
                    metadata["published_at"]
                    .astimezone(timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z")
                )
            response["summary"] = f"{metadata['report_name']} 공시 원문 앞부분"
        return response

    @staticmethod
    def _source_url(receipt_number: str) -> str:
        return f"https://dart.fss.or.kr/dsaf001/main.do?rcptNo={receipt_number}"


def flatten_document_xml(xml: str) -> str:
    """DART XML의 문단과 표를 줄 단위 텍스트로 변환한다."""

    try:
        root = ElementTree.fromstring(html.unescape(xml))
    except ElementTree.ParseError:
        return _flatten_html_document(xml)

    lines: list[str] = []

    def collect(element: ElementTree.Element) -> None:
        tag = _local_tag(element.tag)
        if tag == "TABLE":
            lines.extend(_flatten_table(element))
            return
        if tag in _LINE_TAGS:
            text = _element_text_without_tables(element)
            if text:
                lines.append(text)
        for child in element:
            collect(child)

    collect(root)

    if not lines:
        fallback = _normalize_whitespace(" ".join(root.itertext()))
        if fallback:
            lines.append(fallback)
    return "\n".join(_deduplicate_adjacent(lines))


def _flatten_html_document(document: str) -> str:
    """태그 불일치가 있는 DART HTML 혼합 문서를 관대하게 평탄화한다."""

    soup = BeautifulSoup(html.unescape(document), "html.parser")
    lines: list[str] = []
    for element in soup.find_all(["p", "title", "table"]):
        if element.name in {"p", "title"}:
            if element.find_parent("table") is None:
                text = _normalize_whitespace(" ".join(element.stripped_strings))
                if text:
                    lines.append(text)
            continue

        for row in element.find_all("tr"):
            cells = [
                _normalize_whitespace(" ".join(cell.stripped_strings))
                for cell in row.find_all(["td", "th", "te", "tu"], recursive=False)
            ]
            cells = [cell for cell in cells if cell]
            if cells:
                lines.append(" | ".join(cells))

    if not lines:
        fallback = _normalize_whitespace(" ".join(soup.stripped_strings))
        if fallback:
            lines.append(fallback)
    return "\n".join(_deduplicate_adjacent(lines))


def _flatten_table(table: ElementTree.Element) -> list[str]:
    rows: list[str] = []
    for row in table.iter():
        if _local_tag(row.tag) != "TR":
            continue
        cells = [
            _normalize_whitespace(" ".join(cell.itertext()))
            for cell in list(row)
            if _local_tag(cell.tag) in {"TD", "TE", "TU", "TH"}
        ]
        cells = [cell for cell in cells if cell]
        if cells:
            rows.append(" | ".join(cells))
    return rows


def _element_text_without_tables(element: ElementTree.Element) -> str:
    parts: list[str] = []

    def visit(node: ElementTree.Element) -> None:
        if _local_tag(node.tag) == "TABLE":
            return
        if node.text:
            parts.append(node.text)
        for child in node:
            visit(child)
            if child.tail:
                parts.append(child.tail)

    visit(element)
    return _normalize_whitespace(" ".join(parts))


def _local_tag(tag: str) -> str:
    return tag.rsplit("}", maxsplit=1)[-1].upper()


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _deduplicate_adjacent(lines: list[str]) -> list[str]:
    result: list[str] = []
    for line in lines:
        if not result or result[-1] != line:
            result.append(line)
    return result
