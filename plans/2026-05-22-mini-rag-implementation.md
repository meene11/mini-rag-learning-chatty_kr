# mini-RAG Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** chatty.kr 메인 + 기능 페이지 4~5개를 대상으로 한국어 RAG 미니 시스템을 구축하고, 두 청킹 전략(글자수 500/50, 문단 기반)을 정확도 측면에서 비교한다.

**Architecture:** 텍스트 인제스트 → 청킹(전략 A/B) → bge-m3 임베딩 → Chroma 컬렉션 2개 저장 → 질문 시 두 컬렉션 각각에서 top-3 검색 → 컨텍스트와 함께 Gemini Flash 4.6에 전달 → 답변 두 개를 나란히 출력하고 평가 점수를 CSV로 기록.

**Tech Stack:** Python 3.11, uv (패키지 매니저), sentence-transformers (BAAI/bge-m3), chromadb, google-genai SDK (`gemini-2.5-flash`, 무료 quota), pytest, python-dotenv.

---

## 🔒 Git 규칙 (사용자 글로벌 CLAUDE.md)

- **`git init`, `git add`, `git commit`, `git push`는 사용자가 명시적으로 명령하기 전엔 절대 실행 금지.**
- 이 plan의 각 "Commit" 단계는 *사용자가 직접 실행하거나, 사용자가 "커밋해줘"라고 말한 뒤에만 실행* 가능. 단계는 그대로 두되, 실행 시점에 반드시 확인.
- sandbox 자체가 아직 git 저장소 아님. git 도입을 원할 때만 Task 0의 git init 단계 진행.

## 실행 위치
모든 명령은 **`C:\Users\COM-MKUYO\sandbox\mini-rag\`** 디렉토리에서 PowerShell로 실행한다고 가정. 다른 위치에서 실행 시 절대 경로 사용.

---

## 파일 구조 (최종 상태)

```
C:\Users\COM-MKUYO\sandbox\mini-rag\
├── .venv\                              # uv가 생성, gitignore
├── .env                                # GOOGLE_API_KEY=..., gitignore
├── .env.example                        # 키 없는 템플릿, 공유 가능
├── .gitignore
├── pyproject.toml                      # uv 의존성
├── README.md                           # 사용법 + 회고
├── specs\
│   └── 2026-05-22-mini-rag-design.md   # 설계 문서 (기존)
├── plans\
│   └── 2026-05-22-mini-rag-implementation.md  # 이 문서
├── docs\                               # chatty.kr 원본 텍스트
│   ├── chatty_main.txt
│   ├── chatty_chat.txt
│   ├── chatty_search.txt
│   ├── chatty_doc.txt
│   └── chatty_translate.txt
├── chroma_data\                        # Chroma 자동 영구 저장, gitignore
├── src\
│   ├── __init__.py
│   ├── ingest.py
│   ├── retrieve.py
│   ├── generate.py
│   └── main.py
├── tests\
│   ├── __init__.py
│   └── test_ingest.py
└── eval\
    ├── questions.txt
    └── results.csv                     # 실행 시 자동 생성
```

각 파일 책임:
- `src/ingest.py`: 텍스트 로드 + 두 청킹 함수 (`chunk_by_chars`, `chunk_by_paragraphs`). 순수 함수. 외부 의존성 0.
- `src/retrieve.py`: bge-m3 모델 로딩, Chroma 클라이언트 관리, 두 컬렉션 인덱싱/검색 함수.
- `src/generate.py`: 컨텍스트 + 질문 → Gemini Flash → 답변 문자열.
- `src/main.py`: CLI 엔트리 (`index`, `ask`, `eval` 모드).
- `tests/test_ingest.py`: 청킹 함수 단위 테스트 (TDD 사이클 실제로 돌릴 곳).
- `eval/questions.txt`: 평가 질문 5~7개.
- `eval/results.csv`: 평가 실행 결과 누적.

---

## Task 0: 프로젝트 초기 셋업

**Files:**
- Create: `C:\Users\COM-MKUYO\sandbox\mini-rag\pyproject.toml`
- Create: `C:\Users\COM-MKUYO\sandbox\mini-rag\.gitignore`
- Create: `C:\Users\COM-MKUYO\sandbox\mini-rag\.env.example`
- Create: `C:\Users\COM-MKUYO\sandbox\mini-rag\.env`
- Create: 빈 `src\`, `tests\`, `docs\`, `eval\` 폴더와 `__init__.py`

- [ ] **Step 1: uv 설치 확인**

Run:
```powershell
uv --version
```
Expected: `uv 0.x.x` 형태의 버전 출력.

설치 안 돼 있다면:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

- [ ] **Step 2: 프로젝트 디렉토리에서 uv init**

Run:
```powershell
uv init --python 3.11 --no-readme --bare C:\Users\COM-MKUYO\sandbox\mini-rag
```
Expected: `pyproject.toml` 생성됨.

> `--bare`: src 폴더 자동 생성 안 함 (우리가 직접 구조 잡음). `--no-readme`: README 우리가 마지막에 회고로 작성.

- [ ] **Step 3: 의존성 추가**

Run:
```powershell
uv add google-genai chromadb sentence-transformers python-dotenv
uv add --dev pytest
```
Expected: `pyproject.toml`에 dependencies 섹션 추가, `.venv` 자동 생성, `uv.lock` 생성됨.

> sentence-transformers 첫 설치 시 PyTorch도 같이 깔려 1~2GB 다운로드. 시간 소요됨.

- [ ] **Step 4: 디렉토리 구조 생성**

Run:
```powershell
New-Item -ItemType Directory -Path "C:\Users\COM-MKUYO\sandbox\mini-rag\src","C:\Users\COM-MKUYO\sandbox\mini-rag\tests","C:\Users\COM-MKUYO\sandbox\mini-rag\docs","C:\Users\COM-MKUYO\sandbox\mini-rag\eval" -Force | Out-Null
New-Item -ItemType File -Path "C:\Users\COM-MKUYO\sandbox\mini-rag\src\__init__.py","C:\Users\COM-MKUYO\sandbox\mini-rag\tests\__init__.py" -Force | Out-Null
```
Expected: 4개 폴더 + 2개 빈 `__init__.py` 생성됨.

- [ ] **Step 5: `.gitignore` 작성**

Create `C:\Users\COM-MKUYO\sandbox\mini-rag\.gitignore`:
```
# Python
__pycache__/
*.py[cod]
*.pyc
.venv/
.pytest_cache/

# Env / secrets
.env

# Local data
chroma_data/

# IDE
.vscode/
.idea/
```

- [ ] **Step 6: `.env.example` 작성 (공유 가능 템플릿)**

Create `C:\Users\COM-MKUYO\sandbox\mini-rag\.env.example`:
```
# Google AI Studio에서 무료 발급: https://aistudio.google.com/apikey
GOOGLE_API_KEY=AIza-여기에-실제-키
```

- [ ] **Step 7: `.env` 작성 (실제 키)**

Create `C:\Users\COM-MKUYO\sandbox\mini-rag\.env`:
```
GOOGLE_API_KEY=여기에_실제_키_복붙
```

⚠️ 실제 키는 사용자가 직접 입력. `.gitignore`에 `.env`가 들어 있어 안전.

- [ ] **Step 8: 환경 동작 확인**

Run:
```powershell
uv run python -c "from google import genai; import chromadb, sentence_transformers; from dotenv import load_dotenv; print('OK')"
```
Expected: `OK` 출력. 에러 나면 의존성 재설치.

- [ ] **Step 9 (선택, 사용자 명시적 승인 시에만): git 초기화**

⚠️ **사용자가 "git 초기화해줘"라고 말한 경우에만 진행. 그렇지 않으면 SKIP.**

Run:
```powershell
git init
git checkout -b feat/mini-rag
git add .gitignore .env.example pyproject.toml uv.lock specs plans
git status
```
Expected: 새 브랜치 `feat/mini-rag`, staging 영역에 위 파일들 들어감. `.env`는 안 들어감 (gitignore 적용 확인).

⚠️ **commit은 별도 단계로, 사용자가 "커밋해줘"라고 한 뒤에만:**
```powershell
git commit -m "chore: initial project scaffold for mini-rag"
```

---

## Task 1: `chunk_by_chars` 함수 (TDD 사이클 1)

**Files:**
- Create: `C:\Users\COM-MKUYO\sandbox\mini-rag\tests\test_ingest.py`
- Create: `C:\Users\COM-MKUYO\sandbox\mini-rag\src\ingest.py`

**TDD 사이클:** Red → Green → Refactor.

- [ ] **Step 1: 실패하는 테스트 작성 (Red)**

Create `C:\Users\COM-MKUYO\sandbox\mini-rag\tests\test_ingest.py`:
```python
"""ingest 모듈 단위 테스트 — 청킹 함수의 정확성을 검증한다."""

from src.ingest import chunk_by_chars


def test_chunk_by_chars_short_text_returns_single_chunk():
    text = "안녕하세요. 짧은 텍스트입니다."
    chunks = chunk_by_chars(text, size=500, overlap=50)
    assert chunks == [text]


def test_chunk_by_chars_splits_when_over_size():
    text = "가" * 1100
    chunks = chunk_by_chars(text, size=500, overlap=50)
    # 1100자, size=500, overlap=50이면 (500) + (450부터 500자=950까지) + (900부터 끝)
    # 청크 3개여야 함
    assert len(chunks) == 3
    assert all(len(c) <= 500 for c in chunks)


def test_chunk_by_chars_overlap_preserves_context():
    # 각 청크 사이에 50자 중첩이 있어야 함
    text = "ABCDEFGHIJ" * 100  # 1000자, 'ABCDEFGHIJ' 100번 반복
    chunks = chunk_by_chars(text, size=500, overlap=50)
    # 두번째 청크의 시작 50자가 첫번째 청크의 끝 50자와 같아야 함
    assert chunks[0][-50:] == chunks[1][:50]


def test_chunk_by_chars_empty_text_returns_empty_list():
    assert chunk_by_chars("", size=500, overlap=50) == []
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

Run:
```powershell
uv run pytest tests/test_ingest.py -v
```
Expected: `ModuleNotFoundError: No module named 'src.ingest'` 또는 `ImportError: cannot import name 'chunk_by_chars'`. 4개 테스트 모두 ERROR/FAIL.

> 이게 정상. "구현이 없으니 테스트가 실패한다" — 이게 TDD의 **Red** 단계.

- [ ] **Step 3: 최소 구현 (Green)**

Create `C:\Users\COM-MKUYO\sandbox\mini-rag\src\ingest.py`:
```python
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
```

- [ ] **Step 4: 테스트 통과 확인 (Green)**

Run:
```powershell
uv run pytest tests/test_ingest.py -v
```
Expected: 4개 테스트 모두 PASSED.

실패 시: 출력 메시지를 보고 어느 케이스에서 빠졌는지 파악 → 구현 수정 → 다시 실행. **테스트를 고치지 말고 구현을 고침.**

- [ ] **Step 5: Refactor (지금은 생략 가능)**

코드가 이미 명확하므로 리팩토링 생략. 다음 함수로 넘어감.

- [ ] **Step 6: (사용자 승인 시) Commit**

```powershell
git add src/ingest.py tests/test_ingest.py
git commit -m "feat(ingest): add chunk_by_chars with TDD"
```

---

## Task 2: `chunk_by_paragraphs` 함수 (TDD 사이클 2)

**Files:**
- Modify: `C:\Users\COM-MKUYO\sandbox\mini-rag\tests\test_ingest.py` (테스트 추가)
- Modify: `C:\Users\COM-MKUYO\sandbox\mini-rag\src\ingest.py` (함수 추가)

- [ ] **Step 1: 실패하는 테스트 추가**

Edit `tests/test_ingest.py`, 파일 맨 위 import 줄 수정:
```python
from src.ingest import chunk_by_chars, chunk_by_paragraphs
```

파일 맨 아래에 다음 테스트 추가:
```python
def test_chunk_by_paragraphs_splits_on_blank_lines():
    text = "첫 번째 문단입니다. 충분히 길어요. " * 5 + "\n\n" + "두 번째 문단도 충분히 길어요. " * 5
    chunks = chunk_by_paragraphs(text)
    assert len(chunks) == 2


def test_chunk_by_paragraphs_merges_short_paragraphs():
    # 짧은 문단(<100자) 두 개는 하나로 합쳐져야 함
    text = "짧은 문단1.\n\n짧은 문단2.\n\n" + "긴 문단입니다. " * 20
    chunks = chunk_by_paragraphs(text)
    # 짧은 두 개가 병합되고, 긴 문단 하나 = 청크 2개
    assert len(chunks) == 2
    assert "짧은 문단1" in chunks[0]
    assert "짧은 문단2" in chunks[0]


def test_chunk_by_paragraphs_splits_oversize_paragraph():
    # 1000자 초과 문단은 size=500, overlap=50으로 재분할
    oversize = "가" * 1500
    chunks = chunk_by_paragraphs(oversize)
    assert len(chunks) >= 2
    assert all(len(c) <= 500 for c in chunks)


def test_chunk_by_paragraphs_empty_text_returns_empty_list():
    assert chunk_by_paragraphs("") == []
```

- [ ] **Step 2: 테스트 실행해서 실패 확인**

Run:
```powershell
uv run pytest tests/test_ingest.py -v
```
Expected: 새 테스트 4개 ERROR (`cannot import name 'chunk_by_paragraphs'`). 기존 4개는 PASS.

- [ ] **Step 3: `chunk_by_paragraphs` 구현**

Edit `src/ingest.py`, 파일 맨 아래에 추가:
```python
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

    # 짧은 문단 병합
    merged: list[str] = []
    buffer = ""
    for p in raw_paragraphs:
        if buffer:
            buffer = buffer + "\n\n" + p
        else:
            buffer = p
        if len(buffer) >= min_chars:
            merged.append(buffer)
            buffer = ""
    if buffer:
        if merged:
            merged[-1] = merged[-1] + "\n\n" + buffer
        else:
            merged.append(buffer)

    # 너무 큰 문단 재분할
    result: list[str] = []
    for p in merged:
        if len(p) > max_chars:
            result.extend(chunk_by_chars(p, size=500, overlap=50))
        else:
            result.append(p)
    return result
```

- [ ] **Step 4: 테스트 통과 확인**

Run:
```powershell
uv run pytest tests/test_ingest.py -v
```
Expected: 8개 모두 PASSED.

- [ ] **Step 5: (사용자 승인 시) Commit**

```powershell
git add src/ingest.py tests/test_ingest.py
git commit -m "feat(ingest): add chunk_by_paragraphs with TDD"
```

---

## Task 3: `load_documents` 헬퍼 + chatty.kr 텍스트 수집

**Files:**
- Modify: `src/ingest.py` (load_documents 함수 추가)
- Create: `docs/chatty_main.txt`
- Create: `docs/chatty_chat.txt`
- Create: `docs/chatty_search.txt`
- Create: `docs/chatty_doc.txt`
- Create: `docs/chatty_translate.txt`

- [ ] **Step 1: `load_documents` 헬퍼 추가**

Edit `src/ingest.py`, 파일 맨 위에 추가:
```python
from pathlib import Path
```

파일 맨 아래에 추가:
```python
def load_documents(docs_dir: Path | str) -> dict[str, str]:
    """docs_dir 아래 모든 .txt 파일을 읽어 {filename: content} 반환."""
    docs_dir = Path(docs_dir)
    return {
        f.name: f.read_text(encoding="utf-8")
        for f in sorted(docs_dir.glob("*.txt"))
    }
```

- [ ] **Step 2: chatty.kr 메인 페이지 텍스트 수집**

Claude Code의 WebFetch를 통해 사용자/사용자 도움으로 chatty.kr 메인 페이지 텍스트를 가져와 `docs/chatty_main.txt`에 저장. 한글 텍스트만 (메뉴/푸터 제외 본문 위주). 약 500~1500자 권장.

- [ ] **Step 3: AI 채팅 소개 페이지 수집 → `docs/chatty_chat.txt`**

같은 방식으로 AI 채팅 소개 섹션 텍스트 저장.

- [ ] **Step 4: AI 검색 소개 → `docs/chatty_search.txt`**

- [ ] **Step 5: AI 문서 소개 → `docs/chatty_doc.txt`**

- [ ] **Step 6: AI 번역 소개 → `docs/chatty_translate.txt`**

- [ ] **Step 7: 로드 동작 확인**

Run:
```powershell
uv run python -c "from src.ingest import load_documents; d = load_documents('docs'); print({k: len(v) for k, v in d.items()})"
```
Expected: 5개 파일명과 각 길이가 dict로 출력됨. 모두 0이 아니어야 함.

- [ ] **Step 8: (사용자 승인 시) Commit**

```powershell
git add src/ingest.py docs/
git commit -m "feat(ingest): add load_documents and chatty.kr source texts"
```

---

## Task 4: `retrieve.py` — 임베딩 + Chroma 인덱싱

**Files:**
- Create: `C:\Users\COM-MKUYO\sandbox\mini-rag\src\retrieve.py`

이 모듈은 외부 모델·DB를 다루므로 단위 테스트 생략 (학습 범위 밖). 동작은 main.py 통해 수동 확인.

- [ ] **Step 1: `retrieve.py` 작성**

Create `C:\Users\COM-MKUYO\sandbox\mini-rag\src\retrieve.py`:
```python
"""bge-m3 임베딩 + Chroma 벡터DB 관리."""

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_DIR = Path("chroma_data")
EMBEDDING_MODEL_NAME = "BAAI/bge-m3"


class Retriever:
    """청크를 임베딩해 Chroma 컬렉션에 저장하고 검색하는 클래스."""

    def __init__(self) -> None:
        # 첫 호출 시 bge-m3 모델을 로컬에 다운로드 (~2GB).
        self.model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    def index(self, collection_name: str, chunks: list[str]) -> None:
        """주어진 청크들을 새 컬렉션에 임베딩 후 저장. 이미 있으면 덮어씀."""
        # 기존 컬렉션 있으면 삭제 (재인덱싱 깔끔하게)
        existing = [c.name for c in self.client.list_collections()]
        if collection_name in existing:
            self.client.delete_collection(collection_name)

        collection = self.client.create_collection(name=collection_name)
        embeddings = self.model.encode(chunks, show_progress_bar=True).tolist()
        ids = [f"{collection_name}_{i}" for i in range(len(chunks))]
        collection.add(ids=ids, embeddings=embeddings, documents=chunks)

    def search(
        self,
        collection_name: str,
        query: str,
        top_k: int = 3,
    ) -> list[str]:
        """query와 가장 가까운 청크 top_k개의 본문을 반환."""
        collection = self.client.get_collection(name=collection_name)
        query_emb = self.model.encode([query]).tolist()
        result = collection.query(query_embeddings=query_emb, n_results=top_k)
        return result["documents"][0]
```

- [ ] **Step 2: import 동작 확인**

Run:
```powershell
uv run python -c "from src.retrieve import Retriever; print('import OK')"
```
Expected: `import OK` 출력. 다른 출력 없음.

> 실제 `Retriever()` 인스턴스화는 모델 다운로드(~2GB)가 일어나므로 Task 6에서 진행.

- [ ] **Step 3: (사용자 승인 시) Commit**

```powershell
git add src/retrieve.py
git commit -m "feat(retrieve): add Retriever with bge-m3 and Chroma"
```

---

## Task 5: `generate.py` — Gemini Flash 호출 (Google AI Studio 무료 API)

**Files:**
- Create: `C:\Users\COM-MKUYO\sandbox\mini-rag\src\generate.py`

- [ ] **Step 1: `generate.py` 작성**

Create `C:\Users\COM-MKUYO\sandbox\mini-rag\src\generate.py`:
```python
"""Google Gemini Flash을 사용해 컨텍스트 기반 답변을 생성한다."""

import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL = "gemini-2.5-flash"
MAX_OUTPUT_TOKENS = 1024


def _build_system_prompt(context_chunks: list[str]) -> str:
    joined = "\n\n---\n\n".join(
        f"[참고 {i + 1}]\n{c}" for i, c in enumerate(context_chunks)
    )
    return (
        "당신은 chatty.kr 서비스에 대한 질문에 답하는 한국어 비서입니다.\n"
        "아래 [참고] 자료만 사용해 답하세요. 자료에 없는 내용은 "
        "'자료에 없습니다'라고 답하고 추측하지 마세요.\n\n"
        f"{joined}"
    )


def generate_answer(question: str, context_chunks: list[str]) -> str:
    """질문 + 검색된 청크 → Gemini Flash 답변."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            ".env에 GOOGLE_API_KEY가 없습니다. .env.example을 참고해 작성하세요. "
            "키 발급: https://aistudio.google.com/apikey"
        )
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL,
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=_build_system_prompt(context_chunks),
            max_output_tokens=MAX_OUTPUT_TOKENS,
        ),
    )
    return response.text
```

- [ ] **Step 2: 시스템 프롬프트 단위 확인 (API 호출 없음)**

Run:
```powershell
uv run python -c "from src.generate import _build_system_prompt; print(_build_system_prompt(['예시 청크 1', '예시 청크 2'])[:200])"
```
Expected: "당신은 chatty.kr…" 으로 시작하는 프롬프트가 출력됨.

- [ ] **Step 3: (사용자 승인 시) Commit**

```powershell
git add src/generate.py
git commit -m "feat(generate): add Gemini Flash answer generation via google-genai"
```

---

## Task 6: `main.py` — CLI 통합 (index / ask)

**Files:**
- Create: `C:\Users\COM-MKUYO\sandbox\mini-rag\src\main.py`

`main.py`는 3가지 모드 — `index`, `ask`, `eval`. 이 Task에선 처음 2개. `eval`은 Task 7.

- [ ] **Step 1: `main.py` 1차 작성 (index + ask)**

Create `C:\Users\COM-MKUYO\sandbox\mini-rag\src\main.py`:
```python
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
    print("✅ 인덱싱 완료.")


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
```

- [ ] **Step 2: 인덱싱 실행 (모델 다운로드 포함, ~5~10분 소요 가능)**

Run:
```powershell
uv run python -m src.main index
```
Expected:
- bge-m3 모델 다운로드 진행률 표시 (첫 실행만).
- "글자수 전략: N개 청크", "문단 전략: M개 청크" 출력.
- "✅ 인덱싱 완료." 끝.

`chroma_data\` 폴더가 생성됨.

- [ ] **Step 3: 질문 동작 확인**

Run:
```powershell
uv run python -m src.main ask "AI 채팅 기능의 핵심 기술은 무엇인가요?"
```
Expected:
- [A] 글자수 청킹의 검색 청크 3개 + 답변
- [B] 문단 청킹의 검색 청크 3개 + 답변
- 두 답변이 미묘하게 다를 수 있음 (정상).

- [ ] **Step 4: (사용자 승인 시) Commit**

```powershell
git add src/main.py
git commit -m "feat(main): add CLI with index and ask modes"
```

---

## Task 7: 평가 — `eval` 모드 + CSV 기록

**Files:**
- Create: `C:\Users\COM-MKUYO\sandbox\mini-rag\eval\questions.txt`
- Modify: `C:\Users\COM-MKUYO\sandbox\mini-rag\src\main.py` (cmd_eval 추가)

- [ ] **Step 1: 평가 질문 5개 작성**

Create `C:\Users\COM-MKUYO\sandbox\mini-rag\eval\questions.txt`:
```
AI 채팅 기능의 핵심 기술은 무엇인가요?
번역 기능은 몇 개 언어를 지원하나요?
AI 문서 기능에서 한 번에 몇 개 파일을 요약할 수 있나요?
chatty.kr은 어떤 종류의 고객이 사용하나요?
RAG는 이 서비스에서 어떻게 활용되나요?
```

- [ ] **Step 2: `main.py`에 `cmd_eval` 추가**

Edit `C:\Users\COM-MKUYO\sandbox\mini-rag\src\main.py`, import 영역에 추가:
```python
import csv
from datetime import datetime
from pathlib import Path
```

`cmd_ask` 함수 아래에 추가:
```python
EVAL_QUESTIONS_PATH = Path("eval/questions.txt")
EVAL_RESULTS_PATH = Path("eval/results.csv")


def cmd_eval() -> None:
    """questions.txt의 각 질문을 두 전략에 던지고 점수 입력 후 CSV 저장."""
    if not EVAL_QUESTIONS_PATH.exists():
        print(f"{EVAL_QUESTIONS_PATH} 가 없습니다.")
        sys.exit(1)

    questions = [
        q.strip()
        for q in EVAL_QUESTIONS_PATH.read_text(encoding="utf-8").splitlines()
        if q.strip()
    ]

    retriever = Retriever()
    new_file = not EVAL_RESULTS_PATH.exists()
    with EVAL_RESULTS_PATH.open("a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(
                ["timestamp", "question", "strategy", "retrieved_top1_preview", "answer", "score"]
            )

        for q in questions:
            print(f"\n=== 질문: {q} ===")
            for label, collection in [
                ("char", COLLECTION_CHAR),
                ("para", COLLECTION_PARA),
            ]:
                chunks = retriever.search(collection, q, top_k=3)
                answer = generate_answer(q, chunks)
                top1_preview = chunks[0][:80].replace("\n", " ")
                print(f"\n--- [{label}] ---")
                print(f"top1: {top1_preview}...")
                print(f"답변: {answer}")
                score = input(f"[{label}] 1~5점 점수: ").strip()
                writer.writerow(
                    [
                        datetime.now().isoformat(timespec="seconds"),
                        q,
                        label,
                        top1_preview,
                        answer,
                        score,
                    ]
                )
    print(f"\n✅ {EVAL_RESULTS_PATH} 에 결과 저장 완료.")
```

`main()` 함수의 if/elif 블록에 `eval` 분기 추가 (`elif mode == "ask":` 다음):
```python
    elif mode == "eval":
        cmd_eval()
```

- [ ] **Step 3: 평가 실행**

Run:
```powershell
uv run python -m src.main eval
```
Expected:
- 5개 질문 × 2전략 = 10번 답변 출력.
- 각 답변 후 "1~5점 점수:" 프롬프트 → 입력 (예: 4 엔터).
- 마지막에 "✅ ... 결과 저장 완료" 출력.

`eval/results.csv` 열어서 10행 + 헤더 1행 확인.

- [ ] **Step 4: 결과 분석 (수동, 5분)**

`eval/results.csv`를 Excel/Notepad로 열어 봄. 다음 질문을 자신에게:
- 평균 점수가 더 높은 전략은? (`char` vs `para`)
- 점수가 명확히 갈리는 질문은 어떤 종류?
- 검색된 top1 청크가 두 전략에서 얼마나 달랐는지?

이 관찰을 다음 Task 8의 회고에 적음.

- [ ] **Step 5: (사용자 승인 시) Commit**

```powershell
git add eval/questions.txt eval/results.csv src/main.py
git commit -m "feat(eval): add eval mode comparing two chunking strategies"
```

---

## Task 8: 회고 — README 작성

**Files:**
- Create: `C:\Users\COM-MKUYO\sandbox\mini-rag\README.md`

- [ ] **Step 1: README 작성**

Create `C:\Users\COM-MKUYO\sandbox\mini-rag\README.md`:
```markdown
# mini-RAG

chatty.kr 서비스 문서에 대한 한국어 RAG 미니 시스템. 두 청킹 전략(글자수 vs 문단)의 정확도 비교 학습 프로젝트.

작성: 2026-05-22 / 작성자: AI 엔지니어 입사 첫주 학습 프로젝트.

## 사용법

```powershell
# 1. 의존성 설치 (최초 1회)
uv sync

# 2. .env 작성 (.env.example 참고해 GOOGLE_API_KEY 입력)

# 3. 인덱싱 (첫 실행 시 bge-m3 모델 ~2GB 다운로드)
uv run python -m src.main index

# 4. 단일 질문
uv run python -m src.main ask "AI 채팅 기능의 핵심 기술은?"

# 5. 평가 (questions.txt 기준 5문항 × 2전략)
uv run python -m src.main eval
# 결과는 eval/results.csv 에 누적
```

## 구조

| 모듈 | 책임 |
|---|---|
| `src/ingest.py` | 텍스트 로드 + 두 청킹 함수 (TDD로 작성) |
| `src/retrieve.py` | bge-m3 + Chroma 인덱싱/검색 |
| `src/generate.py` | Google Gemini Flash 답변 생성 |
| `src/main.py` | CLI (index / ask / eval) |

## 회고 (작업 완료 후 직접 작성)

### 잘 된 점
- (예시) TDD 사이클을 청킹 함수에서 실제로 돌려봄. Red→Green 흐름 체감.
- (예시) 두 청킹 전략 결과가 [질문 X]에서 명확히 달랐고, 이유는…

### 막힌 점
- (예시) bge-m3 다운로드가 예상보다 오래 걸림 → 다음엔 미리 받아둘 것.
- (예시) Chroma 컬렉션 중복 생성 에러 → delete_collection 패턴 익힘.

### 사수에게 물어볼 것
- (예시) 회사 RAG는 임베딩 모델로 무엇을 쓰는지?
- (예시) 청킹 전략은 어떻게 결정했는지? 평가 메트릭은?

### 다음에 해볼 것
- TDD 본격 사이클 학습 (작은 문제 5회 반복).
- 이 RAG를 MCP 서버로 감싸기.
- 청킹 전략 추가 (의미 기반 / 문장 기반).
```

- [ ] **Step 2: 회고 섹션 채우기 (5~10분)**

위 README의 "(예시)" 부분을 본인 경험으로 교체. 솔직하게.

- [ ] **Step 3: (사용자 승인 시) Final Commit**

```powershell
git add README.md
git commit -m "docs: add README with usage and retrospective"
```

---

## Self-Review 결과

- ✅ **Spec coverage**: 설계 문서의 모든 섹션이 task에 매핑됨.
  - 기술 스택 → Task 0
  - 청킹 전략 A/B → Task 1, 2 (TDD)
  - 문서 수집 → Task 3
  - 임베딩 + 벡터DB → Task 4
  - 생성 → Task 5
  - CLI → Task 6
  - 평가 → Task 7
  - 회고 → Task 8
- ✅ **Placeholder scan**: TBD/TODO 없음. 모든 코드 블록 완성.
- ✅ **Type consistency**: `chunk_by_chars`, `chunk_by_paragraphs`, `Retriever.index`, `Retriever.search`, `generate_answer` 시그니처가 모든 task에서 일관됨.

---

## 다음 단계 (사용자 승인 대기)

이 plan을 어떻게 실행할까요?

- **옵션 1. Subagent-Driven (skill 권장)** — Task마다 별도 subagent를 띄우고 task 사이에 리뷰. 빠른 반복, 한 단계 끝날 때마다 사용자가 확인 가능.
- **옵션 2. Inline Execution** — 이 세션에서 그대로 `executing-plans` skill로 batch 실행. 체크포인트마다 확인.
- **옵션 3. Manual** — 사용자가 직접 plan을 읽으며 명령어를 PowerShell에 복붙. 가장 학습 효과 큼 (학습자 추천).
