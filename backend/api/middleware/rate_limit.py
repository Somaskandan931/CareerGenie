"""
Rate Limit Middleware
=====================
Simple in-memory rate limiting middleware.
"""

import time
from collections import defaultdict
from typing import Dict, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger("middleware.rate_limit")


class RateLimitStore:
    """In-memory rate limit storage."""
    
    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed under rate limit."""
        now = time.time()
        cutoff = now - window_seconds
        
        # Clean old entries
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
        
        if len(self._requests[key]) >= max_requests:
            return False
        
        self._requests[key].append(now)
        return True
    
    def get_remaining(self, key: str, max_requests: int, window_seconds: int) -> int:
        """Get remaining requests in current window."""
        now = time.time()
        cutoff = now - window_seconds
        current = len([t for t in self._requests[key] if t > cutoff])
        return max(0, max_requests - current)


# Global rate limit store
_rate_limit_store = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple rate limiting middleware.
    
    Limits requests per IP address to prevent abuse.
    Uses in-memory storage (use Redis for production).
    """
    
    def __init__(self, app, requests_per_minute: int = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or getattr(settings, "RATE_LIMIT_PER_MINUTE", 60)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        key = f"rate_limit:{client_ip}"
        
        if not _rate_limit_store.is_allowed(key, self.requests_per_minute, 60):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = _rate_limit_store.get_remaining(key, self.requests_per_minute, 60)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response