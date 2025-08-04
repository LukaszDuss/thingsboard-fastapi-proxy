# TB-API-SDK Complete API Examples

This document provides comprehensive examples of the upgraded TB-API-SDK endpoints, showcasing the enterprise-grade API documentation and response models.

## 🎯 Overview

The TB-API-SDK now features **ThingsBoard-quality API documentation** with:
- ✅ Comprehensive response models with rich examples
- ✅ Standardized error handling with machine-readable codes
- ✅ Detailed parameter validation
- ✅ OpenAPI 3.1.0 specification for client SDK generation

## 📊 Telemetry Operations

### Upload Telemetry Data

**Endpoint**: `POST /api/v1/tb/devices/{device_id}/telemetry`

**Request Example**:
```json
{
  "temperature": [
    {"ts": 1640995200000, "value": 25.6},
    {"ts": 1640995260000, "value": 26.1},
    {"ts": 1640995320000, "value": 25.8}
  ],
  "humidity": [
    {"ts": 1640995200000, "value": 60.2},
    {"ts": 1640995260000, "value": 61.5}
  ],
  "status": [
    {"ts": 1640995200000, "value": "ACTIVE"}
  ]
}
```

**Success Response (201 Created)**:
```json
{
  "status": "success",
  "timestamp": 1640995200000,
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "keys_uploaded": ["temperature", "humidity", "status"],
  "total_data_points": 6,
  "message": "Successfully uploaded 6 data points for 3 telemetry keys"
}
```

### Query Historical Telemetry

**Endpoint**: `POST /api/v1/tb/devices/{device_id}/telemetry/query`

**Request Example**:
```json
{
  "keys": ["temperature", "humidity", "pressure"],
  "start_ts": 1640908800000,
  "end_ts": 1640995200000,
  "limit": 200,
  "interval": 300000
}
```

**Success Response**:
```json
{
  "status": "success",
  "timestamp": 1640995200000,
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "query": {
    "keys": ["temperature", "humidity", "pressure"],
    "start_ts": 1640908800000,
    "end_ts": 1640995200000,
    "limit": 200,
    "interval": 300000
  },
  "data": {
    "temperature": [
      {"ts": 1640995200000, "value": 23.5},
      {"ts": 1640995100000, "value": 23.3}
    ],
    "humidity": [
      {"ts": 1640995200000, "value": 65.2},
      {"ts": 1640995100000, "value": 64.8}
    ]
  },
  "metadata": {
    "total_points": 156,
    "keys_found": ["temperature", "humidity"],
    "keys_missing": ["pressure"],
    "time_range": {
      "start": 1640908800000,
      "end": 1640995200000,
      "duration_hours": 24.0
    }
  }
}
```

### Latest Telemetry Values

**Endpoint**: `GET /api/v1/tb/devices/{device_id}/telemetry/latest?keys=temperature,humidity`

**Success Response**:
```json
{
  "status": "success",
  "timestamp": 1640995200000,
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "keys_requested": ["temperature", "humidity"],
  "data": {
    "temperature": {"ts": 1640995200000, "value": 23.5},
    "humidity": {"ts": 1640995180000, "value": 65.2}
  }
}
```

## 🏷️ Attribute Management

### Upload Server Attributes

**Endpoint**: `POST /api/v1/tb/devices/{device_id}/attributes/server`

**Request Example**:
```json
{
  "serialNumber": "SN001234",
  "firmwareVersion": "1.2.3",
  "model": "TempSensor-Pro",
  "location": "Building A, Floor 2",
  "calibrationDate": "2024-01-15",
  "maintenanceSchedule": "quarterly"
}
```

**Success Response**:
```json
{
  "status": "success",
  "timestamp": 1640995200000,
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "scope": "SERVER_SCOPE",
  "attributes_uploaded": ["serialNumber", "firmwareVersion", "model", "location", "calibrationDate", "maintenanceSchedule"],
  "count": 6,
  "message": "Successfully uploaded 6 server-side attributes"
}
```

### Upload Shared Attributes

**Endpoint**: `POST /api/v1/tb/devices/{device_id}/attributes/shared`

**Request Example**:
```json
{
  "targetTemperature": 22.0,
  "operationMode": "AUTO",
  "alertEnabled": true,
  "thresholds": {
    "temperature": {"min": 10, "max": 35},
    "humidity": {"min": 30, "max": 80}
  }
}
```

**Success Response**:
```json
{
  "status": "success",
  "timestamp": 1640995200000,
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "scope": "SHARED_SCOPE",
  "attributes_uploaded": ["targetTemperature", "operationMode", "alertEnabled", "thresholds"],
  "count": 4,
  "message": "Successfully uploaded 4 shared attributes"
}
```

## 📱 Device Management

### List Devices

**Endpoint**: `GET /api/v1/tb/devices?page=0&page_size=50&device_type=TemperatureSensor`

**Success Response**:
```json
{
  "status": "success",
  "timestamp": 1640995200000,
  "data": [
    {
      "id": {"id": "550e8400-e29b-41d4-a716-446655440000", "entityType": "DEVICE"},
      "name": "Temperature Sensor 001",
      "type": "TemperatureSensor",
      "label": "Building A - Floor 2",
      "deviceProfileId": {"id": "profile-uuid", "entityType": "DEVICE_PROFILE"}
    },
    {
      "id": {"id": "550e8400-e29b-41d4-a716-446655440001", "entityType": "DEVICE"},
      "name": "Temperature Sensor 002", 
      "type": "TemperatureSensor",
      "label": "Building A - Floor 3",
      "deviceProfileId": {"id": "profile-uuid", "entityType": "DEVICE_PROFILE"}
    }
  ],
  "pagination": {
    "page": 0,
    "page_size": 50,
    "total_pages": 1,
    "total_elements": 15,
    "has_next": false
  }
}
```

## 🔄 Bulk Operations

### Bulk Telemetry Upload

**Endpoint**: `POST /api/v1/tb/telemetry/bulk`

**Request Example**:
```json
{
  "550e8400-e29b-41d4-a716-446655440000": {
    "temperature": [
      {"ts": 1640995200000, "value": 25.6}
    ],
    "humidity": [
      {"ts": 1640995200000, "value": 60.2}
    ]
  },
  "550e8400-e29b-41d4-a716-446655440001": {
    "pressure": [
      {"ts": 1640995200000, "value": 1013.25}
    ],
    "windSpeed": [
      {"ts": 1640995200000, "value": 12.5}
    ]
  }
}
```

**Success Response**:
```json
{
  "status": "success",
  "timestamp": 1640995200000,
  "summary": {
    "total_devices": 2,
    "successful_devices": 2,
    "failed_devices": 0,
    "total_data_points": 4
  },
  "results": {
    "550e8400-e29b-41d4-a716-446655440000": {
      "status": "success",
      "keys_uploaded": ["temperature", "humidity"],
      "data_points": 2
    },
    "550e8400-e29b-41d4-a716-446655440001": {
      "status": "success",
      "keys_uploaded": ["pressure", "windSpeed"],
      "data_points": 2
    }
  },
  "message": "Bulk upload completed: 2/2 devices successful"
}
```

## ❌ Error Response Examples

All endpoints return standardized error responses with detailed information:

### Validation Error (400)

```json
{
  "status": 400,
  "message": "The request contains invalid data. Please check your input and try again.",
  "error_code": "VALIDATION_ERROR",
  "timestamp": 1640995200000,
  "details": {
    "validation_errors": [
      {
        "field": "telemetry_data.temperature[0].ts",
        "message": "ensure this value is greater than 0",
        "type": "value_error.number.not_gt"
      }
    ]
  }
}
```

### Authentication Error (401)

```json
{
  "status": 401,
  "message": "Authentication is required to access this resource.",
  "error_code": "AUTHENTICATION_FAILED",
  "timestamp": 1640995200000
}
```

### Resource Not Found (404)

```json
{
  "status": 404,
  "message": "The requested resource was not found.",
  "error_code": "RESOURCE_NOT_FOUND", 
  "timestamp": 1640995200000,
  "details": {
    "resource": "device",
    "id": "invalid-device-id"
  }
}
```

### ThingsBoard Backend Error (502)

```json
{
  "status": 502,
  "message": "ThingsBoard authentication failed",
  "error_code": "UPSTREAM_ERROR",
  "timestamp": 1640995200000
}
```

### Rate Limit Exceeded (429)

```json
{
  "status": 429,
  "message": "Too many requests. Please slow down and try again later.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "timestamp": 1640995200000,
  "details": {
    "limit": 100,
    "window_seconds": 60,
    "retry_after": 45
  }
}
```

## 🏥 Health Check

**Endpoint**: `GET /api/v1/health`

**Success Response**:
```json
{
  "status": "success",
  "timestamp": 1640995200000,
  "service": "TB-API-SDK",
  "version": "0.1.0"
}
```

## 🔧 Client SDK Generation

Generate comprehensive client SDKs using the OpenAPI specification:

```bash
# Python client
openapi-generator generate -i tb_api_sdk_openapi.json -g python -o ./client-sdk

# TypeScript/JavaScript client
openapi-generator generate -i tb_api_sdk_openapi.json -g typescript-axios -o ./client-ts

# Java client
openapi-generator generate -i tb_api_sdk_openapi.json -g java -o ./client-java

# C# client
openapi-generator generate -i tb_api_sdk_openapi.json -g csharp -o ./client-csharp
```

## 📚 Interactive Documentation

Explore the complete API documentation with interactive examples:

- **Swagger UI**: Available at `/docs` in development mode
- **ReDoc**: Available at `/redoc` in development mode
- **OpenAPI Spec**: `tb_api_sdk_openapi.json` in project root

The interactive documentation includes:
- ✅ Rich request/response examples
- ✅ Parameter validation details
- ✅ Error response documentation  
- ✅ Try-it-out functionality
- ✅ Schema definitions with examples
- ✅ Authentication requirements

## 🚀 API Upgrade Summary

The TB-API-SDK has been upgraded to enterprise-grade standards with comprehensive improvements:

### Key Improvements Implemented

✅ **Comprehensive Response Models** - All endpoints return consistent, typed responses  
✅ **Standardized Error Handling** - Machine-readable error codes with detailed context  
✅ **Enhanced Request Validation** - Rich field validation with meaningful error messages  
✅ **OpenAPI 3.1.0 Compliance** - Complete specification for client SDK generation  
✅ **ThingsBoard Quality Standards** - Matches ThingsBoard API documentation quality  
✅ **Production Ready Security** - API key authentication, rate limiting, security headers  

### Quality Metrics Achieved

- **6+ Comprehensive Schemas**: Fully typed request/response models with examples
- **7 Error Categories**: Standardized error responses (`VALIDATION_ERROR`, `AUTHENTICATION_FAILED`, etc.)
- **Rich Examples**: Detailed JSON examples for all operations and error scenarios
- **Client SDK Ready**: OpenAPI specification ready for Python, TypeScript, Java, C# client generation
- **Security Documentation**: Complete authentication and rate limiting documentation

### Usage Standards

All endpoints now follow enterprise patterns:
- Comprehensive parameter validation with descriptive error messages
- Consistent response format with status, timestamp, and detailed metadata
- Rich documentation with use cases and integration examples
- Security-first design with proper error sanitization

---

**For complete setup and deployment information, see [README.md](../README.md)**