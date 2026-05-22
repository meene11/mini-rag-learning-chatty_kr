# mini-rag-learning-chatty_kr

> chatty.kr 문서를 대상으로 한 mini-RAG 실험 — AI 엔지니어 입사 학습 프로젝트 (TDD / RAG / 청킹 비교)

## 진행 상황 (2026-05-22)

설계 + 구현 계획까지 작성 완료. 코드 구현은 다음 단계.

| 산출물 | 위치 | 상태 |
|---|---|---|
| 설계 문서 | [`specs/2026-05-22-mini-rag-design.md`](specs/2026-05-22-mini-rag-design.md) | ✅ |
| 구현 계획 | [`plans/2026-05-22-mini-rag-implementation.md`](plans/2026-05-22-mini-rag-implementation.md) | ✅ |
| 코드 (`src/`, `tests/`, `eval/`) | — | ⏳ 예정 |

## 학습 목표

비전공자 AI 엔지니어 입사 직후 3.5시간 학습 프로젝트로:

1. **RAG (Retrieval-Augmented Generation)** 한 사이클을 직접 만들어보며 체득
2. **TDD (Test-Driven Development)** 사이클 맛보기 (`ingest.py` 청킹 함수)
3. **두 청킹 전략(글자수 기반 vs 문단 기반)** 정확도 비교 — RAG 평가(eval) 영역 체험

## 기술 스택

- Python 3.11, [uv](https://docs.astral.sh/uv/) (패키지 매니저)
- 임베딩: [`BAAI/bge-m3`](https://huggingface.co/BAAI/bge-m3) (sentence-transformers, 로컬)
- 벡터DB: [Chroma](https://www.trychroma.com/) (로컬 영구 저장)
- 생성: [Anthropic Claude Sonnet 4.6](https://www.anthropic.com/) (`claude-sonnet-4-6`)
- 테스트: pytest

자세한 아키텍처 / 데이터 흐름 / 평가 방법은 `specs/`의 설계 문서 참고.

## 다음 단계

`plans/`의 Task 0부터 Task 8까지 순차적으로 구현 예정 — 가상환경 셋업, 청킹 함수 TDD, 임베딩, 검색, 생성, CLI 통합, 평가, 회고.
