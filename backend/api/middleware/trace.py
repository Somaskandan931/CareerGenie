"""
Trace ID Middleware
===================
Adds unique trace ID to each request for debugging and logging.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.core.logging import set_trace_id, get_trace_id


class TraceIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware that generates a unique trace ID for each request.
    
    The trace ID is:
    - Stored in the request context for logging
    - Returned in the response headers for debugging
    - Used to correlate logs across the request lifecycle
    """
    
    HEADER_NAME = "X-Trace-ID"
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Get trace ID from header or generate new one
        trace_id = request.headers.get(self.HEADER_NAME) or set_trace_id()
        
        # Set trace ID in context for logging
        set_trace_id(trace_id)
        
        # Process request
        response = await call_next(request)
        
        # Add trace ID to response headers
        response.headers[self.HEADER_NAME] = trace_id
        
        return response