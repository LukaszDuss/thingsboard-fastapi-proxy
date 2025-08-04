# ThingsBoard FastAPI Proxy

> **Enterprise-grade REST API wrapper for ThingsBoard IoT platform with comprehensive documentation and client SDK generation capabilities**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.108.0-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?style=flat&logo=python)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat&logo=docker)](https://docker.com)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1.0-85EA2D.svg?style=flat&logo=openapi-initiative)](https://swagger.io/specification/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🎯 **What is this?**

A **production-ready FastAPI service** that provides a secure, well-documented REST API wrapper around ThingsBoard's IoT platform. Think of it as an enterprise gateway that simplifies ThingsBoard integration while adding comprehensive security, documentation, and client SDK generation capabilities.

## ✨ **Key Features**

### 🔒 **Enterprise Security**
- **API Key Authentication** - Secure access control for all endpoints
- **Rate Limiting** - Built-in protection (100 req/min configurable)
- **Security Headers** - CSP, HSTS, XSS protection
- **CORS Security** - No wildcard origins, explicit allowlists
- **Error Sanitization** - Production-safe error responses

### 📚 **Professional Documentation**
- **OpenAPI 3.1.0 Specification** - Complete API documentation
- **Rich Examples** - Detailed JSON examples for all operations
- **Client SDK Generation** - Ready for Python, TypeScript, Java, C#
- **Interactive Docs** - Swagger UI and ReDoc available
- **ThingsBoard-Quality Standards** - Enterprise-grade documentation

### 🏗️ **Production Architecture**
- **FastAPI + Uvicorn** - Modern async framework with full type hints
- **Modular Structure** - Clean separation of concerns
- **Docker Ready** - Complete containerization with Docker Compose
- **Health Endpoints** - Kubernetes/Docker Swarm compatible
- **Comprehensive Logging** - Structured logging with security events

### 🚀 **IoT Operations**
- **Device Management** - List, query, and manage IoT devices
- **Telemetry Operations** - Upload and retrieve time-series data  
- **Attribute Management** - Handle device attributes (server-side and shared)
- **Bulk Operations** - Efficient batch processing for multiple devices
- **Entity Relationships** - Explore device and asset relationship graphs

## 🎪 **Who Should Use This?**

### **Perfect for:**
- **IoT Companies** building applications on ThingsBoard
- **System Integrators** needing clean API access to ThingsBoard
- **Enterprise Teams** requiring production-grade security and documentation
- **Mobile/Web Developers** wanting typed client SDKs for ThingsBoard
- **DevOps Teams** needing containerized, observable IoT services

### **Use Cases:**
- 📱 **Mobile App Backend** - Clean REST API for mobile applications
- 🌐 **Web Dashboard APIs** - Simplified endpoints for web interfaces  
- 🔌 **Third-party Integrations** - Secure API for external systems
- 📊 **Data Analytics** - Structured telemetry data access
- 🛠️ **Client SDK Generation** - Automated SDK creation for multiple languages

## 🚀 **Quick Start**

### **1. Clone and Configure**
```bash
git clone https://github.com/yourusername/thingsboard-fastapi-proxy.git
cd thingsboard-fastapi-proxy
cp env_sample .env
# Edit .env with your ThingsBoard credentials
```

**Critical**: Generate a secure API key for `API_KEY` in your `.env` file:
```bash
# Generate the key (copy the output to your .env file)
python -c "import secrets; print('API_KEY=' + secrets.token_urlsafe(32))"
```

### **2. Test Connection**
```bash
pip install -r requirements.txt
python tb_connection_check.py  # Verify ThingsBoard connectivity
```

### **3. Run with Docker**
```bash
docker compose up --build -d
```

### **4. Access Documentation**
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📊 **API Example**

```bash
# Upload telemetry data
curl -X POST \
  -H "X-API-Key: your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"temperature": [{"ts": 1640995200000, "value": 25.6}]}' \
  http://localhost:8000/api/v1/tb/devices/{device-id}/telemetry

# Response: Rich, typed response with metadata
{
  "status": "success",
  "timestamp": 1640995200000,
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "keys_uploaded": ["temperature"],
  "total_data_points": 1,
  "message": "Successfully uploaded 1 data points for 1 telemetry keys"
}
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

## 🔧 **Generate Client SDKs**

```bash
# Python SDK
openapi-generator generate -i tb_api_sdk_openapi.json -g python -o ./client-sdk

# TypeScript SDK  
openapi-generator generate -i tb_api_sdk_openapi.json -g typescript-axios -o ./client-ts

# Java SDK
openapi-generator generate -i tb_api_sdk_openapi.json -g java -o ./client-java
```

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

## 🛡️ Production Security Checklist

- [ ] **HTTPS Only**: Set `TB_HOST=https://...`
- [ ] **Strong API Key**: Use `secrets.token_urlsafe(32)` - generates 43-character cryptographically secure key
- [ ] **Debug Off**: `DEBUG=false` in production
- [ ] **CORS**: Configure specific `BACKEND_CORS_ORIGINS`
- [ ] **Trusted Hosts**: Set `ALLOWED_HOSTS` for your domain
- [ ] **Monitor**: Set up log monitoring for security events

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

## 🏆 **Quality Standards**

- ✅ **6+ Comprehensive Schemas** - Fully typed request/response models
- ✅ **Rich Examples** - Detailed JSON examples for all operations  
- ✅ **Standardized Errors** - Machine-readable error codes with context
- ✅ **Complete Test Suite** - 56+ tests with 98% success rate
- ✅ **Production Security** - Enterprise-grade security implementation
- ✅ **Client SDK Ready** - OpenAPI 3.1.0 specification for code generation

## 🛡️ **Security First**

This proxy never exposes your ThingsBoard credentials. It authenticates server-to-server with ThingsBoard and provides secure API key authentication for clients. Your ThingsBoard instance stays protected behind the proxy.

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

### **API Specification Quality**
- ✅ **6+ Comprehensive Schemas** - Fully typed request/response models
- ✅ **Rich Examples** - Detailed JSON examples for all operations
- ✅ **Error Documentation** - Complete error scenario coverage
- ✅ **Parameter Validation** - Descriptive field validation with error messages
- ✅ **ThingsBoard-Quality Standards** - Enterprise-grade documentation

## Next Steps

1. **Explore Interactive Docs** - Visit `/docs` to explore the comprehensive API documentation
2. **Generate Client SDKs** - Use the OpenAPI spec to generate clients in your preferred language
3. **Extend API** - Add new routers using the established patterns in `app/api/v1/routes/`
4. **Review Security** - See `SECURITY.md` for production deployment guidelines  
5. **Explore API Examples** - See `docs/API_EXAMPLES.md` for comprehensive usage examples and upgrade details

## 🤝 **Contributing**

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⭐ **Star History**

If this project helps you, please consider giving it a star! ⭐

---

**📖 Documentation:** [SECURITY.md](SECURITY.md) | [API Examples](docs/API_EXAMPLES.md)  
**🔧 API Spec:** `tb_api_sdk_openapi.json` | **🌐 Interactive:** `/docs` and `/redoc`  
**Made with ❤️ for the IoT community**