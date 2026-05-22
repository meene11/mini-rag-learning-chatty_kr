"""ingest 모듈 단위 테스트 — 청킹 함수의 정확성을 검증한다."""

from src.ingest import chunk_by_chars


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
