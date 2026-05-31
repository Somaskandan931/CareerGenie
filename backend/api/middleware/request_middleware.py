"""
backend/api/middleware/request_middleware.py
============================================
FastAPI middleware stack for Career Genie.

Register in main.py in this order (last-added = outermost wrapper):

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, limit=settings.RATE_LIMIT_PER_MINUTE)
    app.add_middleware(RequestLogMiddleware)
    app.add_middleware(TraceIDMiddleware)

Middlewares (innermost → outermost):
  1. TraceIDMiddleware       — inject trace ID into every request context
  2. RequestLogMiddleware    — log every request / response pair with timing
  3. RateLimitMiddleware     — sliding-window IP rate limiting (in-memory)
  4. SecurityHeadersMiddleware — add security headers to all responses

⚠️  The in-memory rate limiter is suitable for single-process development.
    For multi-worker / multi-instance production deployments, replace it
    with a Redis-backed implementation (Phase 2).
"""
from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable, Dict, List

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from backend.core.logging import get_logger, set_trace_id

logger = get_logger("middleware")


# ── 1. Trace ID ────────────────────────────────────────────────────────────────

class TraceIDMiddleware(BaseHTTPMiddleware):
    """
    Inject a trace ID into every request's async context.

    Reads ``X-Trace-ID`` from the request headers if present (useful for
    upstream proxies or client-side correlation).  Generates a random 8-char
    ID otherwise.

    Always echoes the trace ID back in the response via ``X-Trace-ID``.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming = request.headers.get("X-Trace-ID", "").strip()
        tid = set_trace_id(incoming or None)

        response = await call_next(request)
        response.headers["X-Trace-ID"] = tid
        return response


# ── 2. Request Logging ────────────────────────────────────────────────────────

class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    Log every HTTP request and its response with wall-clock timing.

    - INFO  for 2xx / 3xx responses
    - WARNING for 4xx
    - ERROR  for 5xx

    Skips noisy health-check and static metadata endpoints.
    """

    #: Paths that produce no log output to reduce noise.
    SKIP_PATHS: frozenset = frozenset({
        "/",
        "/config",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/favicon.ico",
    })

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:                     # pragma: no cover
            logger.error(
                "Unhandled exception on %s %s: %s",
                request.method, request.url.path, exc,
                exc_info=True,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 1)
        status = response.status_code

        if status >= 500:
            log_fn = logger.error
        elif status >= 400:
            log_fn = logger.warning
        else:
            log_fn = logger.info

        log_fn(
            "%s %s → %d (%s ms)",
            request.method,
            request.url.path,
            status,
            duration_ms,
        )
        return response


# ── 3. Rate Limiter ───────────────────────────────────────────────────────────

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple sliding-window rate limiter per client IP.

    Tracks request timestamps per IP in a dict.  On each request it:
      1. Prunes timestamps older than *window* seconds.
      2. Rejects (HTTP 429) if the remaining count ≥ *limit*.
      3. Appends the current timestamp and continues.

    **Production note**: This is in-memory and per-process.  It will not
    enforce limits across multiple Uvicorn workers.  Replace with a Redis
    sliding-window counter in Phase 2.

    Args:
        limit:  Maximum requests allowed per *window* per IP.
        window: Sliding-window duration in seconds (default 60).
        skip_paths: Paths exempted from rate limiting (e.g. health checks).
    """

    DEFAULT_SKIP_PATHS: frozenset = frozenset({"/", "/health", "/docs", "/redoc", "/openapi.json"})

    def __init__(
        self,
        app: ASGIApp,
        limit: int = 60,
        window: int = 60,
        skip_paths: frozenset = DEFAULT_SKIP_PATHS,
    ) -> None:
        super().__init__(app)
        self.limit = limit
        self.window = window
        self.skip_paths = skip_paths
        # ip → sorted list of request timestamps
        self._buckets: Dict[str, List[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP, respecting X-Forwarded-For from proxies."""
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.skip_paths:
            return await call_next(request)

        ip = self._get_client_ip(request)
        now = time.time()
        cutoff = now - self.window

        # Slide the window
        bucket = self._buckets[ip]
        self._buckets[ip] = [t for t in bucket if t > cutoff]
        bucket = self._buckets[ip]

        if len(bucket) >= self.limit:
            logger.warning(
                "[RateLimit] %s blocked — %d requests in %ds window",
                ip, len(bucket), self.window,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": (
                        f"Too many requests. Limit: {self.limit} per {self.window}s. "
                        "Please slow down."
                    ),
                },
                headers={"Retry-After": str(self.window)},
            )

        self._buckets[ip].append(now)
        return await call_next(request)

    def get_stats(self) -> Dict[str, int]:
        """Return a snapshot of current bucket sizes (useful for debugging)."""
        now = time.time()
        cutoff = now - self.window
        active = {
            ip: len([t for t in ts if t > cutoff])
            for ip, ts in self._buckets.items()
        }
        return {"tracked_ips": len(active), "total_recent_requests": sum(active.values())}


# ── 4. Security Headers ───────────────────────────────────────────────────────

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add standard security headers to every HTTP response.

    Headers set:
      - ``X-Content-Type-Options: nosniff``        — prevent MIME sniffing
      - ``X-Frame-Options: DENY``                  — prevent clickjacking
      - ``X-XSS-Protection: 1; mode=block``        — legacy XSS filter
      - ``Referrer-Policy``                        — control referrer leakage
      - ``Permissions-Policy``                     — lock down browser APIs
      - ``Content-Security-Policy``                — restrict resource origins

    **Note**: HSTS (``Strict-Transport-Security``) is intentionally omitted
    here — it should be set by your reverse proxy (Nginx / Caddy) because
    it only makes sense over HTTPS and must survive proxy SSL termination.
    """

    _HEADERS = {
        "X-Content-Type-Options":  "nosniff",
        "X-Frame-Options":          "DENY",
        "X-XSS-Protection":         "1; mode=block",
        "Referrer-Policy":          "strict-origin-when-cross-origin",
        "Permissions-Policy":       "geolocation=(), microphone=(), camera=()",
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "   # tighten after adding CSP nonces
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self' http://localhost:11434"  # allow Ollama in dev
        ),
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers.update(self._HEADERS)
        return response


# ── Exception handler helper ──────────────────────────────────────────────────

def build_exception_handlers() -> dict:
    """
    Return a dict of exception handlers for ``app = FastAPI(exception_handlers=...)``.

    Converts :class:`~backend.core.exceptions.CareerGenieError` subclasses into
    consistent JSON error responses.

    Usage in main.py::

        from backend.api.middleware.request_middleware import build_exception_handlers
        app = FastAPI(exception_handlers=build_exception_handlers())
    """
    from backend.core.exceptions import CareerGenieError  # noqa: PLC0415

    async def career_genie_error_handler(
        request: Request, exc: CareerGenieError
    ) -> JSONResponse:
        logger.error(
            "CareerGenieError [%s]: %s",
            exc.error_code, exc.message,
            extra={"status_code": exc.status_code},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.to_dict(),
        )

    async def unhandled_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "An unexpected error occurred. Please try again.",
                "detail": None,
            },
        )

    return {
        CareerGenieError: career_genie_error_handler,
        Exception: unhandled_error_handler,
    }
