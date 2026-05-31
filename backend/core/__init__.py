"""
Career Genie Core Module
========================
Central configuration, exceptions, logging, and AI pipeline.
"""

from backend.core.config import settings
from backend.core.exceptions import (
    AIError,
    LLMParseError,
    LLMUnavailableError,
    ValidationError,
    AuthError as AuthenticationError,
    NotFoundError,
)

# AIErrorCategory must come from logging (has INJECTION_BLOCKED, LLM_UNAVAILABLE, etc.)
# The one in exceptions.py is a legacy shim with different constant names.
from backend.core.logging import (
    get_logger,
    log_ai_error,
    setup_logging,
    AIErrorCategory,
)

__all__ = [
    "settings",
    "AIError",
    "AIErrorCategory",
    "LLMParseError",
    "LLMUnavailableError",
    "ValidationError",
    "AuthenticationError",
    "NotFoundError",
    "get_logger",
    "log_ai_error",
    "setup_logging",
]
