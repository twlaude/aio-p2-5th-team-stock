from app.rag.chunker import chunk_sections
from app.rag.parser import ParsedReportSection


def test_chunker_keeps_a_normal_table_in_one_chunk() -> None:
    section = ParsedReportSection(
        section_title="II. 사업의 내용 > 1. 사업의 개요",
        content=("설명 문단입니다. " * 8) + "\n구분 | 2025 | 2024\n매출 | 100 | 90",
        has_table=True,
    )

    chunks = chunk_sections([section], chunk_size=100, overlap=20)

    assert len(chunks) == 2
    assert chunks[1].has_table is True
    assert chunks[1].content == "구분 | 2025 | 2024\n매출 | 100 | 90"


def test_chunker_repeats_header_when_a_table_is_large() -> None:
    header = "구분 | 2025"
    rows = [f"항목{i} | {'1' * 100}" for i in range(20)]
    section = ParsedReportSection(
        section_title="II. 사업의 내용",
        content="\n".join([header, *rows]),
        has_table=True,
    )

    chunks = chunk_sections([section])

    assert len(chunks) > 1
    assert all(chunk.content.startswith(header) for chunk in chunks)


def test_chunker_deduplicates_content_and_keeps_indexes_contiguous() -> None:
    sections = [
        ParsedReportSection("I. 회사의 개요", "반복 본문", False),
        ParsedReportSection("II. 사업의 내용", "반복 본문", False),
        ParsedReportSection("VII. 주주에 관한 사항", "다른 본문", False),
    ]

    chunks = chunk_sections(sections, chunk_size=100, overlap=0)

    assert [chunk.chunk_index for chunk in chunks] == [0, 1]
    assert [chunk.content for chunk in chunks] == ["반복 본문", "다른 본문"]
    assert chunks[0].section_title == "I. 회사의 개요"
