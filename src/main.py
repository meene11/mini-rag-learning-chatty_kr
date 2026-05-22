"""mini-RAG CLI 엔트리.

사용법:
  uv run python -m src.main index
  uv run python -m src.main ask "AI 채팅이 뭐야?"
  uv run python -m src.main eval         # Task 7에서 추가
"""

import sys

from src.generate import generate_answer
from src.ingest import chunk_by_chars, chunk_by_paragraphs, load_documents
from src.retrieve import Retriever

COLLECTION_CHAR = "rag_char"
COLLECTION_PARA = "rag_para"


def cmd_index() -> None:
    """docs/ 아래 모든 .txt를 읽어 두 청킹 전략으로 인덱싱."""
    print("[1/3] 문서 로딩...")
    documents = load_documents("docs")
    if not documents:
        print("docs/ 폴더에 .txt 파일이 없습니다.")
        sys.exit(1)
    print(f"  - {len(documents)}개 문서 로드: {list(documents.keys())}")

    all_text = "\n\n".join(documents.values())

    print("[2/3] 청킹 (글자수 / 문단)...")
    char_chunks = chunk_by_chars(all_text, size=500, overlap=50)
    para_chunks = chunk_by_paragraphs(all_text)
    print(f"  - 글자수 전략: {len(char_chunks)}개 청크")
    print(f"  - 문단 전략:   {len(para_chunks)}개 청크")

    print("[3/3] bge-m3 임베딩 + Chroma 저장 (첫 실행 시 모델 다운로드 ~2GB)...")
    retriever = Retriever()
    retriever.index(COLLECTION_CHAR, char_chunks)
    retriever.index(COLLECTION_PARA, para_chunks)
    print("[OK] 인덱싱 완료.")


def cmd_ask(question: str) -> None:
    """질문을 두 컬렉션에 던지고 답변 2개를 나란히 출력."""
    retriever = Retriever()

    print(f"\n질문: {question}\n")

    for label, collection in [
        ("[A] 글자수 청킹", COLLECTION_CHAR),
        ("[B] 문단 청킹", COLLECTION_PARA),
    ]:
        chunks = retriever.search(collection, question, top_k=3)
        answer = generate_answer(question, chunks)
        print(f"=== {label} ===")
        print("검색된 청크 (앞 100자):")
        for i, c in enumerate(chunks, 1):
            print(f"  {i}. {c[:100].replace(chr(10), ' ')}...")
        print(f"\n답변:\n{answer}\n")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    mode = sys.argv[1]
    if mode == "index":
        cmd_index()
    elif mode == "ask":
        if len(sys.argv) < 3:
            print('사용법: uv run python -m src.main ask "질문 내용"')
            sys.exit(1)
        cmd_ask(" ".join(sys.argv[2:]))
    else:
        print(f"알 수 없는 모드: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
