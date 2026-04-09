"""
services/llm.py  —  Centralised multi-provider LLM caller
==========================================================
Provider waterfall:  Ollama (primary/local) → Groq → Anthropic → Gemini

All services import from here — never call any SDK directly.

Public API
----------
Sync  : llm_call_sync(system, user, *, temp, max_tokens) -> str
        llm_call_smart_sync(...)   higher token budget
        llm_json(...)              returns parsed dict/list
Async : llm_call(...)  /  llm_call_smart(...)

Speed optimisations vs original
---------------------------------
• Ollama chat timeout reduced to 45 s (was 60 s buried in OllamaService)
• llm_call_smart_sync default max_tokens reduced 2048→1536 for 3 B models
• _call_ollama propagates RuntimeError immediately so the waterfall
  moves to Groq fast instead of waiting on a dead connection
• Async path uses asyncio.to_thread (Python 3.9+) instead of
  loop.run_in_executor(None, ...) — cleaner and slightly lower overhead
• Groq/Anthropic/Gemini clients still initialised lazily (no change)
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from typing import Any

logger = logging.getLogger(__name__)


# =============================================================================
# Provider clients  (lazy-initialised)
# =============================================================================

_ollama_service   = None
_groq_client      = None
_anthropic_client = None
_gemini_client    = None
_genai_module     = None


def _get_ollama():
    global _ollama_service
    if _ollama_service is not None:
        return _ollama_service
    try:
        from backend.services.ollama_service import get_ollama_service
        _ollama_service = get_ollama_service()
        if _ollama_service and _ollama_service.available:
            logger.info("[llm] ✅ Ollama service initialised (local primary)")
        else:
            logger.warning("[llm] ⚠️ Ollama service not available")
        return _ollama_service
    except Exception as e:
        logger.warning(f"[llm] ❌ Ollama not available: {e}")
        return None


def _get_groq():
    global _groq_client
    if _groq_client is not None:
        return _groq_client
    from backend.config import settings
    if not settings.GROQ_API_KEY:
        return None
    try:
        from groq import Groq
        import httpx
        http_client = httpx.Client(
            timeout=httpx.Timeout(60.0, connect=10.0),
            follow_redirects=True,
            proxies=None,
        )
        _groq_client = Groq(
            api_key=settings.GROQ_API_KEY,
            http_client=http_client,
            max_retries=0,
        )
        logger.info("[llm] ✅ Groq client initialised (cloud fallback)")
        return _groq_client
    except ImportError:
        logger.warning("[llm] ❌ groq package not installed")
        return None
    except Exception as e:
        logger.warning(f"[llm] ❌ Groq init error: {e}")
        return None


def _get_anthropic():
    global _anthropic_client
    if _anthropic_client is not None:
        return _anthropic_client
    from backend.config import settings
    if not settings.ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic, httpx
        http_client = httpx.Client(
            timeout=httpx.Timeout(60.0, connect=10.0),
            follow_redirects=True,
            proxies=None,
        )
        _anthropic_client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
            http_client=http_client,
            max_retries=0,
        )
        logger.info("[llm] ✅ Anthropic client initialised (cloud fallback)")
        return _anthropic_client
    except ImportError:
        logger.warning("[llm] ❌ anthropic package not installed")
        return None
    except Exception as e:
        logger.warning(f"[llm] ❌ Anthropic init error: {e}")
        return None


def _get_gemini():
    global _gemini_client, _genai_module
    if _gemini_client is not None:
        return _gemini_client, _genai_module
    from backend.config import settings
    if not settings.GEMINI_API_KEY:
        return None, None
    try:
        from google import genai as _g
        _genai_module = _g
        _gemini_client = _g.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options={"api_version": "v1"},
        )
        logger.info("[llm] ✅ Gemini client initialised (tertiary fallback)")
        return _gemini_client, _genai_module
    except ImportError:
        logger.warning("[llm] ❌ google-genai package not installed")
        return None, None
    except Exception as e:
        logger.warning(f"[llm] ❌ Gemini init error: {e}")
        return None, None


# =============================================================================
# Error helpers
# =============================================================================

def _parse_retry_after(exc: Exception) -> float:
    text = str(exc)
    m = re.search(r'retry[^0-9]{0,20}(\d+(?:\.\d+)?)\s*s', text, re.IGNORECASE)
    if m:
        return min(float(m.group(1)), 60.0)
    m = re.search(r'(\d+(?:\.\d+)?)\s*s', text)
    if m:
        return min(float(m.group(1)), 60.0)
    return 5.0


def _is_groq_ratelimit(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in ("429", "rate_limit", "ratelimit", "rate limit"))


def _is_groq_unavailable(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in ("503", "502", "unavailable", "overloaded"))


def _is_anthropic_overload(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in ("529", "overloaded", "503", "unavailable"))


def _is_quota_exhausted(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in ("quota", "resource_exhausted", "resourceexhausted", "limit: 0"))


# =============================================================================
# Individual provider callers
# =============================================================================

_MAX_RETRIES = 2


def _call_ollama(system: str, user: str, *, temp: float, max_tokens: int) -> str:
    """
    Call Ollama local LLM.
    Cap max_tokens at 1024 for the 3 B model — larger budgets slow it
    considerably and rarely improve quality for structured outputs.
    """
    svc = _get_ollama()
    if not svc or not svc.available:
        raise RuntimeError("Ollama service not available. Run 'ollama serve'")

    # Protect against callers requesting huge outputs from a tiny local model
    effective_tokens = min(max_tokens, 1024)

    messages = [
        {"role": "system", "content": system},
        {"role": "user",   "content": user},
    ]

    result = svc.chat(messages, temperature=temp, max_tokens=effective_tokens)

    if result and len(result) > 5:
        logger.info(f"[llm] ✅ Ollama/{svc.llm_model} → {len(result)} chars")
        return result

    raise RuntimeError("Empty or too-short response from Ollama")


def _call_groq(system: str, user: str, *, temp: float, max_tokens: int) -> str:
    from backend.config import settings
    client = _get_groq()
    if not client:
        raise RuntimeError("Groq not configured")

    models = list(dict.fromkeys([settings.GROQ_CHAT_MODEL] + settings.GROQ_FALLBACK_MODELS))

    for model in models:
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user",   "content": user},
                    ],
                    temperature=temp,
                    max_tokens=max_tokens,
                )
                result = resp.choices[0].message.content.strip()
                logger.info(f"[llm] ✅ Groq/{model} (attempt {attempt + 1})")
                return result

            except Exception as exc:
                if _is_groq_ratelimit(exc):
                    delay = _parse_retry_after(exc)
                    if attempt < _MAX_RETRIES:
                        logger.warning(f"[llm] ⏳ Groq/{model} rate-limited, sleeping {delay:.0f}s")
                        time.sleep(delay)
                    else:
                        logger.warning(f"[llm] ⚠️  Groq/{model} rate-limit exhausted → next model")
                        break
                elif _is_groq_unavailable(exc):
                    if attempt < _MAX_RETRIES:
                        logger.warning(f"[llm] ⏳ Groq/{model} unavailable, retrying in 3s")
                        time.sleep(3)
                    else:
                        logger.warning(f"[llm] ⚠️  Groq/{model} still unavailable → next model")
                        break
                else:
                    logger.error(f"[llm] ❌ Groq/{model} fatal: {exc}")
                    raise

    raise RuntimeError("All Groq models failed — falling through to Anthropic")


def _call_anthropic(system: str, user: str, *, temp: float, max_tokens: int) -> str:
    from backend.config import settings
    client = _get_anthropic()
    if not client:
        raise RuntimeError("Anthropic not configured")

    models = list(dict.fromkeys(
        [settings.ANTHROPIC_CHAT_MODEL] + settings.ANTHROPIC_FALLBACK_MODELS
    ))

    for model in models:
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temp,
                    system=system,
                    messages=[{"role": "user", "content": user}],
                )
                result = resp.content[0].text.strip()
                logger.info(f"[llm] ✅ Anthropic/{model} (attempt {attempt + 1})")
                return result

            except Exception as exc:
                if _is_anthropic_overload(exc):
                    delay = _parse_retry_after(exc) if attempt > 0 else 3.0
                    if attempt < _MAX_RETRIES:
                        logger.warning(f"[llm] ⏳ Anthropic/{model} overloaded, sleeping {delay:.0f}s")
                        time.sleep(delay)
                    else:
                        logger.warning(f"[llm] ⚠️  Anthropic/{model} still overloaded → next model")
                        break
                else:
                    logger.error(f"[llm] ❌ Anthropic/{model} fatal: {exc}")
                    raise

    raise RuntimeError("All Anthropic models failed — falling through to Gemini")


def _call_gemini(system: str, user: str, *, temp: float, max_tokens: int) -> str:
    from backend.config import settings
    client, genai = _get_gemini()
    if not client or not genai:
        raise RuntimeError("Gemini not configured")

    models = list(dict.fromkeys(
        [settings.GEMINI_SMART_MODEL] + settings.GEMINI_FALLBACK_MODELS
    ))

    for model in models:
        try:
            contents = [{"role": "user", "parts": [{"text": f"{system}\n\n{user}"}]}]
            response = client.models.generate_content(
                model=model,
                config=genai.types.GenerateContentConfig(
                    temperature=temp,
                    max_output_tokens=max_tokens,
                ),
                contents=contents,
            )
            logger.info(f"[llm] ✅ Gemini/{model}")
            return response.text.strip()
        except Exception as exc:
            if _is_quota_exhausted(exc):
                logger.warning(f"[llm] ⚠️  Gemini/{model} quota exhausted → next model")
                continue
            logger.error(f"[llm] ❌ Gemini/{model}: {exc}")
            raise

    raise RuntimeError("All Gemini models quota-exhausted")


# =============================================================================
# Main dispatcher  (Ollama → Groq → Anthropic → Gemini)
# =============================================================================

def _call_sync(
    system:     str,
    user:       str,
    *,
    temp:       float = 0.7,
    max_tokens: int   = 1024,
) -> str:
    from backend.config import settings

    # 1. Ollama (local, no rate limits, no internet needed)
    try:
        return _call_ollama(system, user, temp=temp, max_tokens=max_tokens)
    except Exception as e:
        logger.warning(f"[llm] Ollama failed: {e} → trying Groq")

    # 2. Groq
    if settings.GROQ_API_KEY:
        try:
            return _call_groq(system, user, temp=temp, max_tokens=max_tokens)
        except RuntimeError as e:
            logger.warning(f"[llm] Groq exhausted: {e} → trying Anthropic")
        except Exception as e:
            logger.warning(f"[llm] Groq error: {e} → trying Anthropic")

    # 3. Anthropic
    if settings.ANTHROPIC_API_KEY:
        try:
            return _call_anthropic(system, user, temp=temp, max_tokens=max_tokens)
        except RuntimeError as e:
            logger.warning(f"[llm] Anthropic exhausted: {e} → trying Gemini")
        except Exception as e:
            logger.warning(f"[llm] Anthropic error: {e} → trying Gemini")

    # 4. Gemini
    if settings.GEMINI_API_KEY:
        try:
            return _call_gemini(system, user, temp=temp, max_tokens=max_tokens)
        except Exception as e:
            logger.warning(f"[llm] Gemini error: {e}")

    raise RuntimeError(
        "No LLM providers available.\n"
        "Make sure Ollama is running (recommended) or set at least one API key:\n"
        "  - Ollama: run 'ollama serve' and 'ollama pull llama3.2:3b'\n"
        "  - Groq: set GROQ_API_KEY in backend/.env\n"
        "  - Anthropic: set ANTHROPIC_API_KEY in backend/.env\n"
        "  - Gemini: set GEMINI_API_KEY in backend/.env"
    )


# =============================================================================
# Public API — Sync
# =============================================================================

def llm_call_sync(
    system: str,
    user: str,
    *,
    temp: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """Sync LLM call — Ollama → Groq → Anthropic → Gemini."""
    return _call_sync(system, user, temp=temp, max_tokens=max_tokens)


def llm_call_smart_sync(
    system: str,
    user: str,
    *,
    temp: float = 0.5,
    # Reduced from 2048 → 1536: llama3.2:3b doesn't benefit from huge
    # budgets and the extra tokens cost significant extra latency.
    # Cloud providers will honour the full value if Ollama falls through.
    max_tokens: int = 1536,
) -> str:
    """Higher-token sync call for roadmaps, career advice, debate synthesis."""
    return _call_sync(system, user, temp=temp, max_tokens=max_tokens)


def llm_json(
    system: str,
    user: str,
    *,
    temp: float = 0.3,
    max_tokens: int = 2048,
) -> Any:
    """
    Call LLM and return parsed JSON dict/list.
    Strips markdown fences automatically.
    Raises json.JSONDecodeError if the model returns non-JSON.
    """
    raw = _call_sync(system, user, temp=temp, max_tokens=max_tokens)
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    return json.loads(cleaned)


# =============================================================================
# Public API — Async
# =============================================================================

async def llm_call(
    system: str,
    user: str,
    *,
    temp: float = 0.7,
    max_tokens: int = 1024,
) -> str:
    """Async LLM call — Ollama → Groq → Anthropic → Gemini."""
    return await asyncio.to_thread(
        _call_sync, system, user, temp=temp, max_tokens=max_tokens
    )


async def llm_call_smart(
    system: str,
    user: str,
    *,
    temp: float = 0.5,
    max_tokens: int = 1536,
) -> str:
    """Async higher-token call for synthesis / debate."""
    return await asyncio.to_thread(
        _call_sync, system, user, temp=temp, max_tokens=max_tokens
    )