from fastapi import APIRouter, status
from app.schemas.responses import HealthCheckResponse
from app.core.config import settings
import time

router = APIRouter()


@router.get(
    "/health", 
    status_code=status.HTTP_200_OK,
    response_model=HealthCheckResponse,
    tags=["health"],
    summary="Health Check",
    description="""
    Simple health check endpoint for service monitoring and load balancer probes.
    
    Returns service status, name, version, and current timestamp.
    This endpoint does not require authentication and is always available.
    
    **Use Cases:**
    - Load balancer health checks
    - Service monitoring and alerting
    - Deployment verification
    - Container orchestration health probes
    """,
    responses={
        200: {
            "description": "Service is healthy and operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "timestamp": 1640995200000,
                        "service": "TB-API-SKD",
                        "version": "0.1.0"
                    }
                }
            }
        }
    }
)
async def health_check() -> HealthCheckResponse:
    """
    Simple liveness probe for service health monitoring.
    
    Returns basic service information and current timestamp.
    Always returns 200 OK if the service is running.
    """
    return HealthCheckResponse(
        status="success",
        timestamp=int(time.time() * 1000),
        service=settings.PROJECT_NAME,
        version=settings.VERSION
    ) 