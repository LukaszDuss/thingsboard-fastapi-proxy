"""
Standard response schemas for all API endpoints.

These models ensure consistent response formats across the API,
with detailed examples and comprehensive error handling.
"""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class ErrorCode(str, Enum):
    """Standard error codes used across the API."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class ErrorResponse(BaseModel):
    """
    Standard error response structure used across all endpoints.
    
    Provides consistent error information including status codes,
    descriptive messages, and error categorization.
    """
    status: int = Field(..., description="HTTP status code", example=400)
    message: str = Field(..., description="Human-readable error description", example="Invalid request parameters")
    error_code: ErrorCode = Field(..., description="Machine-readable error category")
    timestamp: int = Field(..., description="Unix timestamp when error occurred", example=1640995200000)
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context", example={"field": "device_id", "issue": "invalid UUID format"})
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": 400,
                    "message": "Invalid device ID format",
                    "error_code": "VALIDATION_ERROR", 
                    "timestamp": 1640995200000,
                    "details": {"field": "device_id", "expected": "UUID", "received": "not-a-uuid"}
                },
                {
                    "status": 502,
                    "message": "ThingsBoard authentication failed",
                    "error_code": "UPSTREAM_ERROR",
                    "timestamp": 1640995200000
                }
            ]
        }
    }


class SuccessResponse(BaseModel):
    """Base success response with common fields."""
    status: str = Field(default="success", description="Response status indicator")
    timestamp: int = Field(..., description="Unix timestamp when response was generated", example=1640995200000)


class PaginationMetadata(BaseModel):
    """Pagination information for list endpoints."""
    page: int = Field(..., description="Current page number (0-based)", example=0)
    page_size: int = Field(..., description="Number of items per page", example=100) 
    total_pages: int = Field(..., description="Total number of pages available", example=5)
    total_elements: int = Field(..., description="Total number of items across all pages", example=487)
    has_next: bool = Field(..., description="Whether more pages are available", example=True)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "page": 0,
                "page_size": 100,
                "total_pages": 5,
                "total_elements": 487,
                "has_next": True
            }
        }
    }


class TelemetryUploadResponse(SuccessResponse):
    """Response for successful telemetry data upload."""
    device_id: str = Field(..., description="Target device UUID", example="550e8400-e29b-41d4-a716-446655440000")
    keys_uploaded: List[str] = Field(..., description="List of telemetry keys that were uploaded", example=["temperature", "humidity", "pressure"])
    total_data_points: int = Field(..., description="Total number of data points uploaded", example=156)
    message: str = Field(..., description="Success confirmation message", example="Successfully uploaded 156 data points for 3 telemetry keys")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "timestamp": 1640995200000,
                "device_id": "550e8400-e29b-41d4-a716-446655440000",
                "keys_uploaded": ["temperature", "humidity", "pressure"],
                "total_data_points": 156,
                "message": "Successfully uploaded 156 data points for 3 telemetry keys"
            }
        }
    }


class AttributesUploadResponse(SuccessResponse):
    """Response for successful attributes upload."""
    device_id: str = Field(..., description="Target device UUID", example="550e8400-e29b-41d4-a716-446655440000")
    scope: str = Field(..., description="Attribute scope (SERVER_SCOPE or SHARED_SCOPE)", example="SERVER_SCOPE")
    attributes_uploaded: List[str] = Field(..., description="List of attribute keys that were uploaded", example=["serialNumber", "firmwareVersion", "model"])
    count: int = Field(..., description="Number of attributes uploaded", example=3)
    message: str = Field(..., description="Success confirmation message", example="Successfully uploaded 3 server-side attributes")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success", 
                "timestamp": 1640995200000,
                "device_id": "550e8400-e29b-41d4-a716-446655440000",
                "scope": "SERVER_SCOPE",
                "attributes_uploaded": ["serialNumber", "firmwareVersion", "model"],
                "count": 3,
                "message": "Successfully uploaded 3 server-side attributes"
            }
        }
    }


class TelemetryQueryMetadata(BaseModel):
    """Metadata for telemetry query responses."""
    total_points: int = Field(..., description="Total number of data points returned", example=156)
    keys_found: List[str] = Field(..., description="Telemetry keys that had data", example=["temperature", "humidity"])
    keys_missing: List[str] = Field(..., description="Requested keys with no data", example=["pressure"])
    time_range: Dict[str, Union[int, float]] = Field(..., description="Query time range information", example={
        "start": 1640908800000,
        "end": 1640995200000, 
        "duration_hours": 24.0
    })


class TelemetryQueryResponse(SuccessResponse):
    """Response for telemetry data queries."""
    device_id: str = Field(..., description="Target device UUID", example="550e8400-e29b-41d4-a716-446655440000")
    query: Dict[str, Any] = Field(..., description="Original query parameters", example={
        "keys": ["temperature", "humidity"],
        "start_ts": 1640908800000,
        "end_ts": 1640995200000,
        "limit": 200
    })
    data: Dict[str, List[Dict[str, Union[int, float, str, bool]]]] = Field(..., description="Telemetry data by key", example={
        "temperature": [
            {"ts": 1640995200000, "value": 23.5},
            {"ts": 1640995100000, "value": 23.3}
        ]
    })
    metadata: TelemetryQueryMetadata = Field(..., description="Query result metadata")


class BulkUploadSummary(BaseModel):
    """Summary statistics for bulk upload operations."""
    total_devices: int = Field(..., description="Total number of devices in request", example=10)
    successful_devices: int = Field(..., description="Number of devices successfully processed", example=8)
    failed_devices: int = Field(..., description="Number of devices that failed", example=2)
    total_data_points: int = Field(..., description="Total data points uploaded across all devices", example=1542)


class BulkUploadDeviceResult(BaseModel):
    """Result for individual device in bulk upload."""
    status: str = Field(..., description="Upload status for this device", example="success")
    keys_uploaded: Optional[List[str]] = Field(None, description="Keys uploaded for successful devices", example=["temperature", "humidity"])
    data_points: Optional[int] = Field(None, description="Data points uploaded for successful devices", example=156)
    error: Optional[str] = Field(None, description="Error message for failed devices", example="Device not found")


class BulkUploadResponse(SuccessResponse):
    """Response for bulk telemetry upload operations."""
    summary: BulkUploadSummary = Field(..., description="Upload operation summary")
    results: Dict[str, BulkUploadDeviceResult] = Field(..., description="Results per device")
    message: str = Field(..., description="Overall operation status", example="Bulk upload completed: 8/10 devices successful")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "timestamp": 1640995200000,
                "summary": {
                    "total_devices": 2,
                    "successful_devices": 2,
                    "failed_devices": 0,
                    "total_data_points": 300
                },
                "results": {
                    "device1-uuid": {
                        "status": "success",
                        "keys_uploaded": ["temperature", "humidity"],
                        "data_points": 200
                    },
                    "device2-uuid": {
                        "status": "success", 
                        "keys_uploaded": ["pressure"],
                        "data_points": 100
                    }
                },
                "message": "Bulk upload completed: 2/2 devices successful"
            }
        }
    }


class DeviceListResponse(SuccessResponse):
    """Response for device listing endpoint."""
    data: List[Dict[str, Any]] = Field(..., description="Array of device objects")
    pagination: PaginationMetadata = Field(..., description="Pagination information")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "timestamp": 1640995200000,
                "data": [
                    {
                        "id": {"id": "550e8400-e29b-41d4-a716-446655440000", "entityType": "DEVICE"},
                        "name": "Temperature Sensor 001",
                        "type": "TemperatureSensor",
                        "label": "Building A - Floor 2",
                        "deviceProfileId": {"id": "profile-uuid", "entityType": "DEVICE_PROFILE"}
                    }
                ],
                "pagination": {
                    "page": 0,
                    "page_size": 100,
                    "total_pages": 1,
                    "total_elements": 15,
                    "has_next": False
                }
            }
        }
    }


class HealthCheckResponse(SuccessResponse):
    """Health check endpoint response."""  
    service: str = Field(..., description="Service name", example="TB-API-SKD")
    version: str = Field(..., description="Service version", example="0.1.0")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "timestamp": 1640995200000,
                "service": "TB-API-SKD",
                "version": "0.1.0"
            }
        }
    }


class TelemetryLatestResponse(SuccessResponse):
    """Response for latest telemetry values."""
    device_id: str = Field(..., description="Target device UUID", example="550e8400-e29b-41d4-a716-446655440000")
    keys_requested: List[str] = Field(..., description="Telemetry keys requested", example=["temperature", "humidity"])
    data: Dict[str, Optional[Dict[str, Union[int, float, str, bool]]]] = Field(..., description="Latest values by key")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "success",
                "timestamp": 1640995200000,
                "device_id": "550e8400-e29b-41d4-a716-446655440000",
                "keys_requested": ["temperature", "humidity"],
                "data": {
                    "temperature": {"ts": 1640995200000, "value": 23.5},
                    "humidity": {"ts": 1640995180000, "value": 65.2}
                }
            }
        }
    }