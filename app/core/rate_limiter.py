"""
Rate limiting utilities for TB-API-SDK.

Implements in-memory rate limiting with configurable windows and limits.
For production use, consider Redis-backed rate limiting for scalability.
"""
import time
import logging
from typing import Dict, Tuple
from collections import defaultdict, deque
from functools import wraps

from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse

from app.core.config import settings

logger = logging.getLogger(__name__)


class InMemoryRateLimiter:
    """
    Simple in-memory rate limiter using sliding window approach.
    
    For production deployments with multiple instances, consider using
    Redis-backed rate limiting for consistent limits across instances.
    """
    
    def __init__(self):
        # Store request timestamps per client IP
        self.clients: Dict[str, deque] = defaultdict(deque)
        self.last_cleanup = time.time()
    
    def _cleanup_old_entries(self):
        """Remove old entries to prevent memory leaks."""
        current_time = time.time()
        
        # Only cleanup every 60 seconds to avoid performance impact
        if current_time - self.last_cleanup < 60:
            return
            
        cutoff_time = current_time - settings.RATE_LIMIT_WINDOW
        
        for client_ip in list(self.clients.keys()):
            client_requests = self.clients[client_ip]
            
            # Remove old requests
            while client_requests and client_requests[0] < cutoff_time:
                client_requests.popleft()
            
            # Remove empty entries
            if not client_requests:
                del self.clients[client_ip]
        
        self.last_cleanup = current_time
    
    def is_allowed(self, client_ip: str) -> Tuple[bool, int, int]:
        """
        Check if request is allowed for the given client IP.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Tuple of (is_allowed, requests_made, time_until_reset)
        """
        current_time = time.time()
        self._cleanup_old_entries()
        
        client_requests = self.clients[client_ip]
        window_start = current_time - settings.RATE_LIMIT_WINDOW
        
        # Remove requests outside the current window
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()
        
        requests_in_window = len(client_requests)
        
        if requests_in_window >= settings.RATE_LIMIT_REQUESTS:
            # Rate limit exceeded
            oldest_request = client_requests[0] if client_requests else current_time
            time_until_reset = int(oldest_request + settings.RATE_LIMIT_WINDOW - current_time)
            return False, requests_in_window, max(0, time_until_reset)
        
        # Allow the request and record it
        client_requests.append(current_time)
        return True, requests_in_window + 1, settings.RATE_LIMIT_WINDOW


# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request.
    
    Handles X-Forwarded-For header for proxy scenarios.
    """
    # Check for forwarded IP first (for load balancers/proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # Fall back to direct client IP
    client_host = request.client.host if request.client else "unknown"
    return client_host


async def rate_limit_middleware(request: Request, call_next):
    """
    Middleware to apply rate limiting to all requests.
    
    Returns 429 Too Many Requests if rate limit is exceeded.
    """
    # Skip rate limiting for health checks and root endpoint
    if request.url.path in ["/", "/api/v1/health"]:
        response = await call_next(request)
        return response
    
    client_ip = get_client_ip(request)
    is_allowed, requests_made, time_until_reset = rate_limiter.is_allowed(client_ip)
    
    if not is_allowed:
        logger.warning(
            f"Rate limit exceeded for IP {client_ip}: {requests_made} requests "
            f"in {settings.RATE_LIMIT_WINDOW}s window"
        )
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "detail": f"Maximum {settings.RATE_LIMIT_REQUESTS} requests per "
                         f"{settings.RATE_LIMIT_WINDOW} seconds allowed",
                "retry_after": time_until_reset
            },
            headers={
                "Retry-After": str(time_until_reset),
                "X-RateLimit-Limit": str(settings.RATE_LIMIT_REQUESTS),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + time_until_reset)
            }
        )
    
    # Process the request
    response = await call_next(request)
    
    # Add rate limit headers to successful responses
    remaining = max(0, settings.RATE_LIMIT_REQUESTS - requests_made)
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + settings.RATE_LIMIT_WINDOW)
    
    return response 