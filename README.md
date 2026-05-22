# mini-rag-learning-chatty_kr

> chatty.kr 문서를 대상으로 한 mini-RAG 실험 — AI 엔지니어 입사 학습 프로젝트 (TDD / RAG / 청킹 비교)

## 한 문장으로 이게 뭔가요

> **chatty.kr 회사 소개 텍스트에 자연어로 질문하면, 그 회사 자료를 근거로 답을 만들어주는 작은 챗봇.** 텍스트를 자르는 두 가지 방식(글자수 vs 문단)으로 동시에 만들어, 어느 쪽이 더 좋은 답을 내는지 정량 비교한 학습 프로젝트.

## 이게 어떻게 돌아가는가 (비전공자용 흐름)

### 1단계 — 인덱싱 (한 번만, `python -m src.main index`)
1. `docs/` 폴더의 .txt 5개를 통째로 읽음
2. 텍스트를 **두 가지 방식으로 잘라 청크 만들기**
   - **글자수 전략**: 500자씩, 50자 겹치게 → 16청크
   - **문단 전략**: 빈 줄 기준으로 → 57청크
3. 각 청크를 **"의미 숫자"(임베딩, 1024차원 벡터)** 로 변환 (bge-m3 모델 사용)
4. Chroma DB에 **두 개의 컬렉션(`rag_char`, `rag_para`)** 으로 따로 저장

### 2단계 — 질문 (`python -m src.main ask "..."`)
1. 사용자 질문도 같은 방식으로 **의미 숫자로 변환**
2. 두 컬렉션 각각에서 **의미가 가까운 청크 top-3 검색** (벡터 거리 계산)
3. 검색된 3청크 + 질문을 **Gemini Flash에 "이 자료만 보고 답해줘"** 라고 전달
4. Gemini가 자연스러운 한국어 답변 생성
5. 두 전략의 답변을 **나란히 출력** → 비교 가능

### 3단계 — 평가 (`python -m src.main eval`)
1. `eval/questions.txt`의 5질문을 두 전략에 던짐
2. 각 질문에 대해 **두 답변의 단어 일치도(Jaccard)** 자동 계산
3. 10행 CSV로 `eval/results.csv` 저장

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

## 기술 스택 — 무엇을 왜 골랐나

| 도구 | 역할 | 왜 골랐나 |
|---|---|---|
| **Python 3.11** | 언어 | AI 생태계 표준. 사용자 학습용 |
| **uv** | 패키지 매니저 | pip보다 10~100배 빠름. 가상환경 + 의존성 잠금 일체 |
| **sentence-transformers** | 임베딩 라이브러리 | 모델을 로컬에서 무료로 실행 (API 호출 불필요) |
| **BAAI/bge-m3** | 임베딩 모델 | 다국어 강함. **한국어 RAG에서 사실상 표준** |
| **chromadb** | 벡터 데이터베이스 | 3줄로 시작, 자동 영구 저장, 메타데이터 지원 |
| **google-genai** | Gemini SDK | Google 공식, async 지원, 깔끔한 API |
| **gemini-2.5-flash** | LLM (답변 생성) | **무료 quota** 분 15회·일 1500회, 한국어 강함 |
| **gemini-2.5-flash-lite** | LLM fallback | 본 모델 503 시 자동 대체 |
| **pytest** | 테스트 러너 | Python 표준 테스트 도구, TDD에 필수 |
| **python-dotenv** | .env 로더 | API 키를 코드에 하드코딩 안 함 |

> 💡 임베딩(`bge-m3`)은 **사용자 PC에서 실행** → 키 불필요·무료. 생성(`gemini-2.5-flash`)만 외부 API → 무료 quota 사용. 즉 **API 키 1개**(`GOOGLE_API_KEY`)만 있으면 끝.

## 사용법

> VSCode 터미널에서 가상환경 `(mini-rag)`가 활성화돼 있으면 `uv run` 생략 가능.

```powershell
# 1. 의존성 설치 (최초 1회 — pyproject.toml 보고 자동 설치)
uv sync

# 2. .env 작성 — .env.example 복사해서 GOOGLE_API_KEY 채우기
#   키 발급: https://aistudio.google.com/apikey  (Google 계정 로그인 → "Create API Key")

# 3. 인덱싱: docs/의 5개 .txt 읽어 두 컬렉션에 저장
#   첫 실행 시 bge-m3 모델 ~2GB 다운로드 (이후 캐시)
uv run python -m src.main index

# 4. 단일 질문 — 두 전략의 답변 나란히 비교
uv run python -m src.main ask "AI 채팅의 핵심 기술이 뭐야?"

# 5. 평가 — 5질문 × 2전략 = 10 Gemini 호출, eval/results.csv 저장
uv run python -m src.main eval

# 6. 테스트 — 청킹 함수 8개
uv run pytest -v

# 7. 특정 테스트만
uv run pytest -k chunk_by_chars -v
```

## 구조 — 각 파일 한 줄 요약

```
src/
  ingest.py     ── 텍스트를 두 가지 방식으로 자르는 함수들 + 파일 로더
  retrieve.py   ── 청크를 의미 숫자로 변환해 Chroma에 저장, 질문으로 유사 청크 찾기
  generate.py   ── 청크+질문을 Gemini에 보내 답 받기 (503 재시도 + fallback 포함)
  main.py       ── 위 3개를 묶어 CLI로 노출 (index / ask / eval)
tests/
  test_ingest.py ── 청킹 함수가 의도대로 자르는지 검증 (pytest 8개, TDD로 작성)
docs/
  chatty_*.txt   ── chatty.kr 5페이지 본문 (RAG 대상 데이터, ~7000자)
eval/
  questions.txt  ── 평가용 질문 5개 (한 줄에 한 질문)
  results.csv    ── 평가 결과 (각 행: 질문/전략/검색청크/답변/일치도)
specs/
  *.md           ── 프로젝트 설계 문서
plans/
  *.md           ── 단계별 구현 계획 (Task 0~8)
.env.example     ── API 키 입력 템플릿 (.env는 gitignore)
pyproject.toml   ── 의존성·Python 버전 잠금 (uv가 관리)
uv.lock          ── 모든 패키지 버전 정확히 잠금
```

### 핵심 함수 시그니처 (검색해서 코드 찾을 때 유용)

| 함수 / 클래스 | 위치 | 입력 → 출력 |
|---|---|---|
| `chunk_by_chars(text, size, overlap)` | `src/ingest.py` | 긴 문자열 → 500자씩 잘린 청크 리스트 |
| `chunk_by_paragraphs(text, min_chars, max_chars)` | `src/ingest.py` | 긴 문자열 → 문단 단위 청크 리스트 |
| `load_documents(docs_dir)` | `src/ingest.py` | 폴더 → `{파일명: 내용}` dict |
| `Retriever()` | `src/retrieve.py` | bge-m3 모델 로드 + Chroma 클라이언트 |
| `Retriever.index(name, chunks)` | `src/retrieve.py` | 청크 리스트 → 임베딩 후 Chroma 저장 |
| `Retriever.search(name, query, top_k)` | `src/retrieve.py` | 질문 → 유사 청크 top_k |
| `generate_answer(question, chunks)` | `src/generate.py` | 질문+청크 → Gemini 답변 문자열 |

## 데이터·평가 입력 — 무엇으로 RAG를 돌렸나

### `docs/` — RAG 학습 대상 5개 파일

| 파일 | chatty.kr 출처 | 길이 | 들어있는 내용 |
|---|---|---|---|
| `chatty_main.txt` | 메인 페이지 (전체 개요) | 1,499자 | 9개 기능(채팅·검색·번역·문서·이미지·음악·동영상·업무지원·학습관리) 한눈 요약 |
| `chatty_chat.txt` | **AI 채팅** 상세 페이지 | 1,760자 | RAG 정의·역할, 텍스트·홈페이지·파일 학습 방식, 24/365 응답, 웹검색 지원 |
| `chatty_search.txt` | **AI 검색** 상세 페이지 | 585자 | 자연어 검색, 통합검색, 멀티미디어(파일·이미지·동영상) 검색, 추천 질문 |
| `chatty_translate.txt` | **AI 번역** 상세 페이지 | 1,908자 | NMT 기술, 104개 언어 지원, 오타 자동 교정, "은행에서 돈을 찾았다" 맥락 번역 예시 |
| `chatty_doc.txt` | **AI 문서요약** 영역 | 1,197자 | 동시 5개 파일 요약, 다국어→한국어 요약, pdf/hwp/ppt/xls 지원, 프레젠테이션 생성(보조) |
| **합계** | — | **6,949자** | — |

→ 본문만 추출 (메뉴·푸터·UI 라벨 제외). 청킹·임베딩·검색·답변 생성의 입력 데이터.

### `eval/questions.txt` — 평가용 5개 질문

```
1. AI 채팅의 핵심 기술이 뭐야?
2. 번역 기능은 몇 개 언어를 지원해?
3. AI 문서요약 기능에서 한 번에 몇 개 파일을 같이 요약할 수 있어?
4. RAG가 이 서비스에서 어떻게 활용돼?
5. 어떤 파일 형식을 학습할 수 있어?
```

선정 기준 — 두 청킹 전략의 차이를 다양한 각도에서 검증:

| 질문 | 유형 | 정답이 있는 문서 | 측정하려는 것 |
|---|---|---|---|
| Q1 | 종합 (여러 기능 언급) | chatty_chat.txt | 검색이 핵심 청크 다 잡는가 |
| Q2 | 단답 (숫자 1개) | chatty_translate.txt | 단답 정확도 — 두 전략 동등성 |
| Q3 | 단답 (숫자 1개) | chatty_doc.txt | 단답 정확도 — 두 전략 동등성 |
| Q4 | **추론** (배경 + 활용 + 결론) | chatty_chat.txt | 컨텍스트 양 차이의 영향 (가장 큰 차이 기대) |
| Q5 | 목록 (파일 형식 다수) | chatty_chat.txt | 정보 누락 차이 |

→ 5개 모두 다른 문서를 정답 영역으로 가져 **검색 폭** 도 함께 테스트.

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
