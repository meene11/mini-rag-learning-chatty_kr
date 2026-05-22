"""mini-RAG CLI 엔트리.

사용법:
  uv run python -m src.main index
  uv run python -m src.main ask "AI 채팅이 뭐야?"
  uv run python -m src.main eval
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

from src.generate import generate_answer
from src.ingest import chunk_by_chars, chunk_by_paragraphs, load_documents
from src.retrieve import Retriever

EVAL_QUESTIONS_PATH = Path("eval/questions.txt")
EVAL_RESULTS_PATH = Path("eval/results.csv")

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


def _word_overlap(text_a: str, text_b: str) -> float:
    """두 텍스트의 단어 집합 Jaccard 유사도 (0~1)."""
    set_a = set(text_a.split())
    set_b = set(text_b.split())
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def cmd_eval() -> None:
    """questions.txt의 각 질문을 두 전략에 던지고 CSV 저장 + 자동 비교 메트릭."""
    if not EVAL_QUESTIONS_PATH.exists():
        print(f"{EVAL_QUESTIONS_PATH} 가 없습니다.")
        sys.exit(1)

    questions = [
        q.strip()
        for q in EVAL_QUESTIONS_PATH.read_text(encoding="utf-8").splitlines()
        if q.strip()
    ]

    retriever = Retriever()
    rows: list[dict] = []

    for q in questions:
        print(f"\n=== 질문: {q} ===")
        per_q: dict[str, dict] = {}
        for label, collection in [
            ("char", COLLECTION_CHAR),
            ("para", COLLECTION_PARA),
        ]:
            chunks = retriever.search(collection, q, top_k=3)
            answer = generate_answer(q, chunks)
            top1_preview = chunks[0][:80].replace("\n", " ")
            avg_chunk_len = sum(len(c) for c in chunks) / len(chunks)
            print(f"\n--- [{label}] avg_chunk={avg_chunk_len:.0f}자, answer={len(answer)}자 ---")
            print(f"top1: {top1_preview}...")
            print(f"답변: {answer}")
            per_q[label] = {
                "question": q,
                "strategy": label,
                "top1_preview": top1_preview,
                "avg_chunk_len": int(avg_chunk_len),
                "answer": answer,
                "answer_len": len(answer),
            }
        # 두 답변 간 자동 비교
        overlap = _word_overlap(per_q["char"]["answer"], per_q["para"]["answer"])
        print(f"\n>> 두 답변의 단어 일치도 (Jaccard): {overlap:.2%}")
        for label in ["char", "para"]:
            per_q[label]["word_overlap_with_other"] = round(overlap, 3)
            rows.append(per_q[label])

    EVAL_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVAL_RESULTS_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp",
                "question",
                "strategy",
                "top1_preview",
                "avg_chunk_len",
                "answer_len",
                "word_overlap_with_other",
                "answer",
            ],
        )
        writer.writeheader()
        ts = datetime.now().isoformat(timespec="seconds")
        for r in rows:
            writer.writerow({"timestamp": ts, **r})

    print(f"\n[OK] {EVAL_RESULTS_PATH} 저장 완료 ({len(rows)}행)")


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
    elif mode == "eval":
        cmd_eval()
    else:
        print(f"알 수 없는 모드: {mode}")
        sys.exit(1)


if __name__ == "__main__":
    main()
