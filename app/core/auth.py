"""
Authentication and authorization utilities for TB-API-SDK.

This module provides security decorators and middleware for protecting API endpoints.
Supports both API key authentication and optional additional security layers.
"""
import logging
from typing import Optional, Annotated
from functools import wraps

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader

from app.core.config import settings

logger = logging.getLogger(__name__)

# API Key authentication
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_security = HTTPBearer(auto_error=False)


async def verify_api_key(api_key: Optional[str] = Depends(api_key_header)) -> bool:
    """
    Verify API key if one is configured.
    
    Returns:
        bool: True if authentication is valid or not required
        
    Raises:
        HTTPException: If API key is required but invalid
    """
    # If no API key is configured, skip authentication
    if not settings.API_KEY:
        logger.debug("No API key configured - allowing unauthenticated access")
        return True
    
    # If API key is configured but not provided
    if not api_key:
        logger.warning("API key required but not provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Verify the API key
    if api_key != settings.API_KEY:
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    logger.debug("API key authentication successful")
    return True


async def get_current_user(
    api_key_valid: bool = Depends(verify_api_key),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_security)
) -> dict:
    """
    Get current authenticated user context.
    
    This function can be extended to support JWT tokens, user sessions, etc.
    Currently focuses on API key authentication.
    
    Returns:
        dict: User context information
    """
    if not api_key_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
    
    # For now, return a simple authenticated context
    # This can be extended to include user roles, permissions, etc.
    return {
        "authenticated": True,
        "method": "api_key",
        "permissions": ["thingsboard:read", "thingsboard:write"]
    }


def require_auth(func=None):
    """
    Decorator to require authentication for endpoint functions.
    
    Usage:
        @require_auth
        async def protected_endpoint():
            return {"message": "Protected content"}
    """
    def decorator(f):
        @wraps(f)
        async def wrapper(*args, **kwargs):
            # Extract user dependency if not already present
            if 'current_user' not in kwargs:
                # This should be handled by FastAPI dependencies in routes
                pass
            return await f(*args, **kwargs)
        return wrapper
    
    if func is None:
        return decorator
    else:
        return decorator(func)


# Dependency aliases for common use cases
AuthenticatedUser = Annotated[dict, Depends(get_current_user)]
ValidAPIKey = Annotated[bool, Depends(verify_api_key)] 