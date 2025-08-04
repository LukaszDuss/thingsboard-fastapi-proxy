"""
Test configuration and fixtures for TB-API-SKD.

This module provides shared test fixtures and configuration for both unit
and integration tests.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.core.thingsboard import thingsboard_client
from app.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def async_client(event_loop):
    """Create an async client for testing async endpoints."""
    client = AsyncClient(app=app, base_url="http://test")
    yield client
    event_loop.run_until_complete(client.aclose())


@pytest.fixture
def mock_device_id():
    """Mock device ID for testing."""
    return "550e8400-e29b-41d4-a716-446655440000"


@pytest.fixture
def sample_telemetry_data():
    """Sample telemetry data for testing uploads."""
    return {
        "temperature": [
            {"ts": 1609459200000, "value": 25.6},
            {"ts": 1609459260000, "value": 26.1}
        ],
        "humidity": [
            {"ts": 1609459200000, "value": 60.2}
        ]
    }


@pytest.fixture 
def sample_attributes():
    """Sample attributes data for testing uploads."""
    return {
        "serialNumber": "SN001234",
        "firmwareVersion": "1.2.3",
        "lastMaintenanceDate": "2024-01-15",
        "calibrationOffset": 0.5
    }


@pytest.fixture
def sample_bulk_telemetry():
    """Sample bulk telemetry data for testing."""
    return {
        "device1-uuid": {
            "temperature": [{"ts": 1609459200000, "value": 25.6}],
            "humidity": [{"ts": 1609459200000, "value": 60.2}]
        },
        "device2-uuid": {
            "pressure": [{"ts": 1609459200000, "value": 1013.25}]
        }
    }


@pytest.fixture
def authenticated_tb_client():
    """
    Fixture that ensures ThingsBoard client is authenticated.
    
    This is for integration tests that need real ThingsBoard connection.
    """
    # The client will authenticate automatically on first request
    return thingsboard_client


@pytest.fixture
def tb_client_for_cleanup():
    """
    Separate fixture for cleanup testing that won't affect other tests.
    
    This creates a separate client instance that can be safely closed.
    """
    from app.core.thingsboard import ThingsBoardClient
    
    # Create a new instance (bypassing singleton pattern for testing)
    cleanup_client = object.__new__(ThingsBoardClient)
    cleanup_client.__init__()
    return cleanup_client


@pytest.fixture
def real_device_id(authenticated_tb_client, event_loop):
    """Get a real device ID from ThingsBoard for integration testing."""
    async def _get_device_id():
        response = await authenticated_tb_client.get("/api/tenant/devices?page=0&pageSize=1")
        assert response.status_code == 200
        
        devices = response.json()["data"]
        if not devices:
            pytest.skip("No devices available for testing - please create a test device in ThingsBoard")
        
        return devices[0]["id"]["id"]
    
    return event_loop.run_until_complete(_get_device_id())


# Test configuration
pytestmark = pytest.mark.asyncio 