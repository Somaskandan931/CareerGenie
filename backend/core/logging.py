"""
backend/core/logging.py
=======================
Centralized structured logging for Career Genie.

Features:
  - Per-request trace IDs via Python contextvars (async-safe)
  - ANSI color-coded console output for development
  - Structured AI error categories for easier log filtering
  - Clean suppression of noisy third-party loggers

Usage::

    from backend.core.logging import get_logger, set_trace_id, log_ai_error, AIErrorCategory

    logger = get_logger("ats_service")

    # Set trace ID at request boundary (done automatically by middleware)
    set_trace_id("abc12345")

    logger.info("Scoring resume")
    logger.warning("Score below threshold")
    log_ai_error(logger, AIErrorCategory.LLM_PARSE_FAIL, "Bad JSON from model", exc=e)
"""
from __future__ import annotations

import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Optional


# ── Per-request trace ID ──────────────────────────────────────────────────────
# ContextVar is async-safe: each asyncio Task gets its own copy.

_trace_id: ContextVar[str] = ContextVar("trace_id", default="")


def get_trace_id() -> str:
    """Return the current request's trace ID, or 'no-trace' if none is set."""
    return _trace_id.get() or "no-trace"


def set_trace_id(tid: Optional[str] = None) -> str:
    """
    Set a trace ID for the current async context.

    Generates a random 8-character ID when *tid* is None or empty.
    Called by ``TraceIDMiddleware`` at the start of every HTTP request.

    Returns the trace ID that was set.
    """
    resolved = (tid or "").strip() or str(uuid.uuid4())[:8]
    _trace_id.set(resolved)
    return resolved


# ── Custom formatter ──────────────────────────────────────────────────────────

class TraceFormatter(logging.Formatter):
    """
    Injects ``trace_id`` and optional ANSI color into every log line.

    Output format::

        [10:32:01] [INFO    ] [career_genie.ats] [trace:abc12345] Scoring resume
    """

    LEVEL_COLORS = {
        "DEBUG":    "\033[36m",   # cyan
        "INFO":     "\033[32m",   # green
        "WARNING":  "\033[33m",   # yellow
        "ERROR":    "\033[31m",   # red
        "CRITICAL": "\033[35m",   # magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_color: bool = True, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        trace = get_trace_id()
        record.trace_id = trace  # type: ignore[attr-defined]

        level = record.levelname
        color = self.LEVEL_COLORS.get(level, "") if self.use_color else ""
        reset = self.RESET if self.use_color else ""
        ts = self.formatTime(record, "%H:%M:%S")
        msg = record.getMessage()

        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)

        return (
            f"{color}[{ts}] [{level:<8}] [{record.name}] "
            f"[trace:{trace}]{reset} {msg}"
        )


# ── Root logger setup ─────────────────────────────────────────────────────────

#: Third-party loggers that are too noisy at INFO level.
_NOISY_LOGGERS = (
    "uvicorn.access",
    "httpx",
    "httpcore",
    "chromadb",
    "sentence_transformers",
    "transformers",
    "PIL",
    "urllib3",
    "multipart",
    "passlib",
)


def setup_logging(level: str = "INFO", use_color: bool = True) -> None:
    """
    Configure the root logger with structured, trace-ID-aware output.

    Call **once** at application startup — typically inside the FastAPI
    ``lifespan`` context manager or at the top of ``main.py``.

    Args:
        level:     Python log-level string: ``"DEBUG"``, ``"INFO"``,
                   ``"WARNING"``, ``"ERROR"``, or ``"CRITICAL"``.
        use_color: Set ``False`` for production log aggregators (Loki,
                   CloudWatch, etc.) that don't render ANSI codes.

    Example::

        # main.py
        from backend.core.logging import setup_logging
        setup_logging(level=settings.LOG_LEVEL, use_color=not settings.is_production)
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(numeric_level)
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    handler.setFormatter(TraceFormatter(use_color=use_color))
    root.addHandler(handler)

    # Suppress noisy third-party loggers
    for lib in _NOISY_LOGGERS:
        logging.getLogger(lib).setLevel(logging.WARNING)

    # Ensure our own namespace always respects the requested level
    logging.getLogger("career_genie").setLevel(numeric_level)


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger scoped under the ``career_genie`` namespace.

    Prefer this over ``logging.getLogger()`` directly so all app loggers
    share consistent naming and level control.

    Args:
        name: Short module/service name, e.g. ``"ats_service"``,
              ``"ai_pipeline"``, ``"middleware"``.

    Example::

        logger = get_logger("roadmap_service")
        logger.info("Generating roadmap for %s", target_role)
    """
    return logging.getLogger(f"career_genie.{name}")


# ── AI-specific error categories ──────────────────────────────────────────────

class AIErrorCategory:
    """
    String constants for structured AI error logging.

    Use with :func:`log_ai_error` to tag log entries with a machine-readable
    category — useful for dashboards, alerts, and log-based metrics.

    Example::

        log_ai_error(logger, AIErrorCategory.LLM_PARSE_FAIL, "Bad JSON", exc=e)
    """

    LLM_UNAVAILABLE = "llm_unavailable"
    LLM_RATE_LIMIT  = "llm_rate_limit"
    LLM_PARSE_FAIL  = "llm_parse_fail"
    EMBED_FAIL      = "embed_fail"
    SCRAPE_FAIL     = "scrape_fail"
    VECTOR_FAIL     = "vector_fail"
    UPLOAD_FAIL     = "upload_fail"
    VALIDATION_FAIL = "validation_fail"
    INJECTION_BLOCKED = "injection_blocked"
    CACHE_MISS      = "cache_miss"
    UNKNOWN         = "unknown"


def log_ai_error(
    logger: logging.Logger,
    category: str,
    message: str,
    exc: Optional[Exception] = None,
) -> None:
    """
    Log an AI pipeline error with a structured category tag.

    Automatically attaches the current trace ID and, if *exc* is provided,
    formats the full traceback into the log record.

    Args:
        logger:   The calling module's logger (from :func:`get_logger`).
        category: One of the :class:`AIErrorCategory` string constants.
        message:  Human-readable description of what went wrong.
        exc:      Optional exception — if supplied the traceback is attached.

    Example::

        try:
            result = call_llm(...)
        except json.JSONDecodeError as e:
            log_ai_error(logger, AIErrorCategory.LLM_PARSE_FAIL, "Model returned invalid JSON", exc=e)
            raise LLMParseError("Model returned invalid JSON") from e
    """
    logger.error(
        "[AI:%s] %s",
        category,
        message,
        exc_info=exc is not None,
        extra={
            "ai_error_category": category,
            "trace_id": get_trace_id(),
        },
    )
