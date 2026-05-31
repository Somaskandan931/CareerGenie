"""
CORS Middleware Configuration
=============================
Secure CORS configuration for Career Genie API.
"""

from typing import List

from backend.core.config import settings


class CORSMiddlewareConfig:
    """
    Centralized CORS configuration.
    
    Security notes:
    - allow_credentials=False unless using cookie-based auth
    - Explicit origins preferred over wildcards in production
    - allow_origin_regex used for dynamic origin reflection
    """
    
    @staticmethod
    def get_config() -> dict:
        """Get CORS middleware configuration."""
        return {
            # Reflect actual origin - compatible with allow_credentials
            "allow_origin_regex": r".*",
            # Keep False unless switching to cookie-based auth
            "allow_credentials": False,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }
    
    @staticmethod
    def get_allowed_origins() -> List[str]:
        """Get list of allowed origins based on deployment mode."""
        origins = []
        
        # Parse configured origins
        for origin in settings.CORS_ORIGINS:
            origin = origin.strip()
            if origin:
                origins.append(origin)
        
        # Add ngrok URL if provided
        if settings.NGROK_URL:
            origins.append(settings.NGROK_URL)
        
        return origins
    
    @staticmethod
    def is_allowed_origin(origin: str) -> bool:
        """Check if an origin is allowed."""
        if not origin:
            return False
        
        # Check explicit origins
        if origin in CORSMiddlewareConfig.get_allowed_origins():
            return True
        
        # Allow common deployment platforms
        allowed_suffixes = (
            ".netlify.app",
            ".vercel.app",
            ".ngrok-free.app",
            ".ngrok.io",
            ".onrender.com",
        )
        for suffix in allowed_suffixes:
            if origin.endswith(suffix):
                return True
        
        return False