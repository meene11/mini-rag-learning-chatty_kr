"""Google Gemini Flash을 사용해 컨텍스트 기반 답변을 생성한다.

503/지연 시 자동 재시도 + 마지막 시도엔 flash-lite로 fallback.
"""

import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import ServerError

load_dotenv()

PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.5-flash-lite"
MAX_OUTPUT_TOKENS = 1024
MAX_ATTEMPTS = 3


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


def _call_model(client: genai.Client, model: str, question: str, system_prompt: str) -> str:
    response = client.models.generate_content(
        model=model,
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        ),
    )
    return response.text


def generate_answer(question: str, context_chunks: list[str]) -> str:
    """질문 + 검색된 청크 → Gemini Flash 답변.

    503/일시 장애 시 지수 backoff로 재시도. 마지막 시도에선 flash-lite로 fallback.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            ".env에 GOOGLE_API_KEY가 없습니다. .env.example을 참고해 작성하세요. "
            "키 발급: https://aistudio.google.com/apikey"
        )
    client = genai.Client(api_key=api_key)
    system_prompt = _build_system_prompt(context_chunks)

    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        model = FALLBACK_MODEL if attempt == MAX_ATTEMPTS - 1 else PRIMARY_MODEL
        try:
            return _call_model(client, model, question, system_prompt)
        except ServerError as e:
            last_error = e
            if attempt < MAX_ATTEMPTS - 1:
                wait = 2 ** attempt  # 1, 2초
                print(f"  ⚠️ {model} 일시 장애 ({e.status}). {wait}초 후 재시도...")
                time.sleep(wait)
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError("unreachable")
