from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.exceptions import RequestValidationError
import logging

from app.core.logging_config import configure_logging
from app.core.config import settings
from app.core.rate_limiter import rate_limit_middleware
from app.core.error_handlers import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)
from app.api.v1.routes import router as api_router

configure_logging()
logger = logging.getLogger(__name__)

# OpenAPI metadata following ThingsBoard standards [[memory:2952258]]
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="""
## ThingsBoard API SDK

A comprehensive REST API wrapper for ThingsBoard IoT platform, providing simplified access to device management, telemetry data operations, and asset management capabilities.

### Features

* **Device Management**: List, query, and manage IoT devices
* **Telemetry Operations**: Upload and retrieve time-series data
* **Attribute Management**: Handle device attributes (server-side and shared)
* **Asset Management**: Manage assets and asset profiles  
* **Bulk Operations**: Efficient batch processing for multiple devices
* **Entity Relationships**: Explore device and asset relationship graphs
* **Authentication**: Secure API access with key-based authentication
* **Rate Limiting**: Built-in protection against API abuse

### Authentication

All endpoints require authentication via API key passed in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key-here" https://api.example.com/api/v1/tb/devices
```

### Rate Limiting

API requests are limited to **{rate_limit_requests} requests per {rate_limit_window} seconds** per API key. 
Rate limit headers are included in responses:

* `X-RateLimit-Limit`: Maximum requests allowed  
* `X-RateLimit-Remaining`: Requests remaining in current window
* `X-RateLimit-Reset`: Time when rate limit resets

### Error Handling

All endpoints return consistent error responses with:

* **status**: HTTP status code
* **message**: Human-readable error description  
* **error_code**: Machine-readable error category
* **timestamp**: When the error occurred
* **details**: Additional context (when applicable)

### Data Formats

* **Timestamps**: Unix milliseconds (e.g., `1640995200000`)
* **Device IDs**: UUID format (e.g., `550e8400-e29b-41d4-a716-446655440000`)
* **Telemetry Values**: Numbers, strings, or booleans
* **Pagination**: Zero-based page indexing

### Base URL

**Production**: `https://api.yourdomain.com`  
**Development**: `http://localhost:8000`
    """.format(
        rate_limit_requests=settings.RATE_LIMIT_REQUESTS,
        rate_limit_window=settings.RATE_LIMIT_WINDOW
    ),
    docs_url="/docs" if settings.DEBUG else None,  # Disable docs in production
    redoc_url="/redoc" if settings.DEBUG else None,
    contact={
        "name": "TB-API-SDK Support",
        "url": "https://github.com/yourusername/TB-API-SKD",
        "email": "support@yourdomain.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {
            "url": "https://api.yourdomain.com",
            "description": "Production server"
        },
        {
            "url": "http://localhost:8000", 
            "description": "Development server"
        }
    ],
    tags_metadata=[
        {
            "name": "health",
            "description": "Service health and status endpoints"
        },
        {
            "name": "thingsboard",
            "description": "ThingsBoard proxy endpoints for device and telemetry management"
        },
        {
            "name": "devices", 
            "description": "Device management and discovery operations"
        },
        {
            "name": "telemetry",
            "description": "Time-series data upload and retrieval operations"
        },
        {
            "name": "attributes",
            "description": "Device attribute management (server-side and shared)"
        },
        {
            "name": "assets",
            "description": "Asset and asset profile management operations"
        },
        {
            "name": "relationships",
            "description": "Entity relationship and graph traversal operations"
        }
    ]
)

# Security: Trusted Host Middleware (prevent Host header attacks)
if settings.ALLOWED_HOSTS:
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=settings.ALLOWED_HOSTS
    )

# CORS setup - Fixed security issue
origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS] if settings.BACKEND_CORS_ORIGINS else []

# Security: Never allow wildcard origins with credentials
if not origins:
    logger.warning("No CORS origins configured. API will only accept same-origin requests.")
    origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Remove dangerous wildcard
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Be explicit about allowed methods
    allow_headers=["Authorization", "Content-Type", "X-Requested-With"],  # Be explicit about headers
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Rate Limiting Middleware
app.middleware("http")(rate_limit_middleware)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Prevent XSS attacks
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # HTTPS enforcement in production
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Prevent referrer leaks
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Content Security Policy - Allow Swagger UI resources
    csp_directives = [
        "default-src 'self'",  # Only same-origin resources by default
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",  # Allow Swagger UI JS + inline scripts
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",   # Allow Swagger UI CSS + inline styles  
        "img-src 'self' data: https://fastapi.tiangolo.com https://cdn.jsdelivr.net",  # Allow images from FastAPI + CDN
        "font-src 'self' https://cdn.jsdelivr.net",  # Allow fonts from CDN
        "connect-src 'self'"  # Only same-origin AJAX/WebSocket connections
    ]
    response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
    
    return response

# Register error handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """Root endpoint just returns service name."""
    return {"service": settings.PROJECT_NAME, "version": settings.VERSION} 