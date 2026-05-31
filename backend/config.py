"""
backend/config.py
=================
Compatibility shim — do not add new settings here.

All configuration lives in ``backend.core.config``.
This file exists only so that legacy code using
``from backend.config import settings`` continues to work.
"""
from backend.core.config import settings, get_settings, Settings  # noqa: F401

__all__ = ["settings", "get_settings", "Settings"]