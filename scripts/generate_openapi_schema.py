#!/usr/bin/env python3
"""
Generate OpenAPI schema documentation for TB-API-SDK.

This script creates example OpenAPI documentation structure without
requiring the full FastAPI app to be runnable, demonstrating the
comprehensive API documentation standards achieved.
"""
import json
from pathlib import Path
from datetime import datetime


def create_comprehensive_openapi_spec() -> dict:
    """Create a comprehensive OpenAPI specification following ThingsBoard standards."""
    
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "TB-API-SDK",
            "version": "0.1.0",
            "description": """
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

API requests are limited to **100 requests per 60 seconds** per API key. 
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
            """,
            "termsOfService": "https://yourdomain.com/terms",
            "contact": {
                "name": "TB-API-SDK Support",
                "url": "https://github.com/yourusername/TB-API-SKD",
                "email": "support@yourdomain.com"
            },
            "license": {
                "name": "MIT License",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "https://api.yourdomain.com",
                "description": "Production server"
            },
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            }
        ],
        "paths": {
            "/health": {
                "get": {
                    "tags": ["health"],
                    "summary": "Health Check",
                    "description": "Simple health check endpoint for service monitoring and load balancer probes.",
                    "operationId": "healthCheck",
                    "responses": {
                        "200": {
                            "description": "Service is healthy and operational",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/HealthCheckResponse"},
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
                }
            },
            "/api/v1/tb/devices/{device_id}/telemetry": {
                "post": {
                    "tags": ["telemetry", "devices"],
                    "summary": "Upload Telemetry Data",
                    "description": "Upload time-series telemetry data to a specific ThingsBoard device.",
                    "operationId": "uploadDeviceTelemetry",
                    "parameters": [
                        {
                            "name": "device_id",
                            "in": "path",
                            "required": True,
                            "description": "UUID of the target device",
                            "schema": {
                                "type": "string",
                                "format": "uuid",
                                "example": "550e8400-e29b-41d4-a716-446655440000"
                            }
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TelemetryUploadRequest"},
                                "example": {
                                    "temperature": [
                                        {"ts": 1640995200000, "value": 25.6},
                                        {"ts": 1640995260000, "value": 26.1}
                                    ],
                                    "humidity": [
                                        {"ts": 1640995200000, "value": 60.2}
                                    ]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Telemetry data uploaded successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TelemetryUploadResponse"},
                                    "example": {
                                        "status": "success",
                                        "timestamp": 1640995200000,
                                        "device_id": "550e8400-e29b-41d4-a716-446655440000",
                                        "keys_uploaded": ["temperature", "humidity"],
                                        "total_data_points": 3,
                                        "message": "Successfully uploaded 3 data points for 2 telemetry keys"
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid request data",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "status": 400,
                                        "message": "No telemetry data provided",
                                        "error_code": "VALIDATION_ERROR",
                                        "timestamp": 1640995200000
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Authentication failed",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "502": {
                            "description": "ThingsBoard backend error",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                                    "example": {
                                        "status": 502,
                                        "message": "ThingsBoard authentication failed",
                                        "error_code": "UPSTREAM_ERROR",
                                        "timestamp": 1640995200000
                                    }
                                }
                            }
                        }
                    },
                    "security": [{"ApiKeyAuth": []}]
                }
            },
            "/api/v1/tb/devices": {
                "get": {
                    "tags": ["devices"],
                    "summary": "List Devices",
                    "description": "Return paginated list of devices for current tenant.",
                    "operationId": "listDevices",
                    "parameters": [
                        {
                            "name": "page",
                            "in": "query",
                            "description": "Zero-based page index",
                            "schema": {"type": "integer", "minimum": 0, "default": 0}
                        },
                        {
                            "name": "page_size",
                            "in": "query", 
                            "description": "Number of items per page (max 1000)",
                            "schema": {"type": "integer", "minimum": 1, "maximum": 1000, "default": 100}
                        },
                        {
                            "name": "text_search",
                            "in": "query",
                            "description": "Optional device name filter",
                            "schema": {"type": "string", "example": "Temperature Sensor"}
                        },
                        {
                            "name": "device_type",
                            "in": "query",
                            "description": "Optional device type filter",
                            "schema": {"type": "string", "example": "TemperatureSensor"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of devices retrieved successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/DeviceListResponse"}
                                }
                            }
                        }
                    },
                    "security": [{"ApiKeyAuth": []}]
                }
            }
        },
        "components": {
            "schemas": {
                "ErrorResponse": {
                    "type": "object",
                    "required": ["status", "message", "error_code", "timestamp"],
                    "properties": {
                        "status": {"type": "integer", "description": "HTTP status code", "example": 400},
                        "message": {"type": "string", "description": "Human-readable error description"},
                        "error_code": {"type": "string", "enum": ["VALIDATION_ERROR", "AUTHENTICATION_FAILED", "AUTHORIZATION_FAILED", "RESOURCE_NOT_FOUND", "UPSTREAM_ERROR", "RATE_LIMIT_EXCEEDED", "INTERNAL_ERROR"]},
                        "timestamp": {"type": "integer", "description": "Unix timestamp when error occurred"},
                        "details": {"type": "object", "description": "Additional error context"}
                    }
                },
                "TelemetryDataPoint": {
                    "type": "object",
                    "required": ["ts", "value"],
                    "properties": {
                        "ts": {"type": "integer", "description": "Timestamp in milliseconds since Unix epoch", "minimum": 0},
                        "value": {"oneOf": [{"type": "string"}, {"type": "number"}, {"type": "boolean"}], "description": "Telemetry value"}
                    }
                },
                "TelemetryUploadRequest": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/TelemetryDataPoint"}
                    },
                    "example": {
                        "temperature": [{"ts": 1640995200000, "value": 25.6}],
                        "humidity": [{"ts": 1640995200000, "value": 60.2}]
                    }
                },
                "TelemetryUploadResponse": {
                    "type": "object",
                    "required": ["status", "timestamp", "device_id", "keys_uploaded", "total_data_points", "message"],
                    "properties": {
                        "status": {"type": "string", "example": "success"},
                        "timestamp": {"type": "integer", "example": 1640995200000},
                        "device_id": {"type": "string", "format": "uuid"},
                        "keys_uploaded": {"type": "array", "items": {"type": "string"}},
                        "total_data_points": {"type": "integer", "minimum": 0},
                        "message": {"type": "string"}
                    }
                },
                "HealthCheckResponse": {
                    "type": "object",
                    "required": ["status", "timestamp", "service", "version"],
                    "properties": {
                        "status": {"type": "string", "example": "success"},
                        "timestamp": {"type": "integer", "example": 1640995200000},
                        "service": {"type": "string", "example": "TB-API-SKD"},
                        "version": {"type": "string", "example": "0.1.0"}
                    }
                },
                "DeviceListResponse": {
                    "type": "object",
                    "required": ["status", "timestamp", "data", "pagination"],
                    "properties": {
                        "status": {"type": "string", "example": "success"},
                        "timestamp": {"type": "integer", "example": 1640995200000},
                        "data": {"type": "array", "items": {"type": "object"}},
                        "pagination": {
                            "type": "object",
                            "properties": {
                                "page": {"type": "integer"},
                                "page_size": {"type": "integer"},
                                "total_pages": {"type": "integer"},
                                "total_elements": {"type": "integer"},
                                "has_next": {"type": "boolean"}
                            }
                        }
                    }
                }
            },
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for authentication. Contact support to obtain your API key."
                }
            }
        },
        "tags": [
            {"name": "health", "description": "Service health and status endpoints"},
            {"name": "thingsboard", "description": "ThingsBoard proxy endpoints for device and telemetry management"},
            {"name": "devices", "description": "Device management and discovery operations"},
            {"name": "telemetry", "description": "Time-series data upload and retrieval operations"},
            {"name": "attributes", "description": "Device attribute management (server-side and shared)"},
            {"name": "assets", "description": "Asset and asset profile management operations"},
            {"name": "relationships", "description": "Entity relationship and graph traversal operations"}
        ]
    }


def main():
    """Generate the OpenAPI specification file."""
    print("🚀 Generating comprehensive OpenAPI specification...")
    
    spec = create_comprehensive_openapi_spec()
    
    # Save to file
    output_path = Path("tb_api_sdk_openapi.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
    
    print(f"✅ OpenAPI specification saved to: {output_path}")
    print(f"📊 Generated spec contains:")
    print(f"   - {len(spec.get('paths', {}))} endpoint groups")
    print(f"   - {len(spec.get('components', {}).get('schemas', {}))} schemas")
    print(f"   - {len(spec.get('tags', []))} tags")
    print(f"   - Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n🔧 Usage examples:")
    print("   # Validate specification")
    print("   swagger-codegen validate -i tb_api_sdk_openapi.json")
    print("   ")
    print("   # Generate Python client SDK")
    print("   openapi-generator generate -i tb_api_sdk_openapi.json -g python -o ./client-sdk")
    print("   ")
    print("   # Generate TypeScript/JavaScript client")
    print("   openapi-generator generate -i tb_api_sdk_openapi.json -g typescript-axios -o ./client-ts")


if __name__ == "__main__":
    main()