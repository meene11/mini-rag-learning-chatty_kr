"""ingest 모듈 단위 테스트 — 청킹 함수의 정확성을 검증한다."""

from src.ingest import chunk_by_chars, chunk_by_paragraphs


def test_chunk_by_chars_short_text_returns_single_chunk():
    text = "안녕하세요. 짧은 텍스트입니다."
    chunks = chunk_by_chars(text, size=500, overlap=50)
    assert chunks == [text]


def test_chunk_by_chars_splits_when_over_size():
    text = "가" * 1100
    chunks = chunk_by_chars(text, size=500, overlap=50)
    assert len(chunks) == 3
    assert all(len(c) <= 500 for c in chunks)


def test_chunk_by_chars_overlap_preserves_context():
    text = "ABCDEFGHIJ" * 100
    chunks = chunk_by_chars(text, size=500, overlap=50)
    assert chunks[0][-50:] == chunks[1][:50]


def test_chunk_by_chars_empty_text_returns_empty_list():
    assert chunk_by_chars("", size=500, overlap=50) == []


def test_chunk_by_paragraphs_splits_on_blank_lines():
    # 각 문단이 min_chars(100자) 이상이 되도록 충분히 반복
    text = "첫 번째 문단입니다. 충분히 길어요. " * 10 + "\n\n" + "두 번째 문단도 충분히 길어요. " * 10
    chunks = chunk_by_paragraphs(text)
    assert len(chunks) == 2


def test_chunk_by_paragraphs_merges_short_paragraphs():
    text = "짧은 문단1.\n\n짧은 문단2.\n\n" + "긴 문단입니다. " * 20
    chunks = chunk_by_paragraphs(text)
    assert len(chunks) == 2
    assert "짧은 문단1" in chunks[0]
    assert "짧은 문단2" in chunks[0]


def test_chunk_by_paragraphs_splits_oversize_paragraph():
    oversize = "가" * 1500
    chunks = chunk_by_paragraphs(oversize)
    assert len(chunks) >= 2
    assert all(len(c) <= 500 for c in chunks)


def test_chunk_by_paragraphs_empty_text_returns_empty_list():
    assert chunk_by_paragraphs("") == []
