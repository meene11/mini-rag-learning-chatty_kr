# mini-RAG 설계 문서

- 작성일: 2026-05-22
- 작성자: 사용자(amydreamsu@gmail.com) + Claude
- 위치: `C:\Users\COM-MKUYO\sandbox\mini-rag\`
- 상태: 사용자 1차 승인 완료 (구현 계획 단계 진입 전 최종 검토 대기)

---

## 1. 목표

AI 엔지니어 **입사 첫주동안의 학습 프로젝트**.

1순위: **RAG(Retrieval-Augmented Generation, 검색증강생성) 개념을 손으로 한 번 만들어보며 체득**.
2순위: **TDD(Test-Driven Development) 사이클 1회 맛보기**.
3순위: **두 청킹 전략의 정확도 비교 — "RAG 평가(evaluation)" 영역 체험**.

성공 기준:
- 입사 첫주동안 동작하는 mini-RAG 1개 구축.
- 같은 질문에 대해 두 청킹 전략의 검색·답변 결과를 나란히 비교할 수 있는 표 1개 생산.
- 핵심 개념(RAG, 임베딩, 벡터DB, 청킹, TDD)이 머릿속에서 명확히 분리되는 상태.

비-목표(YAGNI):
- 자동 평가 메트릭(BLEU/ROUGE 등) 구현 — 사람 평가로 충분.
- 본격 CLI 도구화, 설정 파일, 로깅 풀세트.
- MCP 서버 변환 — 별도 세션.

## 2. 기술 스택

| 역할 | 선택 | 이유 |
|---|---|---|
| 패키지 매니저 | `uv` | 글로벌 CLAUDE.md 권장. 빠르고 단순. |
| 임베딩 모델 | `BAAI/bge-m3` (sentence-transformers로 로컬) | 다국어 강함, 한국어 품질 ★. |
| 벡터DB | `Chroma` (로컬 영구) | 사용 쉬움, 자동 디스크 저장, 메타데이터 지원. |
| 생성 모델 | `claude-sonnet-4-6` | 일반 작업 가성비. 글로벌 CLAUDE.md 모델 정책. |
| 테스트 | `pytest` | TDD 맛보기. |
| HTTP/문서 수집 | Claude Code의 WebFetch (수집은 사람이 직접) | 외부 라이브러리 추가 부담 줄이기. |

## 3. 데이터 흐름

```
[1회 셋업 — 사람이 수동]
chatty.kr 5페이지 → WebFetch로 텍스트 추출 → docs/*.txt 저장

[2번 인덱싱 — 청킹 전략 A, B 각각]
docs/*.txt → 청킹(전략 A: 글자수) → bge-m3 임베딩 → Chroma 컬렉션 "rag_char"
docs/*.txt → 청킹(전략 B: 문단)   → bge-m3 임베딩 → Chroma 컬렉션 "rag_para"

[질문 처리]
질문 → bge-m3 임베딩 → 각 컬렉션에서 top-3 청크 검색 → Claude Sonnet에 컨텍스트 → 답변
같은 질문을 두 컬렉션에 던져 답변 2개 나란히 출력
```

## 4. 파일/모듈 구조

```
C:\Users\COM-MKUYO\sandbox\mini-rag\
├── .venv\                  # uv가 생성 (gitignore)
├── .env                    # ANTHROPIC_API_KEY (gitignore)
├── .gitignore
├── pyproject.toml          # uv 의존성 관리
├── README.md               # 사용법 + 회고 (마지막에 작성)
├── specs\
│   └── 2026-05-22-mini-rag-design.md   # 이 문서
├── docs\                   # 원본 chatty.kr 텍스트
│   ├── chatty_main.txt
│   ├── chatty_chat.txt
│   ├── chatty_search.txt
│   ├── chatty_doc.txt
│   └── chatty_translate.txt
├── chroma_data\            # Chroma 자동 영구 저장 (gitignore)
├── src\
│   ├── __init__.py
│   ├── ingest.py           # 문서 로드 + 두 청킹 전략 함수
│   ├── retrieve.py         # bge-m3 임베딩 + Chroma 컬렉션 관리
│   ├── generate.py         # Claude Sonnet 호출
│   └── main.py             # CLI 진입점, 두 전략 비교 실행
├── tests\
│   └── test_ingest.py      # 청킹 함수 pytest (TDD 맛보기)
└── eval\
    ├── questions.txt       # 평가용 질문 5~7개
    └── results.csv         # 두 전략 결과 + 사람 점수
```

### 모듈 책임

- `ingest.py`: 텍스트 파일 로드, 청킹 전략 2개 (`chunk_by_chars`, `chunk_by_paragraphs`). 외부 의존성 없음. **테스트 적용 대상**.
- `retrieve.py`: sentence-transformers로 bge-m3 로드, Chroma 클라이언트 관리, 두 컬렉션(`rag_char`, `rag_para`)에 청크 저장 및 검색.
- `generate.py`: Anthropic SDK로 Claude Sonnet 호출. 검색된 청크들을 시스템 프롬프트에 컨텍스트로 삽입.
- `main.py`: 인덱싱 모드(`python -m src.main index`), 질문 모드(`python -m src.main ask "..."`), 평가 모드(`python -m src.main eval`).

## 5. 청킹 전략 (비교 대상)

### 전략 A — 글자수 기반 (`chunk_by_chars`)
- 입력: 긴 문자열 1개
- 파라미터: `size=500`, `overlap=50`
- 동작: 500자씩 자르되, 인접 청크 사이 50자가 겹치도록. 마지막 청크가 100자 미만이면 직전 청크에 흡수.

### 전략 B — 문단 기반 (`chunk_by_paragraphs`)
- 입력: 긴 문자열 1개
- 동작: 빈 줄(`\n\n`) 기준으로 분할. 100자 미만 문단은 다음 문단과 병합. 1000자 초과 문단은 전략 A와 같은 파라미터(`size=500, overlap=50`)로 재분할.

두 전략 모두 출력은 `list[str]`. 인터페이스 동일 → 비교 용이.

## 6. 평가 방법

`eval/questions.txt`에 chatty.kr 관련 자연어 질문 5~7개:
- "AI 채팅의 핵심 기술이 뭐야?"
- "번역 기능은 몇 개 언어를 지원해?"
- "AI 문서 기능에서 한 번에 몇 개 파일을 요약할 수 있어?"
- "RAG가 이 서비스에선 어떻게 쓰여?"
- "어떤 기관·기업이 이 서비스를 이용해?"

`python -m src.main eval`를 실행하면:
1. 각 질문을 두 컬렉션에 던져 검색된 청크 + 최종 답변 출력.
2. 콘솔에서 사람이 5점 척도 점수 입력.
3. `eval/results.csv`에 한 줄씩 저장: `question, strategy, retrieved_snippet, answer, score`.

자동 메트릭은 도입하지 않음 — 학습 목적엔 사람 평가가 더 직관적.

## 7. TDD 적용 범위

`ingest.py`의 청킹 함수에만 적용. 외부 의존성 없고 입출력이 명확해 TDD 사이클이 자연스럽다.

`tests/test_ingest.py`에 2~3개 테스트:
- `test_chunk_by_chars_basic`: 1100자 텍스트 → size=500, overlap=50 → 청크 개수 검증.
- `test_chunk_by_chars_overlap`: 인접 청크 간 끝-시작 50자가 일치하는지 검증.
- `test_chunk_by_paragraphs_short_merge`: 짧은 문단 2개가 하나로 병합되는지 검증.

사이클: Red(실패하는 테스트 작성) → Green(통과만 시키는 최소 구현) → Refactor(다듬기).

다른 모듈(retrieve, generate)은 외부 모델·API 호출이라 단위 테스트 가성비가 낮음 → 오늘은 제외.

## 8. 에러 처리 (의도적으로 최소)

학습용이므로 방어 코딩 남발 금지:
- `.env` 미로드 / `ANTHROPIC_API_KEY` 부재 → 시작 시점에 명확한 메시지로 raise.
- 청킹 입력이 빈 문자열 → 빈 리스트 반환.
- 그 외 예외는 그대로 raise. try/except로 묻지 않음.

## 9. 보안

- `.env`에 `ANTHROPIC_API_KEY` 저장. 코드에 하드코딩 금지.
- `.gitignore` 1차 작성 시점에 다음 포함:
  - `.env`
  - `.venv/`
  - `chroma_data/`
  - `__pycache__/`
  - `*.pyc`
- 글로벌 CLAUDE.md "Git 작업 규칙": **commit·push는 사용자가 명시적으로 지시하기 전엔 절대 단독 실행 금지**. 본 설계 문서도 자동 commit 하지 않음. git 초기화 자체도 사용자가 원할 때 진행.

## 10. 시간 계획 (한 세션 ~3.5h 기준, 첫주 안에 나눠서 진행)

| 시간 | 단계 | 산출물 |
|---|---|---|
| 00:00–00:25 | 환경 셋업: `uv venv`, 의존성 설치, `.env` 작성, `.gitignore` 작성 | 동작하는 venv |
| 00:25–00:45 | `ingest.py` + `tests/test_ingest.py` — TDD 사이클 1회 (청킹 함수) | 청킹 함수 + 통과하는 테스트 |
| 00:45–01:30 | `retrieve.py`: bge-m3 다운로드, Chroma 두 컬렉션에 저장 | 인덱싱 완료 |
| 01:30–02:10 | `generate.py` + `main.py`: 검색 → 컨텍스트 조립 → Claude 호출 | 질문 → 답변 흐름 동작 |
| 02:10–02:50 | `eval/`: 질문 5개 + 두 전략 비교 + 점수 기록 | `results.csv` |
| 02:50–03:20 | 회고: 막힌 부분 / 배운 점 / 사수에게 물어볼 질문 정리 | `README.md` 회고 섹션 |
| 03:20–03:30 | 다음 단계 메모 (TDD 본격 학습, MCP 변환 등) | 끝 |

마일스톤(놓치면 중단 후 조정):
- **01:30까지 인덱싱 안 끝나면** → 평가 세션 축소 / 청킹 전략 1개로 후퇴.
- **02:10까지 첫 답변 안 나오면** → 평가 생략, 기본 RAG만 완성.

## 11. 다음 단계 (오늘 이후)

- TDD 본격 사이클 학습 (FizzBuzz·문자열 뒤집기 등 작은 문제로 5회 반복).
- 이 mini-RAG를 MCP 서버로 변환 → Claude Code가 도구처럼 호출.
- 청킹 전략 더 추가(의미 기반/문장 기반)해서 평가 확장.

---

## 메모

- 본 문서는 git에 자동 커밋하지 않음 (사용자 규칙).
- `superpowers:brainstorming` 플로우에 따라 작성됨.
- 사용자 최종 검토 후 `writing-plans` skill로 진행.
