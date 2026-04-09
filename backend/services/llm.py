"""
services/llm.py
================
Async LLM service — thin wrapper around the Google Gemini client that:
  • configures the SDK once at import time
  • runs blocking SDK calls in a thread executor (non-blocking event loop)
  • exposes a clean async llm_call(system, user, temp) interface
  • is the single place where model selection lives
  • used by proposer agents, critic, and synthesizer for async parallel execution
"""
from __future__ import annotations

import asyncio
import logging

import google.genai as genai

from backend.config import settings

logger = logging.getLogger(__name__)

# Configure the SDK once
_genai_client = genai.Client(api_key=settings.GEMINI_API_KEY)


async def llm_call(
    system: str,
    user: str,
    temp: float = 0.7,
    model: str | None = None,
    max_tokens: int = 1024,
) -> str:
    """
    Async LLM call via Google Gemini. The blocking SDK call is offloaded to a
    thread pool executor so it never blocks the event loop — enabling true
    parallel proposer execution with asyncio.gather().
    """
    chosen_model = model or settings.GEMINI_CHAT_MODEL
    loop = asyncio.get_event_loop()

    def _run() -> str:
        response = _genai_client.models.generate_content(
            model=chosen_model,
            config=genai.types.GenerateContentConfig(
                system_instruction=system,
                temperature=temp,
                max_output_tokens=max_tokens,
            ),
            contents=user,
        )
        return response.text.strip()

    try:
        return await loop.run_in_executor(None, _run)
    except Exception as e:
        logger.error(f"llm_call failed (model={chosen_model}): {e}")
        raise


async def llm_call_smart(system: str, user: str, temp: float = 0.5, max_tokens: int = 1500) -> str:
    """Convenience wrapper that always uses the SMART (Pro) model."""
    return await llm_call(system, user, temp=temp, model=settings.GEMINI_SMART_MODEL, max_tokens=max_tokens)
