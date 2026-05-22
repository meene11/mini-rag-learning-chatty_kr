# mini-rag-learning-chatty_kr

> chatty.kr 문서를 대상으로 한 mini-RAG 실험 — AI 엔지니어 입사 학습 프로젝트 (TDD / RAG / 청킹 비교)

## 현재 상태 (2026-05-22)

✅ MVP 완료 — 두 청킹 전략 인덱싱·검색·답변 비교 가능. 5질문 평가 결과 1세트 저장.

| 산출물 | 위치 |
|---|---|
| 설계 문서 | [`specs/2026-05-22-mini-rag-design.md`](specs/2026-05-22-mini-rag-design.md) |
| 구현 계획 | [`plans/2026-05-22-mini-rag-implementation.md`](plans/2026-05-22-mini-rag-implementation.md) |
| 평가 결과 (CSV) | [`eval/results.csv`](eval/results.csv) |
| 평가 질문 | [`eval/questions.txt`](eval/questions.txt) |

## 학습 목표

AI 엔지니어 입사 첫주동안의 학습 프로젝트:

1. **RAG (Retrieval-Augmented Generation)** 한 사이클 직접 구축 → 체득
2. **TDD (Test-Driven Development)** 사이클 맛보기 (`ingest.py` 청킹 함수에 pytest 8개)
3. **두 청킹 전략(글자수 vs 문단)** 정확도 비교 — RAG 평가 영역 체험

## 기술 스택

- Python 3.11, [uv](https://docs.astral.sh/uv/) (패키지 매니저)
- 임베딩: [`BAAI/bge-m3`](https://huggingface.co/BAAI/bge-m3) (sentence-transformers, 로컬)
- 벡터DB: [Chroma](https://www.trychroma.com/) (로컬 영구 저장)
- 생성: [Google Gemini Flash](https://aistudio.google.com/) (`gemini-2.5-flash`) — 무료 quota
- 테스트: pytest (TDD)

## 사용법

```powershell
# 1. 의존성 설치 (최초 1회)
uv sync

# 2. .env 작성 — .env.example 참고해 GOOGLE_API_KEY 입력
# 키 발급: https://aistudio.google.com/apikey

# 3. 인덱싱 (첫 실행 시 bge-m3 모델 다운로드)
uv run python -m src.main index

# 4. 단일 질문
uv run python -m src.main ask "AI 채팅의 핵심 기술이 뭐야?"

# 5. 평가 (5질문 x 2전략 자동 비교)
uv run python -m src.main eval

# 6. 테스트
uv run pytest -v
```

## 구조

```
src/
  ingest.py     # 텍스트 로드 + 두 청킹 전략 (chunk_by_chars, chunk_by_paragraphs) + load_documents
  retrieve.py   # bge-m3 임베딩 + Chroma 인덱싱/검색 (Retriever 클래스)
  generate.py   # Gemini Flash 답변 생성 + 503 재시도 + flash-lite fallback
  main.py       # CLI (index / ask / eval)
tests/
  test_ingest.py  # pytest 8개 (청킹 함수 TDD)
docs/
  chatty_*.txt  # chatty.kr 5페이지 본문 (~7000자)
eval/
  questions.txt  # 평가 질문 5개
  results.csv    # 평가 결과 (10행 = 5질문 × 2전략)
```

## 첫 평가 결과 — 두 청킹 전략 비교

### L1 — 구조 메트릭 (chatty.kr 6,949자 기준)

| 전략 | 청크 수 | 평균 길이 | 표준편차 | 최소 | 최대 |
|---|---|---|---|---|---|
| 글자수 (500/50) | 16 | 482자 | 73자 | 207자 | 500자 |
| 문단 | 57 | 120자 | 81자 | **4자** ⚠️ | 382자 |

→ 문단 전략은 청크 수가 3.5배 많지만 "4자짜리" 같은 노이즈 청크 발생.

### L2/L3 — 검색 + 답변 품질 (5질문 평가)

| 질문 유형 | char 답변길이 | para 답변길이 | 단어 일치도 | 인사이트 |
|---|---|---|---|---|
| Q1 (종합) AI 채팅 핵심 기술 | 87자 | 35자 | 25% | char가 LLM/Web 검색까지 잡음 |
| Q2 (단답) 번역 언어 수 | 23자 | 18자 | 50% | 차이 미미 |
| Q3 (단답) 문서요약 동시 파일 | 47자 | 48자 | 85% | 거의 동일 |
| **Q4 (추론) RAG 활용** | **645자** | 276자 | **16%** | char 압승 |
| Q5 (목록) 파일 형식 | 161자 | 162자 | 52% | 비슷한 품질 |

### 발견한 패턴

> - **단답형 사실 질문** → 두 전략 차이 거의 없음
> - **추론·종합 질문** → 글자수 전략이 압도적으로 풍부 (더 큰 컨텍스트 ~500자 vs ~120자)
> - **단어 Jaccard 일치도** = 답변 깊이의 가시화 지표 (낮을수록 두 전략 차이 큼)
>
> 한국어 마케팅 텍스트 RAG에서 추론 답변이 필요하면 글자수 청킹 우위. 단답형 위주면 어느 전략이든 OK.

## 회고

### 잘 된 점
- **TDD 사이클 2회 완주** — 청킹 함수 작성 전 테스트 먼저 → Red → Green. 실제로 테스트 데이터가 함수 기본값(min_chars=100)과 맞지 않아 실패 → 테스트 + 구현 둘 다 손봐서 해결. "테스트도 틀릴 수 있다"는 실무 감각.
- **자동 비교 메트릭** (단어 Jaccard 일치도, 청크 평균 길이) 추가로 사람이 5점 점수 매기지 않아도 차이 가시화.
- **503 재시도 + fallback** — 실전 중 Gemini API가 503을 자주 던지는 걸 발견 → 재시도 로직 + flash-lite fallback 즉시 추가. 코드 한 단계 production-grade로 올라감.

### 막힌 점
- chatty.kr `/doc/presentation.htm`가 사실 프레젠테이션 생성 페이지여서 AI 문서요약 텍스트가 부족 → 메인 페이지 발췌로 보강.
- PowerShell heredoc + 한국어 + 특수문자 조합이 잘 안 풀려서 commit 메시지를 임시 파일에 써서 `git commit -F`로 처리. 인코딩 함정.
- 콘솔 출력 한국어가 mojibake로 깨지지만 파일에는 정상 UTF-8 — 학습용엔 무시 가능.

### 다음에 해볼 것 (단계별)
- **청킹 전략 추가**: 의미 기반(LLM으로 토픽 단위 자르기) / 문장 기반(마침표) 추가해 4종 비교
- **L1 자동화**: `src/compare_chunking.py` 분리해 청크 길이 히스토그램 시각화
- **MCP 서버화**: 이 mini-RAG를 MCP 서버로 감싸 Claude Code 안에서 도구처럼 호출
- **TDD 본격 학습**: 작은 문제(FizzBuzz, 문자열 뒤집기 등) 5회 사이클 반복
- **회사 진짜 RAG 코드 매핑**: 이 구조를 바탕으로 사수 코드 읽을 때 이해 가속

### 사수에게 물어볼 것
- 회사 RAG는 어떤 임베딩 모델 / 벡터DB를 쓰는지?
- 청킹 전략은 어떻게 결정했고, 평가 메트릭은 무엇을 쓰는지?
- transient API 에러는 어떻게 처리하는지 (재시도 횟수, 백오프, fallback 정책)?
- 평가용 골든셋(질문·정답 쌍)은 어떻게 관리하는지?
