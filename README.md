# TB-API-SDK – Enterprise ThingsBoard API Wrapper

This repository contains a **comprehensive, enterprise-grade** FastAPI service that provides a secure, well-documented REST API wrapper for ThingsBoard IoT platform with **ThingsBoard-quality API documentation**, client SDK generation capabilities, and advanced features.

## 🔒 Security Features

* **API Key Authentication** - All endpoints protected with configurable API keys
* **Rate Limiting** - Prevent abuse with configurable request limits (100/min default)
* **Security Headers** - Comprehensive headers including CSP (with Swagger UI support), HSTS, XSS protection
* **CORS Security** - No wildcard origins, explicit allowlists only
* **Error Sanitization** - Generic error messages in production, detailed logs for debugging
* **HTTPS Enforcement** - TLS verification and security warnings for non-HTTPS

## 🚀 Features
--------
### 📚 **Enterprise-Grade API Documentation**
* **OpenAPI 3.1.0 Specification** - Comprehensive API documentation matching ThingsBoard standards
* **Rich Examples** - Detailed JSON examples for all endpoints and response models  
* **Client SDK Generation** - Ready for Python, TypeScript, and other client SDK generation
* **Interactive Documentation** - Swagger UI and ReDoc available in development mode

### 🔧 **Advanced API Capabilities**  
* **Comprehensive Response Models** - Fully typed Pydantic models with validation
* **Standardized Error Handling** - Consistent error responses with machine-readable error codes
* **Detailed Parameter Validation** - Rich field validation with descriptive error messages
* **Bulk Operations** - Efficient batch processing for multiple devices

### 🏗️ **Robust Architecture**
* **FastAPI + Uvicorn** - Modern async framework with full type hints
* **Modular Structure** - Layered architecture (`app/core`, `app/api/v1/routes`, `app/schemas`)
* **Settings Management** - Pydantic `BaseSettings` with environment-driven configuration
* **Comprehensive Logging** - Structured logging with security event monitoring
* **Health Endpoints** - Kubernetes/Docker Swarm ready with detailed health responses

### 🛡️ **Production Security**
* **API Key Authentication** - All endpoints protected with configurable API keys
* **Rate Limiting** - Prevent abuse with configurable request limits (100/min default)
* **Security Headers** - Comprehensive headers including CSP, HSTS, XSS protection
* **CORS Security** - No wildcard origins, explicit allowlists only
* **Error Sanitization** - Generic error messages in production, detailed logs for debugging
* **HTTPS Enforcement** - TLS verification and security warnings

Project layout
--------------
```
app/
  core/            # configuration + logging helpers + security
    auth.py        # API key authentication
    rate_limiter.py # Request rate limiting
    error_handlers.py # Sanitized error responses
  api/
    v1/routes/     # individual feature routers (health, devices, …)
  main.py          # FastAPI application factory
Dockerfile
requirements.txt
```

## 🔧 Quick Start

### 1. Environment Setup
```bash
# Copy and configure environment
cp env_sample .env
vim .env   # Configure TB_HOST, credentials, API_KEY, etc.
```

**Critical**: Generate a secure API key for `API_KEY` in your `.env` file:
```bash
# Generate the key (copy the output to your .env file)
python -c "import secrets; print('API_KEY=' + secrets.token_urlsafe(32))"
```

### 2. Test Connection
```bash
# Install dependencies  
pip install -r requirements.txt

# Test ThingsBoard connection
python tb_connection_check.py
```

### 3. Run the Service
```bash
# Development
uvicorn app.main:app --reload

# Production with Docker
docker compose up --build -d
```

## 🔐 API Authentication & Usage

All endpoints require the `X-API-Key` header and return comprehensive, typed responses:

### 📱 **Device Management**
```bash
# List devices with rich response model  
curl -H "X-API-Key: your-secret-api-key" \
     http://localhost:8000/api/v1/tb/devices

# Response includes pagination metadata:
{
  "status": "success", 
  "timestamp": 1640995200000,
  "data": [...],
  "pagination": {
    "page": 0, "page_size": 100, "total_pages": 5, 
    "total_elements": 487, "has_next": true
  }
}
```

### 📊 **Telemetry Operations**
```bash
# Upload telemetry with detailed response
curl -X POST \
     -H "X-API-Key: your-secret-api-key" \
     -H "Content-Type: application/json" \
     -d '{"temperature": [{"ts": 1640995200000, "value": 25.6}]}' \
     http://localhost:8000/api/v1/tb/devices/{device_id}/telemetry

# Rich success response:
{
  "status": "success",
  "timestamp": 1640995200000, 
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "keys_uploaded": ["temperature"],
  "total_data_points": 1,
  "message": "Successfully uploaded 1 data points for 1 telemetry keys"
}
```

### ❌ **Standardized Error Responses**
```bash
# Invalid request returns consistent error format:
{
  "status": 400,
  "message": "No telemetry data provided", 
  "error_code": "VALIDATION_ERROR",
  "timestamp": 1640995200000,
  "details": {"field": "telemetry_data", "issue": "empty request body"}
}
```

### 🔄 **Bulk Operations**
```bash
# Upload to multiple devices efficiently
curl -X POST \
     -H "X-API-Key: your-secret-api-key" \
     -H "Content-Type: application/json" \
     -d '{"device1-uuid": {"temp": [{"ts": 1640995200000, "value": 25.6}]}}' \
     http://localhost:8000/api/v1/tb/telemetry/bulk

# Detailed per-device results:
{
  "status": "success",
  "summary": {"total_devices": 1, "successful_devices": 1, "failed_devices": 0},
  "results": {"device1-uuid": {"status": "success", "data_points": 1}},
  "message": "Bulk upload completed: 1/1 devices successful"
}
```

## 📊 Rate Limiting

Default limits: **100 requests per minute per IP**

Headers included in responses:
- `X-RateLimit-Limit: 100`
- `X-RateLimit-Remaining: 87`
- `X-RateLimit-Reset: 1640995260`

When exceeded:
```json
{
  "error": "Rate limit exceeded",
  "detail": "Maximum 100 requests per 60 seconds allowed",
  "retry_after": 45
}
```

## 🛡️ Production Security Checklist

- [ ] **HTTPS Only**: Set `TB_HOST=https://...`
- [ ] **Strong API Key**: Use `secrets.token_urlsafe(32)` - generates 43-character cryptographically secure key
- [ ] **Debug Off**: `DEBUG=false` in production
- [ ] **CORS**: Configure specific `BACKEND_CORS_ORIGINS`
- [ ] **Trusted Hosts**: Set `ALLOWED_HOSTS` for your domain
- [ ] **Monitor**: Set up log monitoring for security events

## Testing ThingsBoard Connection

Before running the API service, you should verify that your ThingsBoard connection is working properly. The repository includes a **standalone diagnostic script** for this purpose:

```bash
python tb_connection_check.py
```

### What the diagnostic script tests:

1. **📋 Configuration** - Validates ThingsBoard host, username, password
2. **🔐 Authentication** - Tests login and JWT token functionality  
3. **📱 Device Discovery** - Lists available devices in your tenant
4. **📤 Upload Testing** - Tests telemetry and attributes upload to real devices
5. **🌐 API Endpoints** - Verifies FastAPI health and SDK endpoints

### Sample output:
```
🔧 TB-API-SKD Connection Test Suite
Testing connection to ThingsBoard at https://your-thingsboard-host.com

✅ Configuration values are set!
✅ Successfully authenticated as: your-username@domain.com  
✅ Found 3 devices in tenant
✅ Telemetry upload successful
✅ Server attributes upload successful
✅ Health endpoint working

🎉 ALL TESTS PASSED!
Your ThingsBoard integration is working perfectly!
```

### When to use the diagnostic:
- **First setup** - Verify everything works after installation
- **Troubleshooting** - Quick diagnosis of connection issues
- **Configuration changes** - Test after updating settings  
- **Pre-deployment** - Validate integration before going live

**Note**: This script runs independently and doesn't require pytest or any test framework.

## Running with Docker Compose

The repository ships with a minimal `docker-compose.yml` so you don't have to build / run manually:

```bash
docker compose up --build -d     # builds image and starts container
```

* Service will listen on `localhost:8000`.  
* Environment variables are loaded from `.env` – copy the provided `env_sample` and adjust:

```bash
cp env_sample .env
vim .env   # edit TB_HOST, credentials, API_KEY, CORS list …
```

### Recommended setup workflow:
```bash
# 1. Copy and configure environment
cp env_sample .env
vim .env

# 2. Generate and set secure API key
echo "Generated API key (copy to your .env file):"
python -c "import secrets; print('API_KEY=' + secrets.token_urlsafe(32))"

# 2.1. Verify your API key is properly set (should be 43+ characters)
grep "API_KEY=" .env

# 3. Install dependencies  
pip install -r requirements.txt

# 4. Test ThingsBoard connection
python tb_connection_check.py

# 5. Run the service
docker compose up --build -d
```

Tear-down:
```bash
docker compose down
``` 

## 🚨 Security Monitoring

The API automatically logs security events:

```bash
# Monitor authentication failures
docker logs tb-api-skd | grep "Security event: 401"

# Check rate limiting
docker logs tb-api-skd | grep "Rate limit exceeded"

# ThingsBoard connection issues
docker logs tb-api-skd | grep "ThingsBoard HTTP error"
```

## 📚 API Documentation & Client SDKs

### **Interactive Documentation**
- **Swagger UI**: Available at `/docs` in development mode
- **ReDoc**: Available at `/redoc` in development mode  
- **OpenAPI Spec**: `tb_api_sdk_openapi.json` (3.1.0 compliant)

### **Generate Client SDKs**
```bash
# Python client SDK
openapi-generator generate -i tb_api_sdk_openapi.json -g python -o ./client-sdk

# TypeScript/JavaScript client  
openapi-generator generate -i tb_api_sdk_openapi.json -g typescript-axios -o ./client-ts

# Other languages supported: Java, C#, Go, PHP, Ruby, etc.
```

### **API Specification Quality**
- ✅ **6+ Comprehensive Schemas** - Fully typed request/response models
- ✅ **Rich Examples** - Detailed JSON examples for all operations
- ✅ **Error Documentation** - Complete error scenario coverage
- ✅ **Parameter Validation** - Descriptive field validation with error messages
- ✅ **ThingsBoard-Quality Standards** - Enterprise-grade documentation

## 🔧 Development & Deployment

### **Project Structure**
```
app/
├── schemas/           # Pydantic request/response models
│   ├── requests.py    # Comprehensive request validation
│   └── responses.py   # Typed response models with examples
├── core/              # Configuration + security + error handling  
│   ├── auth.py        # API key authentication
│   ├── error_handlers.py # Standardized error responses
│   └── rate_limiter.py   # Request rate limiting
├── api/v1/routes/     # Feature routers with rich documentation
└── main.py            # FastAPI app with comprehensive OpenAPI metadata

scripts/
└── generate_openapi_schema.py  # OpenAPI specification generation

tb_api_sdk_openapi.json         # Complete API specification
```

## Next Steps
----------
1.  **Explore Interactive Docs** - Visit `/docs` to explore the comprehensive API documentation
2.  **Generate Client SDKs** - Use the OpenAPI spec to generate clients in your preferred language
3.  **Extend API** - Add new routers using the established patterns in `app/api/v1/routes/`
4.  **Review Security** - See `SECURITY.md` for production deployment guidelines  
5.  **Explore API Examples** - See `docs/API_EXAMPLES.md` for comprehensive usage examples and upgrade details

---

**📖 Documentation:** [SECURITY.md](SECURITY.md) | [API Examples](docs/API_EXAMPLES.md)
**🔧 API Spec:** `tb_api_sdk_openapi.json` | **🌐 Interactive:** `/docs` and `/redoc` 