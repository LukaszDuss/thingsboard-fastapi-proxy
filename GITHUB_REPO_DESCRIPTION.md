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

## 🔧 **Generate Client SDKs**

```bash
# Python SDK
openapi-generator generate -i tb_api_sdk_openapi.json -g python -o ./client-sdk

# TypeScript SDK  
openapi-generator generate -i tb_api_sdk_openapi.json -g typescript-axios -o ./client-ts

# Java SDK
openapi-generator generate -i tb_api_sdk_openapi.json -g java -o ./client-java
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

## 📈 **Production Ready**

- **Docker Containerization** - Ready for deployment
- **Health Monitoring** - Kubernetes-compatible health checks
- **Structured Logging** - Security event monitoring
- **Rate Limiting** - Built-in abuse protection
- **Error Handling** - Comprehensive error management
- **Configuration Management** - Environment-driven settings

## 🤝 **Contributing**

Contributions are welcome! Please read our [Contributing Guidelines](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md).

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⭐ **Star History**

If this project helps you, please consider giving it a star! ⭐

---

**Made with ❤️ for the IoT community**