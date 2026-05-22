"""문서 인제스트(수집) + 청킹 전략."""

from pathlib import Path


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


def chunk_by_paragraphs(
    text: str,
    min_chars: int = 100,
    max_chars: int = 1000,
) -> list[str]:
    """문단(빈 줄 기준) 기반 청킹.

    빈 줄로 자른 뒤:
    - min_chars 미만 문단은 다음 문단에 흡수.
    - max_chars 초과 문단은 chunk_by_chars(size=500, overlap=50)로 재분할.
    """
    if not text:
        return []

    raw_paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    merged: list[str] = []
    buffer = ""
    for p in raw_paragraphs:
        if len(p) >= min_chars:
            # 단독으로 충분히 긴 문단 → 버퍼 내려놓고 따로 추가
            if buffer:
                merged.append(buffer)
                buffer = ""
            merged.append(p)
        else:
            # 짧은 문단은 버퍼에 누적, 누적량이 min_chars 넘으면 flush
            buffer = buffer + "\n\n" + p if buffer else p
            if len(buffer) >= min_chars:
                merged.append(buffer)
                buffer = ""
    if buffer:
        if merged:
            merged[-1] = merged[-1] + "\n\n" + buffer
        else:
            merged.append(buffer)

    result: list[str] = []
    for p in merged:
        if len(p) > max_chars:
            result.extend(chunk_by_chars(p, size=500, overlap=50))
        else:
            result.append(p)
    return result


def load_documents(docs_dir: Path | str) -> dict[str, str]:
    """docs_dir 아래 모든 .txt 파일을 읽어 {filename: content} 반환."""
    docs_dir = Path(docs_dir)
    return {
        f.name: f.read_text(encoding="utf-8")
        for f in sorted(docs_dir.glob("*.txt"))
    }
