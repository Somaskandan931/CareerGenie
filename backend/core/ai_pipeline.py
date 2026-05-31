"""
backend/core/ai_pipeline.py
============================
Unified AI pipeline — the **single entry point** for every LLM call.

Every AI feature routes through here instead of calling llm.py directly.
This layer provides:

  1. In-memory response caching with configurable TTL
  2. Prompt-injection sanitization on user-supplied content
  3. Structured output validation via Pydantic schemas
  4. Centralized retry / fallback logic
  5. AI token cost tracking (counters, not billing)
  6. Consistent error handling — only ``AIError`` subclasses escape

Public API::

    from backend.core import ai_pipeline

    # Plain text response
    text = ai_pipeline.call(system, user)

    # Parse JSON from LLM
    data = ai_pipeline.call_json(system, user)

    # Validate against a Pydantic model
    obj  = ai_pipeline.call_structured(system, user, schema=MyModel)

    # High-token call for roadmaps / detailed advice
    text = ai_pipeline.call_smart(system, user)

    # Multiple prompts in one go
    results = ai_pipeline.call_batch([{"system": s, "user": u}, ...])
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from backend.core.exceptions import LLMParseError, LLMUnavailableError
from backend.core.logging import get_logger, log_ai_error, AIErrorCategory

logger = get_logger("ai_pipeline")

T = TypeVar("T", bound=BaseModel)


# ── In-memory response cache ──────────────────────────────────────────────────
# Structure: cache_key → {"value": str, "expires": float, "hits": int}
# Not thread-safe for multi-process deployments — use Redis in production (Phase 2).

_cache: Dict[str, Dict[str, Any]] = {}
_DEFAULT_TTL: int = 3600          # 1 hour
_MAX_CACHE_ENTRIES: int = 512     # evict oldest when exceeded


def _cache_key(system: str, user: str, temp: float, max_tokens: int) -> str:
    raw = f"{system}\x00{user}\x00{temp:.3f}\x00{max_tokens}"
    return hashlib.sha256(raw.encode()).hexdigest()[:40]


def _get_cached(key: str) -> Optional[str]:
    entry = _cache.get(key)
    if entry is None:
        return None
    if time.time() >= entry["expires"]:
        del _cache[key]
        return None
    entry["hits"] += 1
    return entry["value"]


def _set_cached(key: str, value: str, ttl: int = _DEFAULT_TTL) -> None:
    # Simple LRU eviction: drop the oldest entry when at capacity
    if len(_cache) >= _MAX_CACHE_ENTRIES:
        oldest_key = next(iter(_cache))
        del _cache[oldest_key]
    _cache[key] = {"value": value, "expires": time.time() + ttl, "hits": 0}


def clear_cache() -> int:
    """Clear all cached responses. Returns the number of entries removed."""
    n = len(_cache)
    _cache.clear()
    return n


def cache_stats() -> Dict[str, int]:
    """Return a snapshot of cache health metrics."""
    now = time.time()
    live = sum(1 for e in _cache.values() if now < e["expires"])
    total_hits = sum(e["hits"] for e in _cache.values())
    return {
        "total_entries": len(_cache),
        "live_entries": live,
        "expired_entries": len(_cache) - live,
        "total_hits": total_hits,
        "capacity": _MAX_CACHE_ENTRIES,
    }


# ── Prompt injection sanitization ─────────────────────────────────────────────
# Applied to *user-supplied* content (resume text, user messages).
# Never applied to system prompts, which come from code.

_INJECTION_PATTERNS: List[re.Pattern] = [
    re.compile(r"ignore\s+(previous|all|above|prior)\s+instructions?", re.I),
    re.compile(r"you\s+are\s+now\s+(a\s+|an\s+)?\w+\s*(AI|assistant|bot|model)", re.I),
    re.compile(r"pretend\s+(you\s+are|to\s+be)", re.I),
    re.compile(r"disregard\s+your\s+(instructions?|training|guidelines?|rules?)", re.I),
    re.compile(r"act\s+as\s+(if\s+you\s+are|a\s+)", re.I),
    re.compile(r"system\s*[\-_]?\s*prompt", re.I),
    re.compile(r"<\s*/?system\s*>", re.I),
    re.compile(r"\[INST\]|\[/INST\]", re.I),        # Llama instruction tags
    re.compile(r"<\|im_start\|>|<\|im_end\|>", re.I),  # ChatML tags
    re.compile(r"###\s*(Instruction|System|Human|Assistant)\s*:", re.I),
]


def sanitize_user_content(text: str, max_length: int = 8000) -> str:
    """
    Strip prompt-injection patterns from user-supplied content.

    Also enforces ``max_length`` to prevent context stuffing.
    Logs a warning if any pattern is matched (for monitoring).

    Args:
        text:       Raw user-supplied text (resume, chat message, etc.).
        max_length: Maximum allowed characters; excess is silently truncated.

    Returns:
        Sanitized text safe to interpolate into a prompt.
    """
    if not text:
        return ""

    text = text[:max_length]
    matched = False
    for pattern in _INJECTION_PATTERNS:
        new_text, n = pattern.subn("[REDACTED]", text)
        if n:
            matched = True
            text = new_text

    if matched:
        log_ai_error(
            logger,
            AIErrorCategory.INJECTION_BLOCKED,
            "Prompt injection pattern detected and redacted in user content",
        )

    return text


# ── Token counter (lightweight, no billing logic) ─────────────────────────────

_token_counters: Dict[str, int] = {
    "total_calls": 0,
    "cache_hits": 0,
    "llm_calls": 0,
    "parse_errors": 0,
    "fallbacks_triggered": 0,
}


def get_counters() -> Dict[str, int]:
    """Return a copy of the AI usage counters (reset on process restart)."""
    return dict(_token_counters)


def reset_counters() -> None:
    """Reset all counters to zero (useful in tests)."""
    for k in _token_counters:
        _token_counters[k] = 0


# ── Core pipeline call ────────────────────────────────────────────────────────

def call(
    system: str,
    user: str,
    *,
    temp: float = 0.7,
    max_tokens: int = 1024,
    use_cache: bool = True,
    cache_ttl: int = _DEFAULT_TTL,
    smart: bool = False,
) -> str:
    """
    Make an LLM call through the unified pipeline.

    Pipeline steps:
      1. Cache check — return immediately on hit
      2. LLM call (smart or standard) via ``backend.services.llm``
      3. Cache store on success
      4. Counter update

    Args:
        system:     System prompt — comes from code, **not** sanitized here.
                    Sanitize user-supplied fields in the caller via
                    :func:`sanitize_user_content` before building the prompt.
        user:       User / human turn prompt.
        temp:       Sampling temperature (0.0 – 1.0).
        max_tokens: Maximum output tokens.
        use_cache:  Whether to check / populate the in-memory cache.
        cache_ttl:  Cache TTL in seconds (default 1 hour).
        smart:      If ``True``, uses the higher-capacity smart model
                    (e.g. for roadmaps, detailed career advice).

    Returns:
        LLM response as a plain string.

    Raises:
        :class:`~backend.core.exceptions.LLMUnavailableError`:
            All configured providers failed.
    """
    _token_counters["total_calls"] += 1

    # ── Cache check ───────────────────────────────────────────────────────────
    if use_cache:
        key = _cache_key(system, user, temp, max_tokens)
        cached = _get_cached(key)
        if cached is not None:
            _token_counters["cache_hits"] += 1
            logger.debug("Cache hit (%s…)", key[:10])
            return cached

    # ── LLM call ──────────────────────────────────────────────────────────────
    try:
        from backend.services.llm import llm_call_sync, llm_call_smart_sync  # noqa: PLC0415
        fn = llm_call_smart_sync if smart else llm_call_sync
        result: str = fn(system=system, user=user, temp=temp, max_tokens=max_tokens)
        _token_counters["llm_calls"] += 1
    except RuntimeError as exc:
        log_ai_error(logger, AIErrorCategory.LLM_UNAVAILABLE, str(exc))
        raise LLMUnavailableError(str(exc)) from exc
    except Exception as exc:
        log_ai_error(logger, AIErrorCategory.UNKNOWN, str(exc), exc=exc)
        raise LLMUnavailableError(f"LLM call failed: {exc}") from exc

    # ── Cache store ───────────────────────────────────────────────────────────
    if use_cache and result:
        _set_cached(key, result, cache_ttl)  # type: ignore[possibly-undefined]

    return result


def call_smart(system: str, user: str, **kwargs: Any) -> str:
    """
    Convenience wrapper for high-token calls (roadmaps, advice, synthesis).

    Sets conservative defaults: lower temperature for reliability, higher
    token budget for verbose outputs.
    """
    kwargs.setdefault("max_tokens", 2048)
    kwargs.setdefault("temp", 0.5)
    return call(system, user, smart=True, **kwargs)


# ── JSON output helpers ───────────────────────────────────────────────────────

def _strip_markdown_fences(text: str) -> str:
    """Remove ```json ... ``` fences that models frequently add."""
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```\s*$", "", text, flags=re.MULTILINE)
    return text.strip()


def _fix_trailing_commas(text: str) -> str:
    """Remove trailing commas before } or ] — common LLM mistake."""
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)
    return text


def call_json(
    system: str,
    user: str,
    *,
    temp: float = 0.3,
    max_tokens: int = 2048,
    use_cache: bool = True,
    cache_ttl: int = _DEFAULT_TTL,
    smart: bool = False,
) -> Any:
    """
    Call the LLM and return the response parsed as JSON.

    Applies several recovery strategies before raising:
      - Strip markdown fences
      - Seek the first ``{`` or ``[`` if preamble exists
      - Auto-close unclosed braces from truncated outputs
      - Remove trailing commas

    Args:
        system:     System prompt.
        user:       User prompt (should instruct the model to return only JSON).
        temp:       Lower temperature produces more reliable JSON (default 0.3).
        max_tokens: Token budget — ensure it's large enough for the expected payload.
        use_cache:  Cache the raw string response.
        cache_ttl:  Cache TTL in seconds.
        smart:      Route to the smart / high-capacity model.

    Returns:
        Parsed Python object (``dict`` or ``list``).

    Raises:
        :class:`~backend.core.exceptions.LLMParseError`:
            JSON could not be recovered after all repair attempts.
    """
    raw = call(
        system, user,
        temp=temp, max_tokens=max_tokens,
        use_cache=use_cache, cache_ttl=cache_ttl,
        smart=smart,
    )

    cleaned = _strip_markdown_fences(raw or "")

    # Skip any preamble before the first { or [
    first_brace = cleaned.find("{")
    first_bracket = cleaned.find("[")
    starts = [i for i in (first_brace, first_bracket) if i >= 0]
    if starts:
        cleaned = cleaned[min(starts):]

    # Attempt 1 — straight parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Attempt 2 — close unclosed braces (truncated outputs)
    open_braces = cleaned.count("{") - cleaned.count("}")
    if open_braces > 0:
        try:
            return json.loads(cleaned + "}" * open_braces)
        except json.JSONDecodeError:
            pass

    # Attempt 3 — trailing comma removal
    fixed = _fix_trailing_commas(cleaned)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError as exc:
        _token_counters["parse_errors"] += 1
        raise LLMParseError(
            f"Could not parse LLM JSON response after 3 repair attempts: {exc}",
            detail={"raw_preview": cleaned[:300]},
        ) from exc


def call_structured(
    system: str,
    user: str,
    schema: Type[T],
    *,
    temp: float = 0.3,
    max_tokens: int = 2048,
    fallback: Optional[T] = None,
    smart: bool = False,
) -> T:
    """
    Call the LLM and validate the JSON output against a Pydantic schema.

    Args:
        system:   System prompt.
        user:     User prompt.
        schema:   A Pydantic ``BaseModel`` class to validate against.
        temp:     Sampling temperature.
        max_tokens: Token budget.
        fallback: If provided, return this instance instead of raising on
                  validation failure.  Useful for non-critical features.
        smart:    Route to the smart model.

    Returns:
        A validated instance of *schema*.

    Raises:
        :class:`~backend.core.exceptions.LLMParseError`:
            Validation failed and no *fallback* was provided.

    Example::

        class ATSResult(BaseModel):
            overall_score: int
            missing_keywords: list[str]

        result = call_structured(system, user, schema=ATSResult)
        print(result.overall_score)
    """
    try:
        data = call_json(system, user, temp=temp, max_tokens=max_tokens, smart=smart)
        if not isinstance(data, dict):
            raise LLMParseError(
                f"Expected JSON object, got {type(data).__name__}",
                detail={"received": str(data)[:200]},
            )
        return schema(**data)
    except Exception as exc:
        if fallback is not None:
            logger.warning(
                "Structured call fell back to default for %s: %s",
                schema.__name__, exc,
            )
            _token_counters["fallbacks_triggered"] += 1
            return fallback
        raise


# ── Batch helpers ─────────────────────────────────────────────────────────────

def call_batch(
    prompts: List[Dict[str, str]],
    *,
    temp: float = 0.7,
    max_tokens: int = 1024,
    use_cache: bool = True,
    skip_errors: bool = True,
) -> List[str]:
    """
    Execute multiple system/user prompt pairs sequentially.

    Args:
        prompts:     List of dicts, each with ``"system"`` and ``"user"`` keys.
        temp:        Shared temperature for all calls.
        max_tokens:  Shared token budget.
        use_cache:   Apply caching to each individual call.
        skip_errors: If ``True`` (default), replace failed calls with ``""``
                     instead of raising.  Set ``False`` for strict pipelines.

    Returns:
        List of response strings in the same order as *prompts*.
        Failed items are ``""`` when *skip_errors* is ``True``.
    """
    results: List[str] = []
    for i, prompt in enumerate(prompts):
        try:
            results.append(
                call(
                    system=prompt["system"],
                    user=prompt["user"],
                    temp=temp,
                    max_tokens=max_tokens,
                    use_cache=use_cache,
                )
            )
        except Exception as exc:
            logger.warning("Batch item %d/%d failed: %s", i + 1, len(prompts), exc)
            if skip_errors:
                results.append("")
            else:
                raise
    return results
