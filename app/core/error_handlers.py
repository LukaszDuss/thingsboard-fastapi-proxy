"""
Custom error handlers for TB-API-SDK.

Provides sanitized error responses to prevent information leakage while
maintaining proper logging for debugging and monitoring.
"""
import logging
import time
from typing import Dict, Any, Optional

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import httpx

from app.core.config import settings
from app.schemas.responses import ErrorResponse, ErrorCode

logger = logging.getLogger(__name__)


def create_error_response(
    status_code: int,
    message: str,
    error_code: ErrorCode,
    details: Optional[Dict[str, Any]] = None
) -> ErrorResponse:
    """Create a standardized error response."""
    return ErrorResponse(
        status=status_code,
        message=message,
        error_code=error_code,
        timestamp=int(time.time() * 1000),
        details=details
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors with sanitized responses.
    
    Logs detailed validation errors for debugging while returning
    clean, non-revealing error messages to clients.
    """
    logger.warning(
        f"Validation error on {request.method} {request.url.path}: {exc.errors()}",
        extra={"request_id": getattr(request.state, "request_id", None)}
    )
    
    # In debug mode, return detailed validation errors
    if settings.DEBUG:
        error_response = create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="Request validation failed",
            error_code=ErrorCode.VALIDATION_ERROR,
            details={"validation_errors": exc.errors()}
        )
    else:
        # In production, return sanitized error
        error_response = create_error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="The request contains invalid data. Please check your input and try again.",
            error_code=ErrorCode.VALIDATION_ERROR
        )
    
    return JSONResponse(
        status_code=error_response.status,
        content=error_response.model_dump()
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with consistent error format.
    
    Ensures all HTTP errors follow the same response structure
    and logs security-relevant events.
    """
    # Log security-relevant HTTP errors
    if exc.status_code in [401, 403, 429]:
        logger.warning(
            f"Security event: {exc.status_code} on {request.method} {request.url.path} - {exc.detail}",
            extra={
                "client_ip": getattr(request.state, "client_ip", "unknown"),
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
    
    # Map status codes to error codes
    error_code_map = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.AUTHENTICATION_FAILED,
        403: ErrorCode.AUTHORIZATION_FAILED,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        502: ErrorCode.UPSTREAM_ERROR,
    }
    
    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)
    message = str(exc.detail) if settings.DEBUG else get_sanitized_message(exc.status_code)
    
    error_response = create_error_response(
        status_code=exc.status_code,
        message=message,
        error_code=error_code
    )
    
    # Add additional headers if present
    headers = getattr(exc, "headers", None)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(),
        headers=headers
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions with secure error responses.
    
    Logs full exception details for debugging while returning
    generic error messages to prevent information disclosure.
    """
    logger.error(
        f"Unexpected error on {request.method} {request.url.path}: {str(exc)}",
        exc_info=True,
        extra={
            "client_ip": getattr(request.state, "client_ip", "unknown"),
            "request_id": getattr(request.state, "request_id", None)
        }
    )
    
    # Never expose internal error details in production
    if settings.DEBUG:
        error_detail = f"{type(exc).__name__}: {str(exc)}"
    else:
        error_detail = "An internal server error occurred"
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": error_detail,
            "code": "INTERNAL_ERROR"
        }
    )


async def thingsboard_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle ThingsBoard-specific exceptions with proper error mapping.
    
    Converts upstream ThingsBoard errors into appropriate HTTP responses
    while preventing leakage of backend system details.
    """
    # Handle httpx errors from ThingsBoard requests
    if isinstance(exc, httpx.HTTPError):
        logger.error(
            f"ThingsBoard HTTP error on {request.method} {request.url.path}: {str(exc)}",
            extra={"tb_error": True}
        )
        
        status_code = getattr(exc.response, "status_code", 502) if hasattr(exc, "response") else 502
        
        # Map common ThingsBoard errors
        if status_code == 401:
            return JSONResponse(
                status_code=status.HTTP_502_BAD_GATEWAY,
                content={
                    "error": "Upstream Authentication Error",
                    "message": "Failed to authenticate with ThingsBoard backend",
                    "code": "TB_AUTH_ERROR"
                }
            )
        elif status_code == 404:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "error": "Resource Not Found",
                    "message": "The requested resource was not found",
                    "code": "RESOURCE_NOT_FOUND"
                }
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_502_BAD_GATEWAY,
                content={
                    "error": "Backend Service Error",
                    "message": "The backend service is temporarily unavailable",
                    "code": "BACKEND_ERROR"
                }
            )
    
    # Fall back to general exception handler
    return await general_exception_handler(request, exc)


def get_error_title(status_code: int) -> str:
    """Get a human-readable error title for HTTP status codes."""
    error_titles = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden", 
        404: "Not Found",
        405: "Method Not Allowed",
        422: "Unprocessable Entity",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable"
    }
    return error_titles.get(status_code, "Error")


def get_sanitized_message(status_code: int) -> str:
    """Get sanitized error messages that don't reveal system internals."""
    sanitized_messages = {
        400: "The request was invalid. Please check your input and try again.",
        401: "Authentication is required to access this resource.",
        403: "You don't have permission to access this resource.",
        404: "The requested resource was not found.",
        405: "This HTTP method is not allowed for this endpoint.",
        422: "The request data is invalid or incomplete.",
        429: "Too many requests. Please slow down and try again later.",
        500: "An internal server error occurred. Please try again later.",
        502: "The backend service is temporarily unavailable.",
        503: "The service is temporarily unavailable. Please try again later."
    }
    return sanitized_messages.get(status_code, "An error occurred. Please try again later.") 