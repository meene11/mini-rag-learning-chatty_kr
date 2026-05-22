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
