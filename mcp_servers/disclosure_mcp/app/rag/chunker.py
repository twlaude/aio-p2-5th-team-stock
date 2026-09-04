"""사업보고서 섹션을 표 경계를 보존하며 RAG 청크로 나눈다."""

from __future__ import annotations

from dataclasses import dataclass
import re

from .parser import ParsedReportSection


DEFAULT_CHUNK_SIZE = 1_000
DEFAULT_OVERLAP = 150
TABLE_SPLIT_SIZE = 1_500


@dataclass(frozen=True)
class ReportChunk:
    """임베딩·저장 계층으로 넘기는 한 개의 검색 단위."""

    chunk_index: int
    section_title: str
    content: str
    has_table: bool


def chunk_sections(
    sections: list[ParsedReportSection],
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> list[ReportChunk]:
    """여러 섹션을 문서 순서대로 청킹하고 인덱스를 연속 부여한다."""

    chunks: list[ReportChunk] = []
    seen_contents: set[str] = set()
    for section in sections:
        section_chunks = _chunk_section(
            section,
            start_index=len(chunks),
            chunk_size=chunk_size,
            overlap=overlap,
        )
        for chunk in section_chunks:
            if chunk.content in seen_contents:
                continue
            seen_contents.add(chunk.content)
            chunks.append(
                ReportChunk(
                    chunk_index=len(chunks),
                    section_title=chunk.section_title,
                    content=chunk.content,
                    has_table=chunk.has_table,
                )
            )
    return chunks


def _chunk_section(
    section: ParsedReportSection,
    *,
    start_index: int,
    chunk_size: int,
    overlap: int,
) -> list[ReportChunk]:
    _validate_chunk_options(chunk_size, overlap)
    blocks = _to_blocks(section.content)
    contents: list[tuple[str, bool]] = []
    current = ""
    current_has_table = False

    def flush() -> None:
        nonlocal current, current_has_table
        if current:
            contents.append((current, current_has_table))
        current = ""
        current_has_table = False

    for block, is_table in blocks:
        if is_table and len(block) > TABLE_SPLIT_SIZE:
            flush()
            contents.extend((part, True) for part in _split_table(block))
            continue

        block_limit = TABLE_SPLIT_SIZE if is_table else chunk_size
        if len(block) > block_limit:
            flush()
            contents.extend((part, False) for part in _split_text(block, chunk_size, overlap))
            continue

        candidate = f"{current}\n{block}" if current else block
        if current and len(candidate) > chunk_size:
            previous = current
            previous_had_table = current_has_table
            flush()
            # 표의 끝을 다음 청크에 억지로 반복하면 헤더 없는 숫자만 남을 수 있다.
            current = "" if previous_had_table or is_table else _tail(previous, overlap)
            candidate = f"{current}\n{block}" if current else block

        current = candidate
        current_has_table = current_has_table or is_table

    flush()
    return [
        ReportChunk(
            chunk_index=start_index + index,
            section_title=section.section_title,
            content=content,
            has_table=has_table,
        )
        for index, (content, has_table) in enumerate(contents)
    ]


def _to_blocks(content: str) -> list[tuple[str, bool]]:
    """연속된 표 행은 하나의 원자적 블록, 나머지는 문단 블록으로 만든다."""

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    blocks: list[tuple[str, bool]] = []
    table_lines: list[str] = []

    def flush_table() -> None:
        nonlocal table_lines
        if table_lines:
            blocks.append(("\n".join(table_lines), True))
        table_lines = []

    for line in lines:
        if " | " in line:
            table_lines.append(line)
            continue
        flush_table()
        blocks.append((line, False))
    flush_table()
    return blocks


def _split_table(table: str) -> list[str]:
    """큰 표를 헤더 행 반복 방식으로 분할한다."""

    rows = table.splitlines()
    if len(rows) < 2:
        return _split_text(table, TABLE_SPLIT_SIZE, 0)

    header = rows[0]
    parts: list[str] = []
    current = header
    for row in rows[1:]:
        candidate = f"{current}\n{row}"
        if len(candidate) > TABLE_SPLIT_SIZE and current != header:
            parts.append(current)
            current = f"{header}\n{row}"
        else:
            current = candidate
    parts.append(current)
    return parts


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """가능하면 문장 경계에서 자르고, 불가능하면 공백 경계를 사용한다."""

    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= chunk_size:
        return [text]

    parts: list[str] = []
    remaining = text
    while len(remaining) > chunk_size:
        boundary = max(
            remaining.rfind(mark, 0, chunk_size + 1)
            for mark in (". ", "! ", "? ", "다. ", "요. ", " ")
        )
        if boundary <= 0:
            boundary = chunk_size
        else:
            boundary += 1
        part = remaining[:boundary].strip()
        parts.append(part)
        remaining = f"{_tail(part, overlap)} {remaining[boundary:].lstrip()}".strip()
    if remaining:
        parts.append(remaining)
    return parts


def _tail(value: str, size: int) -> str:
    if size <= 0:
        return ""
    return value[-size:].lstrip()


def _validate_chunk_options(chunk_size: int, overlap: int) -> None:
    if chunk_size < 100:
        raise ValueError("chunk_size는 100 이상이어야 합니다.")
    if not 0 <= overlap < chunk_size:
        raise ValueError("overlap은 0 이상 chunk_size 미만이어야 합니다.")
