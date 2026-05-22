"""문서 인제스트(수집) + 청킹 전략."""


def chunk_by_chars(text: str, size: int = 500, overlap: int = 50) -> list[str]:
    """글자수 기반 청킹.

    text를 size 글자씩 자르되, 인접 청크 사이가 overlap 글자만큼 겹치도록 한다.
    빈 문자열은 빈 리스트 반환.
    """
    if not text:
        return []
    if len(text) <= size:
        return [text]

    chunks: list[str] = []
    step = size - overlap
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += step
    return chunks
