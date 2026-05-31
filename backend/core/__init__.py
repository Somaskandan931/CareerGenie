"""
Career Genie Core Module
========================
Central configuration, exceptions, logging, and AI pipeline.
"""

from backend.core.config import settings
from backend.core.exceptions import (
    AIError,
    AIErrorCategory,
    LLMParseError,
    LLMUnavailableError,
    ValidationError,
    AuthenticationError,
    NotFoundError,
)
from backend.core.logging import get_logger, log_ai_error, setup_logging

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