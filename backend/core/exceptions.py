"""
backend/core/exceptions.py
==========================
Unified exception hierarchy for Career Genie.

All services raise from these — never raw Exception.
FastAPI exception handlers in main.py convert them to HTTP responses.

Hierarchy:
  CareerGenieError
  ├── ValidationError
  │   ├── UploadError
  │   │   ├── FileTooLargeError
  │   │   └── UnsupportedFileTypeError
  │   └── PromptInjectionError
  ├── AIError
  │   ├── LLMUnavailableError
  │   ├── LLMRateLimitError
  │   ├── LLMParseError
  │   └── EmbeddingError
  ├── StorageError
  │   └── VectorStoreError
  ├── JobScraperError
  ├── NotFoundError
  │   ├── MentorNotFoundError
  │   ├── ResumeNotFoundError
  │   └── JobNotFoundError
  ├── AuthError
  │   └── TokenExpiredError
  ├── PermissionDeniedError   ← NOTE: NOT named PermissionError (shadows builtin OSError)
  └── RateLimitError

Usage::

    from backend.core.exceptions import LLMUnavailableError, UploadError

    raise UploadError("File exceeds 10 MB limit", error_code="file_too_large")
"""
from __future__ import annotations

from typing import Any, Dict, Optional


# ── Base ──────────────────────────────────────────────────────────────────────

class CareerGenieError(Exception):
    """
    Root exception for all Career Genie errors.

    Every subclass *must* declare ``status_code`` and ``error_code`` so the
    FastAPI exception handler can convert it to a consistent HTTP response
    without any isinstance() sprawl.
    """

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(
        self,
        message: str,
        detail: Optional[Any] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail
        # Allow caller to override error_code for one-off variants
        if error_code is not None:
            self.error_code = error_code

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to the standard API error envelope."""
        return {
            "error": self.error_code,
            "message": self.message,
            "detail": self.detail,
        }

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"error_code={self.error_code!r}, "
            f"status_code={self.status_code}, "
            f"message={self.message!r})"
        )


# ── Validation ────────────────────────────────────────────────────────────────

class ValidationError(CareerGenieError):
    """Generic request / input validation failure (HTTP 422)."""
    status_code = 422
    error_code = "validation_error"


class UploadError(CareerGenieError):
    """Raised when a file upload violates policy (HTTP 400)."""
    status_code = 400
    error_code = "upload_error"


class FileTooLargeError(UploadError):
    """File exceeds the configured MAX_UPLOAD_SIZE_MB limit."""
    error_code = "file_too_large"


class UnsupportedFileTypeError(UploadError):
    """File MIME type or extension is not in ALLOWED_UPLOAD_EXTENSIONS."""
    error_code = "unsupported_file_type"


class PromptInjectionError(ValidationError):
    """
    Raised when prompt-injection patterns are detected in user-supplied content
    (e.g. a resume that contains 'ignore previous instructions').
    Treat as a validation error — log it, reject the request, never propagate
    the malicious content to the LLM.
    """
    error_code = "prompt_injection_detected"


# ── AI / LLM ─────────────────────────────────────────────────────────────────

class AIError(CareerGenieError):
    """Base class for all AI / LLM pipeline errors (HTTP 503)."""
    status_code = 503
    error_code = "ai_error"


class LLMUnavailableError(AIError):
    """
    All configured LLM providers (Ollama, Groq, Anthropic) are unreachable
    or returned non-retryable errors.
    """
    error_code = "llm_unavailable"


class LLMRateLimitError(AIError):
    """Provider-side rate limit hit (HTTP 429)."""
    status_code = 429
    error_code = "llm_rate_limit"


class LLMParseError(AIError):
    """
    LLM returned a response that could not be parsed into the expected
    JSON / Pydantic schema.  Signals a prompt or model quality issue.
    """
    status_code = 500
    error_code = "llm_parse_error"


class EmbeddingError(AIError):
    """Embedding model call failed (local or remote)."""
    error_code = "embedding_error"


# ── Data / Storage ────────────────────────────────────────────────────────────

class StorageError(CareerGenieError):
    """Generic persistence / IO error (HTTP 500)."""
    status_code = 500
    error_code = "storage_error"


class VectorStoreError(StorageError):
    """ChromaDB / PgVector operation failed."""
    error_code = "vector_store_error"


class DatabaseError(StorageError):
    """PostgreSQL / ORM operation failed."""
    error_code = "database_error"


class CacheError(StorageError):
    """Redis / in-memory cache operation failed (non-fatal in most cases)."""
    error_code = "cache_error"


# ── External services ─────────────────────────────────────────────────────────

class JobScraperError(CareerGenieError):
    """Job scraping / SERP API call failed (HTTP 503)."""
    status_code = 503
    error_code = "scraper_error"


# ── Resource not found ────────────────────────────────────────────────────────

class NotFoundError(CareerGenieError):
    """Requested resource does not exist (HTTP 404)."""
    status_code = 404
    error_code = "not_found"


class MentorNotFoundError(NotFoundError):
    """No mentor matched the requested criteria."""
    error_code = "mentor_not_found"


class ResumeNotFoundError(NotFoundError):
    """No resume on record for the given user / session."""
    error_code = "resume_not_found"


class JobNotFoundError(NotFoundError):
    """Requested job posting no longer exists."""
    error_code = "job_not_found"


# ── Auth / Permission ─────────────────────────────────────────────────────────

class AuthError(CareerGenieError):
    """Authentication failed — missing or invalid credentials (HTTP 401)."""
    status_code = 401
    error_code = "auth_error"


class TokenExpiredError(AuthError):
    """JWT / session token has expired."""
    error_code = "token_expired"


class PermissionDeniedError(CareerGenieError):
    """
    Authenticated user lacks permission to perform this action (HTTP 403).

    ⚠️  This is intentionally named ``PermissionDeniedError``, NOT
    ``PermissionError``.  ``PermissionError`` is a Python builtin (subclass of
    ``OSError``) — shadowing it causes extremely confusing stack traces when the
    OS raises file-access errors that then match an except PermissionError
    clause intended for API auth checks.
    """
    status_code = 403
    error_code = "permission_denied"


# ── Rate Limiting ─────────────────────────────────────────────────────────────

class RateLimitError(CareerGenieError):
    """
    Application-level rate limit exceeded (HTTP 429).
    Distinct from ``LLMRateLimitError`` which originates from the provider.
    """
    status_code = 429
    error_code = "rate_limit_exceeded"


# ── Background / Queue ────────────────────────────────────────────────────────

class TaskQueueError(CareerGenieError):
    """
    Background task could not be enqueued (Celery / BackgroundTasks).
    Used by the worker layer — Phase 2 addition.
    """
    status_code = 503
    error_code = "task_queue_error"
